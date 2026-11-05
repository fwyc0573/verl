"""Adapt verified Miles source turns to verl without retemplating their prompts.

The source preparer remains responsible for byte-range extraction and inherited
training exclusions. Prepared prompts are consumed by the task's agent loop as
token IDs; historical completions remain metadata, never OPD training targets.
"""

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import torch

from verl.utils.dataset.rl_dataset import RLHFDataset


def token_hash(tokens):
    return hashlib.sha256(json.dumps(tokens, separators=(",", ":")).encode()).hexdigest()


def _load_renderer(miles_root):
    path = miles_root / "examples/agentic_opd/glm_turns.py"
    spec = importlib.util.spec_from_file_location("miles_opd_turn_renderer", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _glm_prompt(row, tokenizer, renderer):
    prompt = row["prompt"]
    ids = tokenizer.encode(prompt, add_special_tokens=False)
    source = row["metadata"]["source"]
    if len(ids) != source["prompt_token_count"] or token_hash(ids) != source["prompt_sha256"]:
        raise ValueError("Student tokenization differs from the verified GLM source prompt")
    if not prompt.endswith("<|assistant|>"):
        raise ValueError("GLM source prompt does not end at the role-only assistant boundary")
    return prompt, ids, None


def _qwen_prompt(row, tokenizer, renderer):
    metadata = row["metadata"]
    thinking = metadata["original_completion"]["has_thinking"]
    prompt = tokenizer.apply_chat_template(
        renderer.normalize_tool_arguments(metadata["history"]),
        tools=metadata["tools"],
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=thinking,
    )
    return prompt, tokenizer.encode(prompt, add_special_tokens=False), thinking


PROMPT_FORMATS = {"glm_role_only": _glm_prompt, "qwen_chat_template": _qwen_prompt}


def make_prepared_row(row, *, tokenizer, renderer, pair_name, prompt_format, max_prompt_tokens):
    """Preserve source metadata while recording the exact student input."""
    prompt, ids, thinking = PROMPT_FORMATS[prompt_format](row, tokenizer, renderer)
    if len(ids) > max_prompt_tokens:
        raise ValueError(
            f"Student-rendered source exceeds the prompt budget: {len(ids)} > {max_prompt_tokens}"
        )
    metadata = copy.deepcopy(row["metadata"])
    source = metadata["source"]
    if prompt_format == "qwen_chat_template":
        metadata["source"] = {
            "uid": source["uid"],
            "category": source["category"],
            "glm_source": source,
            "prompt_token_count": len(ids),
            "prompt_sha256": token_hash(ids),
        }
    metadata["thinking_enabled"] = thinking
    return {
        "data_source": pair_name,
        "source_uid": source["uid"],
        "source_category": source["category"],
        "prepared_prompt": prompt,
        "prepared_prompt_ids": ids,
        "metadata_json": json.dumps(metadata, ensure_ascii=False, separators=(",", ":")),
        "thinking_enabled": thinking,
    }


class PreparedTurnDataset(RLHFDataset):
    """Use verified tokenized turns through verl's existing dataset interface."""

    def maybe_filter_out_long_prompts(self, dataframe=None):
        return dataframe

    def __getitem__(self, item):
        row = self.dataframe[item]
        metadata = json.loads(row.pop("metadata_json"))
        ids = row["prepared_prompt_ids"]
        source = metadata["source"]
        if len(ids) > self.max_prompt_length:
            raise ValueError("Prepared source exceeds the configured prompt length; truncation is unsupported")
        if len(ids) != source["prompt_token_count"] or token_hash(ids) != source["prompt_sha256"]:
            raise ValueError("Prepared prompt token IDs differ from their source receipt")
        row.update(
            raw_prompt=metadata["history"],
            metadata=metadata,
            source=source,
            tools=metadata["tools"],
            extra_info={"index": item, "source_uid": source["uid"], "source_category": source["category"]},
            index=item,
            tools_kwargs={},
            interaction_kwargs={},
            reward_model={"style": "rule", "ground_truth": ""},
            dummy_tensor=torch.tensor([0], dtype=torch.uint8),
        )
        return row


def prepare(args):
    import pyarrow as pa
    import pyarrow.parquet as pq
    from transformers import AutoTokenizer

    output = args.output.resolve()
    output.relative_to("/mnt/codesign-exp/ycfeng")
    report_path = args.report.resolve()
    if output.exists() or report_path.exists():
        raise FileExistsError("Preparation requires new output and report paths")
    pairs = json.loads(args.pairs.read_text())
    pair = pairs[args.pair]
    prompt_format = pair["prompt_format"]
    if prompt_format not in PROMPT_FORMATS:
        raise ValueError(f"Unknown prompt_format: {prompt_format}")
    student = Path(pair["student"]).resolve()
    student.relative_to("/mnt/codesign-exp/ycfeng")
    manifest_raw = args.manifest.read_bytes()
    manifest = json.loads(manifest_raw)
    glm_tokenizer = Path(manifest["tokenizer"]["path"]).resolve()
    glm_tokenizer.relative_to("/mnt/codesign-exp/ycfeng")
    miles_root = args.miles_root.resolve()
    preparer = miles_root / "tests/manual/agent_opd/prepare_glm5_2.py"
    renderer = _load_renderer(miles_root)
    tokenizer = AutoTokenizer.from_pretrained(student, local_files_only=True)
    environment = dict(os.environ, PYTHONPATH=str(miles_root), PYTHONDONTWRITEBYTECODE="1")
    args.work_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="verl-opd-turns-", dir=args.work_dir) as temporary:
        directory = Path(temporary)
        source_path, source_report = directory / "source.jsonl", directory / "source-report.json"
        command = [
            sys.executable,
            "-B",
            str(preparer),
            "--manifest",
            str(args.manifest.resolve()),
            "--tokenizer",
            str(glm_tokenizer),
            "--output",
            str(source_path),
            "--report",
            str(source_report),
            "--turns-per-category",
            str(args.turns_per_category),
            "--max-prompt-tokens",
            str(args.max_prompt_tokens),
        ]
        subprocess.run(command, env=environment, cwd=miles_root, check=True)
        source_receipt = json.loads(source_report.read_text())
        # Unicode line separators inside JSON strings are not record boundaries.
        with source_path.open(encoding="utf-8") as stream:
            rows = [
                make_prepared_row(
                    json.loads(line),
                    tokenizer=tokenizer,
                    renderer=renderer,
                    pair_name=args.pair,
                    prompt_format=prompt_format,
                    max_prompt_tokens=args.max_prompt_tokens,
                )
                for line in stream
            ]
    counts = Counter(row["source_category"] for row in rows)
    expected = {category: args.turns_per_category for category in manifest["categories"]}
    if counts != expected or len({row["source_uid"] for row in rows}) != len(rows):
        raise ValueError("Prepared rows do not preserve the requested distinct category population")
    if len({token_hash(row["prepared_prompt_ids"]) for row in rows}) != len(rows):
        raise ValueError("Student-rendered prompts are not distinct")
    schema = pa.schema(
        [
            ("data_source", pa.string()),
            ("source_uid", pa.string()),
            ("source_category", pa.string()),
            ("prepared_prompt", pa.string()),
            ("prepared_prompt_ids", pa.list_(pa.int32())),
            ("metadata_json", pa.string()),
            ("thinking_enabled", pa.bool_()),
        ]
    )
    table = pa.Table.from_pylist(rows, schema=schema)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        pq.write_table(table, stream)
    actual = pq.read_table(output).to_pylist()
    if actual != rows:
        raise ValueError("Parquet round trip changed prepared tokens or source metadata")
    lengths = [len(row["prepared_prompt_ids"]) for row in rows]
    report = {
        "status": "passed",
        "model_pair": args.pair,
        "student": str(student),
        "prompt_format": prompt_format,
        "source_preparer": str(preparer),
        "source_manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
        "rows": len(rows),
        "distinct_source_uids": len({row["source_uid"] for row in rows}),
        "categories": dict(counts),
        "prompt_token_range": [min(lengths), max(lengths)],
        "max_prompt_tokens": args.max_prompt_tokens,
        "training_exclusion": source_receipt["training_exclusion"],
        "isolation": source_receipt["isolation"],
        "historical_completion_use": (
            "Source classification and serialization evidence only; student generates OPD targets"
        ),
        "history_representation": "Original unchanged messages in metadata_json",
        "parquet_round_trip": "Exact rows, token IDs and source metadata match",
        "temporary_source_files": "Removed after conversion",
        "output": str(output),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("x") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print("VERL_AGENT_OPD_TURNS_PREPARED", args.pair, len(rows), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--miles-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--pairs", type=Path, required=True)
    parser.add_argument("--pair", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--turns-per-category", type=int, default=20)
    parser.add_argument("--max-prompt-tokens", type=int, required=True)
    args = parser.parse_args()
    if args.turns_per_category < 1 or args.max_prompt_tokens < 1:
        parser.error("Turn count and prompt length must be positive")
    prepare(args)


if __name__ == "__main__":
    main()
