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


def _load_preparer(miles_root):
    path = miles_root / "tests/manual/agent_opd/prepare_glm5_2.py"
    spec = importlib.util.spec_from_file_location("miles_opd_source_preparer", path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(miles_root))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    renderer = sys.modules[module.encode_glm_turn.__module__]
    if Path(renderer.__file__).resolve() != miles_root / "examples/agentic_opd/glm_turns.py":
        raise ValueError("The source preparer imported a renderer outside the explicit Miles root")
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


def make_prepared_row(row, *, tokenizer, renderer, pair_name, prompt_format):
    """Preserve source metadata while recording the exact student input."""
    prompt, ids, thinking = PROMPT_FORMATS[prompt_format](row, tokenizer, renderer)
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


def select_prepared_rows(
    manifest,
    source_rows,
    *,
    tokenizer,
    renderer,
    source_preparer,
    glm_tokenizer,
    pair_name,
    prompt_format,
    turns_per_category,
    max_prompt_tokens,
):
    """Select verified source turns using the current student's actual budget."""

    def key(category, source):
        return category, source["file"], source["source_item_index"], source["assistant_turn_index"]

    cached = {
        key(row["metadata"]["source"]["category"], row["metadata"]["source"]): row
        for row in source_rows
    }
    selected, statistics = {}, {}
    used_source_prompts, used_student_prompts = set(), set()
    for category, bank in manifest["categories"].items():
        candidates = sorted(
            bank["train"],
            key=lambda row: (row["prompt_token_count"], row["source_item_index"], row["assistant_turn_index"]),
        )
        turns, groups = [], set()
        counts = {
            "manifest_candidates": len(candidates),
            "verified_candidates_checked": 0,
            "over_budget_candidates": 0,
            "duplicate_source_candidates": 0,
            "duplicate_student_prompts": 0,
            "selected": 0,
            "pool_exhausted": True,
        }
        for position, candidate in enumerate(candidates):
            if candidate["group_id"] in groups or candidate["prompt_sha256"] in used_source_prompts:
                counts["duplicate_source_candidates"] += 1
                continue
            source_row = cached.get(key(category, candidate))
            if source_row is None:
                file = manifest["files"][candidate["file"]]
                conversation = source_preparer._read_conversation(file, candidate)
                source_row, _ = source_preparer._make_row(
                    glm_tokenizer, conversation, file, candidate, category
                )
            prepared = make_prepared_row(
                source_row, tokenizer=tokenizer, renderer=renderer,
                pair_name=pair_name, prompt_format=prompt_format,
            )
            counts["verified_candidates_checked"] += 1
            if len(prepared["prepared_prompt_ids"]) > max_prompt_tokens:
                counts["over_budget_candidates"] += 1
                continue
            student_hash = token_hash(prepared["prepared_prompt_ids"])
            if student_hash in used_student_prompts:
                counts["duplicate_student_prompts"] += 1
                continue
            turns.append(prepared)
            groups.add(candidate["group_id"])
            used_source_prompts.add(candidate["prompt_sha256"])
            used_student_prompts.add(student_hash)
            counts["selected"] = len(turns)
            if len(turns) == turns_per_category:
                counts["pool_exhausted"] = position + 1 == len(candidates)
                break
        selected[category] = turns
        statistics[category] = counts
    print("VERL_AGENT_OPD_SOURCE_ELIGIBILITY", pair_name, json.dumps(statistics, sort_keys=True), flush=True)
    if any(len(turns) != turns_per_category for turns in selected.values()):
        raise ValueError(
            "Insufficient verified student-length-eligible source turns: "
            + json.dumps(statistics, sort_keys=True)
        )
    rows = [turns[position] for position in range(turns_per_category) for turns in selected.values()]
    return rows, statistics


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
            source_rows = [json.loads(line) for line in stream]
        source_preparer = _load_preparer(miles_root)
        source_tokenizer = tokenizer if student == glm_tokenizer else AutoTokenizer.from_pretrained(
            glm_tokenizer, local_files_only=True
        )
        rows, selection = select_prepared_rows(
            manifest, source_rows, tokenizer=tokenizer, renderer=renderer,
            source_preparer=source_preparer, glm_tokenizer=source_tokenizer,
            pair_name=args.pair, prompt_format=prompt_format,
            turns_per_category=args.turns_per_category, max_prompt_tokens=args.max_prompt_tokens,
        )
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
        "selection_order": "Miles prompt_token_count, source_item_index, assistant_turn_index within each category",
        "selection_budget": "Actual student-rendered length; no source GLM-length cutoff or truncation",
        "selection": selection,
        "turns": [
            {"source_uid": row["source_uid"], "category": row["source_category"],
             "student_prompt_tokens": len(row["prepared_prompt_ids"]),
             "student_prompt_sha256": token_hash(row["prepared_prompt_ids"])}
            for row in rows
        ],
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
