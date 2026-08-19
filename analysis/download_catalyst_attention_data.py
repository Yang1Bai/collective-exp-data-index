"""Download hash-pinned public catalyst data used by the attention model."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from catalyst_attention.data import (
    OCX24_SHA256,
    OCX24_BYTES,
    OCX24_URL,
    SECCM_EDX_SHA256,
    SECCM_EDX_BYTES,
    SECCM_EDX_URL,
    SECCM_SHA256,
    SECCM_BYTES,
    SECCM_URL,
    SECCM_XPS_SHA256,
    SECCM_XPS_BYTES,
    SECCM_XPS_URL,
    SPECGEN_SHA256,
    SPECGEN_BYTES,
    SPECGEN_URL,
    atomic_write_text,
    download_pinned,
    sha256,
)


SOURCES = {
    "specgen": (
        SPECGEN_URL,
        "44160_2025_983_MOESM4_ESM.zip",
        SPECGEN_SHA256,
        SPECGEN_BYTES,
    ),
    "ocx24": (
        OCX24_URL,
        "ExpDataDump_241113_clean.csv",
        OCX24_SHA256,
        OCX24_BYTES,
    ),
    "seccm": (
        SECCM_URL,
        "SECCM_dataset.zip",
        SECCM_SHA256,
        SECCM_BYTES,
    ),
    "seccm-edx": (
        SECCM_EDX_URL,
        "EDX_dataset.zip",
        SECCM_EDX_SHA256,
        SECCM_EDX_BYTES,
    ),
    "seccm-xps": (
        SECCM_XPS_URL,
        "XPS_dataset.zip",
        SECCM_XPS_SHA256,
        SECCM_XPS_BYTES,
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path.home() / ".collective_data_cache" / "catalyst_attention",
    )
    parser.add_argument(
        "--source",
        action="append",
        choices=[*SOURCES, "all"],
        default=[],
        help="repeat to select sources; default is all",
    )
    args = parser.parse_args()
    selected = args.source or ["all"]
    names = list(SOURCES) if "all" in selected else selected
    records = []
    for name in names:
        url, filename, expected, expected_size = SOURCES[name]
        path = download_pinned(
            url,
            args.cache_dir / filename,
            expected,
            expected_size,
        )
        records.append(
            {
                "source": name,
                "path": str(path),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
                "url": url,
            }
        )
        print(f"{name}: {path} ({path.stat().st_size:,} bytes)")
    manifest = args.cache_dir / "download_manifest.json"
    atomic_write_text(
        manifest,
        json.dumps({"sources": records}, indent=2, sort_keys=True) + "\n",
    )
    print(f"manifest: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
