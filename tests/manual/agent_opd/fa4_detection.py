# Copyright 2026 Individual Contributor.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Backport the upstream FA4 metadata check to the locked native environment.

Run with the worker's native interpreter after uv sync and before native imports:
    "$UV_PROJECT_ENVIRONMENT/bin/python" -B tests/manual/agent_opd/fa4_detection.py

Only the inspected Megatron Core 0.19.2 file, or this exact patched file, is
accepted. The JSON receipt describes a source change, not runtime qualification.
"""

import ast
import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path

CORE_VERSION = "0.19.2"
CORE_COMMIT = "4b4acac9a1d28ea6829c8d4f566d75698a21249d"
ORIGINAL_SHA256 = "a019cd00a708a22237383456a7ba85bf522201c14a5b7cb0c1e4f0f12eac9837"
PATCHED_SHA256 = "a733e2a6b5eb24e99fe4ca55a68f88bddf56ab0e5fd7ffd56a4b231c7262f5c8"
UPSTREAM_SOURCE = (
    "https://github.com/NVIDIA/Megatron-LM/blob/"
    "90f4d5279b951a408d7bf605a24776c248357c03/megatron/core/transformer/attention.py"
)
UPSTREAM_GUARD_SHA256 = "9937bb5ee3d521f8e1c627f082aaa7a181cd4290a963d6860b156bb6071c5258"

ORIGINAL_BLOCK = b'''_MIN_FA4_VERSION = "4.0.0b20"
try:
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as _get_dist_version

    from flash_attn.cute import flash_attn_varlen_func as flash_attn4_varlen_func
    from packaging.version import Version as _Version

    try:
        HAVE_FA4 = _Version(_get_dist_version("flash-attn-4")) >= _Version(_MIN_FA4_VERSION)
    except PackageNotFoundError:
        HAVE_FA4 = False
except ImportError:
    HAVE_FA4 = False'''

REPLACEMENT_BLOCK = b'''_MIN_FA4_VERSION = "4.0.0b20"
flash_attn4_varlen_func = None
try:
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as _get_dist_version

    from packaging.version import Version as _Version

    HAVE_FA4 = _Version(_get_dist_version("flash-attn-4")) >= _Version(_MIN_FA4_VERSION)
    if HAVE_FA4:
        from flash_attn.cute import flash_attn_varlen_func as flash_attn4_varlen_func
except (ImportError, PackageNotFoundError):
    HAVE_FA4 = False'''


def sha256(content):
    return hashlib.sha256(content).hexdigest()


def patched_source(content):
    """Accept only the inspected original or the exact upstream-guard backport."""
    digest = sha256(content)
    if digest == PATCHED_SHA256:
        return content, "already_applied"
    if digest != ORIGINAL_SHA256 or content.count(ORIGINAL_BLOCK) != 1:
        raise ValueError(f"Refusing unknown Megatron Core attention.py source: sha256={digest}")
    if sha256(REPLACEMENT_BLOCK) != UPSTREAM_GUARD_SHA256:
        raise ValueError("The replacement block differs from the inspected upstream guard")
    updated = content.replace(ORIGINAL_BLOCK, REPLACEMENT_BLOCK, 1)
    if sha256(updated) != PATCHED_SHA256:
        raise ValueError("The resulting Megatron Core source does not match the expected SHA256")
    ast.parse(updated)
    return updated, "applied"


def main():
    distribution = importlib.metadata.distribution("megatron-core")
    if distribution.version != CORE_VERSION:
        raise ValueError(f"Expected megatron-core=={CORE_VERSION}, found {distribution.version}")
    path = Path(distribution.locate_file("megatron/core/transformer/attention.py")).resolve()
    if not path.is_relative_to(Path(sys.prefix).resolve()):
        raise ValueError(f"Refusing to patch a source file outside the active environment: {path}")
    original = path.read_bytes()
    updated, action = patched_source(original)
    if action == "applied":
        path.write_bytes(updated)
    observed_sha256 = sha256(path.read_bytes())
    if observed_sha256 != PATCHED_SHA256:
        raise ValueError("Installed Megatron Core source differs after applying the patch")
    try:
        fa4_version = importlib.metadata.version("flash-attn-4")
    except importlib.metadata.PackageNotFoundError:
        fa4_version = None
    print(json.dumps({
        "action": action,
        "source_path": str(path),
        "python": sys.executable,
        "megatron_core_version": distribution.version,
        "locked_megatron_core_commit": CORE_COMMIT,
        "before_sha256": sha256(original),
        "after_sha256": observed_sha256,
        "upstream_source": UPSTREAM_SOURCE,
        "upstream_guard_sha256": UPSTREAM_GUARD_SHA256,
        "flash_attn_4_version": fa4_version,
        "native_import_verified": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
