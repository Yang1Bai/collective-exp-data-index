"""Download and verify the open BambooMixer response-transfer datasets."""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path


HERE = Path(__file__).resolve().parent
DEFAULT_DIR = HERE / "external_data" / "bamboomixer_response_transfer"
FILES = {
    "source": {
        "filename": "bamboomixer_original_data.json",
        "url": (
            "https://huggingface.co/ByteDance-Seed/bamboo_mixer/resolve/main/"
            "dataset/data.json?download=true"
        ),
        "sha256": "592ba3643251f1e07bfdd31fd84c4188c6af20c3b9eeadb3f93e703efd7b6061",
        "bytes": 193868504,
    },
    "target": {
        "filename": "LiAsF6_conductivity.json",
        "url": (
            "https://huggingface.co/datasets/PKUAIBDA/"
            "Dataset_Bamboomixer_extension/resolve/main/"
            "LiAsF6_conductivity.json?download=true"
        ),
        "sha256": "39c31b90bd7fdcf24530bec7eaa379c19e270ddc54fdc910bf72d5ed021ac543",
        "bytes": 1713298,
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def download(url: str, destination: Path) -> None:
    partial = destination.with_suffix(destination.suffix + ".part")
    partial.parent.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(url, partial)
        partial.replace(destination)
    finally:
        if partial.exists():
            partial.unlink()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_DIR)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, spec in FILES.items():
        path = args.output_dir / spec["filename"]
        if not path.exists() or sha256(path) != spec["sha256"]:
            download(spec["url"], path)
        observed_hash = sha256(path)
        observed_size = path.stat().st_size
        if observed_hash != spec["sha256"] or observed_size != spec["bytes"]:
            raise RuntimeError(f"Downloaded {name} file failed verification")
        manifest[name] = {
            **spec,
            "path": str(path.resolve()),
            "observed_sha256": observed_hash,
            "observed_bytes": observed_size,
        }
    manifest["status"] = "verified"
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

