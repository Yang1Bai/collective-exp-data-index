"""Download the HybriD3 band-gap records through its public web API.

HybriD3 exposes searchable material pages and JSON endpoints for each numeric
subset.  This downloader caches every material page and every subset response,
so interrupted runs are resumable and the final table can be independently
reconstructed from the cached snapshot.
"""
from __future__ import annotations

import gzip
import hashlib
import html
import http.cookiejar
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA_ROOT = (
    ROOT / "data" / "external" / "bandgap_borrowing" / "hybrid3_bandgap"
)
MATERIAL_DIR = DATA_ROOT / "materials"
SUBSET_DIR = DATA_ROOT / "subsets"
SEARCH_HTML = DATA_ROOT / "bandgap_search.html.gz"
CSV_PATH = DATA_ROOT / "hybrid3_bandgap_records.csv"
MANIFEST_PATH = DATA_ROOT / "hybrid3_bandgap_manifest.json"

BASE_URL = "https://materials.hybrid3.duke.edu"
USER_AGENT = "collective-exp-data-index/hybrid3-audit-1.0"
REQUEST_INTERVAL_SECONDS = 0.20


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def strip_tags(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    return " ".join(html.unescape(text).split())


def opener() -> urllib.request.OpenerDirector:
    cookies = http.cookiejar.CookieJar()
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookies)
    )


def open_bytes(
    session: urllib.request.OpenerDirector,
    url: str,
    *,
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    attempts: int = 5,
) -> bytes:
    request_headers = {"User-Agent": USER_AGENT}
    request_headers.update(headers or {})
    request = urllib.request.Request(
        url,
        data=data,
        headers=request_headers,
    )
    for attempt in range(attempts):
        try:
            with session.open(request, timeout=120) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            retryable = error.code in {429, 500, 502, 503, 504}
            if not retryable or attempt + 1 == attempts:
                detail = error.read().decode("utf-8", errors="replace")
                raise RuntimeError(
                    f"HybriD3 HTTP {error.code}: {detail[:1000]}"
                ) from error
        except (TimeoutError, urllib.error.URLError) as error:
            if attempt + 1 == attempts:
                raise RuntimeError(f"HybriD3 request failed: {url}") from error
        time.sleep(max(1.0, 2**attempt))
    raise AssertionError("unreachable")


def write_gzip(path: Path, payload: bytes) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with gzip.open(temporary, "wb", compresslevel=6) as handle:
        handle.write(payload)
    temporary.replace(path)


def read_gzip(path: Path) -> bytes:
    with gzip.open(path, "rb") as handle:
        return handle.read()


def get_search(
    session: urllib.request.OpenerDirector,
) -> bytes:
    if SEARCH_HTML.exists():
        return read_gzip(SEARCH_HTML)
    search_url = f"{BASE_URL}/materials/search"
    landing = open_bytes(session, search_url).decode("utf-8")
    match = re.search(
        r'name="csrfmiddlewaretoken" value="([^"]+)"',
        landing,
    )
    if match is None:
        raise RuntimeError("HybriD3 search page omitted CSRF token")
    token = match.group(1)
    body = urllib.parse.urlencode(
        {
            "csrfmiddlewaretoken": token,
            "search_term": "band_gap",
            "band_gap_min": "0",
            "band_gap_max": "10",
            "is_experimental": "any",
        }
    ).encode("utf-8")
    result = open_bytes(
        session,
        search_url,
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": search_url,
            "X-CSRFToken": token,
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    write_gzip(SEARCH_HTML, result)
    return result


def parse_materials(search_html: bytes) -> list[dict[str, str]]:
    text = search_html.decode("utf-8")
    output: dict[int, dict[str, str]] = {}
    for row in re.findall(r"<tr>(.*?)</tr>", text, flags=re.S):
        link = re.search(
            r'href="/materials/(\d+)">([^<]+)</a>',
            row,
        )
        if link is None:
            continue
        cells = re.findall(
            r"<td(?:\s[^>]*)?>(.*?)</td>",
            row,
            flags=re.S,
        )
        if len(cells) < 5:
            continue
        material_id = int(link.group(1))
        output[material_id] = {
            "material_id": str(material_id),
            "material_name": strip_tags(cells[0]),
            "iupac_name": strip_tags(cells[1]),
            "alternate_names": strip_tags(cells[2]),
            "organic_component": strip_tags(cells[3]),
            "inorganic_component": strip_tags(cells[4]),
        }
    if len(output) < 100:
        raise RuntimeError(
            f"HybriD3 search returned only {len(output)} materials"
        )
    return [output[key] for key in sorted(output)]


def get_material_page(
    session: urllib.request.OpenerDirector,
    material_id: int,
) -> bytes:
    path = MATERIAL_DIR / f"material_{material_id:05d}.html.gz"
    if path.exists():
        return read_gzip(path)
    payload = open_bytes(session, f"{BASE_URL}/materials/{material_id}")
    write_gzip(path, payload)
    time.sleep(REQUEST_INTERVAL_SECONDS)
    return payload


def card_records(
    material: dict[str, str],
    page: bytes,
) -> list[dict[str, Any]]:
    text = page.decode("utf-8")
    chunks = re.split(r'<div class="card card-item">', text)[1:]
    output: list[dict[str, Any]] = []
    for chunk in chunks:
        header = re.search(
            r'<div class="card-header">\s*<h5>(.*?)</h5>',
            chunk,
            flags=re.S,
        )
        if header is None:
            continue
        property_name = re.sub(
            r"\s+Verified$",
            "",
            strip_tags(header.group(1)),
        )
        if "band gap" not in property_name.lower():
            continue
        subset = re.search(
            r'<tbody class="tabulated-data" id="table-(\d+)">',
            chunk,
        )
        dataset = re.search(r"Data set ID:\s*(\d+)", chunk)
        if subset is None or dataset is None:
            continue
        origin_match = re.search(
            r"<h5>Origin:\s*([A-Za-z]+)",
            chunk,
        )
        temperature_match = re.search(
            r"\(T\s*=\s*([-+0-9.]+)\s*K\)",
            chunk,
        )
        doi_match = re.search(
            r"10\.\d{4,9}/[^\s<\"']+",
            html.unescape(chunk),
            flags=re.I,
        )
        doi = doi_match.group(0).rstrip(".,;") if doi_match else ""
        output.append(
            {
                **material,
                "property_name": property_name,
                "verified": "badge badge-success" in header.group(1),
                "origin": (
                    origin_match.group(1).lower()
                    if origin_match
                    else ""
                ),
                "temperature_k": (
                    float(temperature_match.group(1))
                    if temperature_match
                    else None
                ),
                "doi": doi,
                "dataset_id": int(dataset.group(1)),
                "subset_id": int(subset.group(1)),
            }
        )
    return output


def get_subset(
    session: urllib.request.OpenerDirector,
    subset_id: int,
) -> list[dict[str, Any]]:
    path = SUBSET_DIR / f"subset_{subset_id:06d}.json.gz"
    if path.exists():
        payload = read_gzip(path)
    else:
        payload = open_bytes(
            session,
            f"{BASE_URL}/materials/get-subset-values/{subset_id}",
        )
        parsed = json.loads(payload)
        if not isinstance(parsed, list):
            raise RuntimeError(f"Unexpected subset payload: {subset_id}")
        write_gzip(path, payload)
        time.sleep(REQUEST_INTERVAL_SECONDS)
    parsed = json.loads(payload)
    if not isinstance(parsed, list):
        raise RuntimeError(f"Unexpected subset payload: {subset_id}")
    return parsed


def main() -> None:
    MATERIAL_DIR.mkdir(parents=True, exist_ok=True)
    SUBSET_DIR.mkdir(parents=True, exist_ok=True)
    session = opener()
    search = get_search(session)
    materials = parse_materials(search)
    print(f"HybriD3 band-gap materials: {len(materials)}", flush=True)

    cards: list[dict[str, Any]] = []
    for index, material in enumerate(materials, start=1):
        page = get_material_page(session, int(material["material_id"]))
        cards.extend(card_records(material, page))
        if index % 25 == 0 or index == len(materials):
            print(
                f"materials {index}/{len(materials)}; "
                f"band-gap cards {len(cards)}",
                flush=True,
            )
    if len(cards) < 100:
        raise RuntimeError(f"Only {len(cards)} band-gap cards were parsed")

    rows: list[dict[str, Any]] = []
    unique_subsets = sorted({int(card["subset_id"]) for card in cards})
    subset_values: dict[int, list[dict[str, Any]]] = {}
    for index, subset_id in enumerate(unique_subsets, start=1):
        subset_values[subset_id] = get_subset(session, subset_id)
        if index % 50 == 0 or index == len(unique_subsets):
            print(
                f"subsets {index}/{len(unique_subsets)}",
                flush=True,
            )
    for card in cards:
        values = subset_values[int(card["subset_id"])]
        for value_index, value in enumerate(values):
            if not isinstance(value, dict) or "y" not in value:
                continue
            rows.append(
                {
                    **card,
                    "value_index": value_index,
                    "x": value.get("x"),
                    "band_gap_ev": value.get("y"),
                }
            )
    frame_columns = [
        "material_id",
        "material_name",
        "iupac_name",
        "alternate_names",
        "organic_component",
        "inorganic_component",
        "property_name",
        "verified",
        "origin",
        "temperature_k",
        "doi",
        "dataset_id",
        "subset_id",
        "value_index",
        "x",
        "band_gap_ev",
    ]
    import csv

    temporary = CSV_PATH.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=frame_columns)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(CSV_PATH)
    manifest = {
        "status": "complete",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source": BASE_URL,
        "search": {
            "property": "band_gap",
            "range_ev": [0, 10],
            "origin": "any",
        },
        "materials": len(materials),
        "cards": len(cards),
        "subsets": len(unique_subsets),
        "numeric_rows": len(rows),
        "search_html_sha256": sha256(SEARCH_HTML),
        "csv_sha256": sha256(CSV_PATH),
        "cached_material_pages": len(
            list(MATERIAL_DIR.glob("material_*.html.gz"))
        ),
        "cached_subset_payloads": len(
            list(SUBSET_DIR.glob("subset_*.json.gz"))
        ),
        "claim_guard": (
            "HybriD3 is an external adjacent-domain donor. Recipient DOI "
            "overlap and exact composition overlap must be measured and "
            "controlled before any photovoltaic outcome model is fit."
        ),
    }
    temporary_manifest = MANIFEST_PATH.with_suffix(".json.tmp")
    temporary_manifest.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary_manifest.replace(MANIFEST_PATH)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
