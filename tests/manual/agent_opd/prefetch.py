"""Populate a mounted uv cache with this task's five locked native wheels.

Run on the CPU host with its working GitHub proxy route. Package installation
uses a disposable target and no dependencies; no CUDA modules are imported.
The original lock URLs remain the cache keys used by the worker's frozen sync.
"""

import argparse
import hashlib
import importlib.metadata
import json
import os
import subprocess
import tempfile
import tomllib
from pathlib import Path


PACKAGES = {"apex", "deep-ep", "flash-attn", "megatron-bridge", "transformer-engine"}


def native_wheels(lock):
    selected = []
    for package in lock["package"]:
        if package["name"] not in PACKAGES:
            continue
        wheels = [
            wheel
            for wheel in package.get("wheels", [])
            if wheel["url"].startswith("https://github.com/verl-project/verl-wheelhouse/releases/download/")
            and ("-cp312-cp312-linux_x86_64.whl" in wheel["url"] or "-py3-none-any.whl" in wheel["url"])
        ]
        if len(wheels) != 1:
            raise ValueError(f"Expected one native wheel for {package['name']}, found {len(wheels)}")
        selected.append({
            "name": package["name"], "version": package["version"],
            "registry": package["source"]["registry"], **wheels[0],
        })
    if {item["name"] for item in selected} != PACKAGES:
        raise ValueError("The lock does not contain all five required native wheels")
    return selected


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def archive_receipt(path):
    rows = []
    for item in sorted(path.rglob("*")):
        if item.is_file():
            rows.append({"path": str(item.relative_to(path)), "size": item.stat().st_size, "sha256": file_hash(item)})
    encoded = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    return {
        "path": str(path),
        "distributions": [
            {"name": dist.metadata["Name"], "version": dist.version}
            for dist in importlib.metadata.distributions(path=[str(path)])
        ],
        "files": len(rows),
        "bytes": sum(row["size"] for row in rows),
        "file_manifest_sha256": hashlib.sha256(encoded).hexdigest(),
        "file_manifest": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    cache, work = args.cache.resolve(), args.work_dir.resolve()
    cache.relative_to("/data/ycfeng/tmp")
    work.relative_to("/data/ycfeng/tmp")
    if args.report.exists():
        raise FileExistsError("Use a new prefetch report path")
    lock_bytes = args.lock.read_bytes()
    wheels = native_wheels(tomllib.loads(lock_bytes.decode()))
    registries = {wheel["registry"] for wheel in wheels}
    if len(registries) != 1:
        raise ValueError("The five native wheels must share the locked wheelhouse registry")
    cache.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ, UV_CACHE_DIR=str(cache), PYTHONDONTWRITEBYTECODE="1")
    uv_version = subprocess.check_output(["uv", "--version"], text=True).strip()
    report = {
        "lock": str(args.lock.resolve()),
        "lock_sha256": hashlib.sha256(lock_bytes).hexdigest(),
        "uv_version": uv_version,
        "python": str(args.python.resolve()),
        "cache": str(cache),
        "wheels": wheels,
        "lock_wheel_hashes_available": all("hash" in row for row in wheels),
        "imports_performed": False,
    }
    with tempfile.TemporaryDirectory(prefix="native-wheel-target-", dir=work) as temporary:
        target = Path(temporary)
        command = [
            "uv", "pip", "install", "--no-deps", "--target", str(target),
            "--python", str(args.python), "--link-mode", "copy",
            "--index-url", next(iter(registries)),
            *[wheel["name"] + "==" + wheel["version"] for wheel in wheels],
        ]
        report["command"] = command
        print(json.dumps({"stage": "native_wheel_prefetch", "packages": wheels, "cache": str(cache)}), flush=True)
        result = subprocess.run(command, env=environment, check=False)
        report["install_exit_code"] = result.returncode
        if result.returncode:
            report["status"] = "FAIL"
        else:
            distributions = list(importlib.metadata.distributions(path=[str(target)]))
            found = {dist.metadata["Name"].lower().replace("_", "-"): dist.version for dist in distributions}
            expected = {wheel["name"]: wheel["version"] for wheel in wheels}
            if found != expected:
                raise ValueError(f"Installed metadata differs from lock: {found}")
            report["distributions"] = [
                {
                    "name": dist.metadata["Name"], "version": dist.version,
                    "metadata_sha256": hashlib.sha256(dist.read_text("METADATA").encode()).hexdigest(),
                    "wheel_metadata": dist.read_text("WHEEL"),
                }
                for dist in distributions
            ]
            report["archives"] = [archive_receipt(path) for path in sorted((cache / "archive-v0").iterdir())]
            links = [path for path in cache.rglob("*") if path.is_symlink()]
            report["cache_links"] = [
                {"path": str(path.relative_to(cache)), "target": os.readlink(path),
                 "relative": not Path(os.readlink(path)).is_absolute(), "valid": path.exists()}
                for path in sorted(links)
            ]
            report["status"] = "PASS"
            report["limits"] = [
                "Cache file manifests hash extracted wheel content, not original wheel ZIP bytes.",
                "GitHub lock entries provide no wheel hash; URL and version matching is not lock hash validation.",
                "Worker uv compatibility and merged-cache consumption require a separate offline verification.",
            ]
    report["temporary_install_target_removed"] = not target.exists()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("x") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "report": str(args.report),
                      "temporary_install_target_removed": report["temporary_install_target_removed"]}), flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
