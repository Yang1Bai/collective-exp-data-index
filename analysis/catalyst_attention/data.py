"""Pinned catalyst datasets and a shared multimodal sample contract.

Raw third-party data remain outside the repository.  Loaders accept exact local
archives and preserve enough provenance for group-held-out transfer tests.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import io
import json
import math
import os
import re
import secrets
import stat
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from .schema import (
    CONDITION_NAMES,
    MEASUREMENT_MODALITY_NAMES,
    PROGRAM_NAMES,
    REACTION_NAMES,
    TARGET_NAMES,
)

SPECGEN_SHA256 = "ca565bf1bb581080985ec86c331291aabb2c9b354500839aba7f9b8b57ba0cb2"
SPECGEN_BYTES = 7_759_603
SPECGEN_URL = (
    "https://static-content.springer.com/esm/"
    "art%3A10.1038%2Fs44160-025-00983-5/"
    "MediaObjects/44160_2025_983_MOESM4_ESM.zip"
)
OCX24_SHA256 = "e55446ee81b26c0ceaa6e9d532186954124ff11a51f854ca13511c7c8b31de99"
OCX24_BYTES = 526_042
OCX24_URL = (
    "https://raw.githubusercontent.com/FAIR-Chem/fairchem/"
    "a838178c0b6cef68ed6b23167cc93c98ee26d2f7/"
    "src/fairchem/applications/ocx/data/experimental_data/"
    "ExpDataDump_241113_clean.csv"
)
SECCM_SHA256 = "6e30cdb3a5ecd257daa091bfc2b6cfaa7889d27938e27ae614977d8845f0ffc0"
SECCM_BYTES = 6_608_379
SECCM_URL = "https://zenodo.org/api/records/20439519/files/SECCM_dataset.zip/content"
SECCM_EDX_SHA256 = "95340043ccecec0e9c92c75900c1992d3f92e98fc72cc80c895b53289f5b8791"
SECCM_EDX_BYTES = 11_963
SECCM_EDX_URL = "https://zenodo.org/api/records/20439519/files/EDX_dataset.zip/content"
SECCM_XPS_SHA256 = "67d1aef3c2d8d640828d241540c21f0d32a8c7923257f323d32403fe8d3d998a"
SECCM_XPS_BYTES = 20_949
SECCM_XPS_URL = "https://zenodo.org/api/records/20439519/files/XPS_dataset.zip/content"

_ELEMENT_SYMBOLS = (
    "H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn "
    "Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag "
    "Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm "
    "Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa "
    "U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh "
    "Fl Mc Lv Ts Og"
).split()
ATOMIC_NUMBER = {symbol: index + 1 for index, symbol in enumerate(_ELEMENT_SYMBOLS)}


@dataclass(frozen=True)
class CatalystSample:
    """One aligned experimental catalyst record.

    Curves use two value channels: primary signal and reported uncertainty.
    ``curve_channel_mask`` distinguishes a genuine zero uncertainty from an
    unavailable uncertainty channel.
    """

    sample_id: str
    program: str
    elements: np.ndarray
    fractions: np.ndarray
    curve_axis: np.ndarray
    curve_values: np.ndarray
    curve_channel_mask: np.ndarray
    condition_values: np.ndarray
    condition_mask: np.ndarray
    reaction_id: int
    modality_id: int
    program_id: int
    target: float | None
    target_name: str
    group_id: str
    surface_elements: np.ndarray = field(
        default_factory=lambda: np.zeros(0, dtype=np.int64)
    )
    surface_fractions: np.ndarray = field(
        default_factory=lambda: np.zeros(0, dtype=np.float32)
    )
    provenance: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.sample_id or not self.group_id:
            raise ValueError("sample_id and group_id are required")
        if self.elements.ndim != 1 or self.fractions.ndim != 1:
            raise ValueError("elements and fractions must be one-dimensional")
        if len(self.elements) == 0 or len(self.elements) != len(self.fractions):
            raise ValueError("composition tokens must be non-empty and aligned")
        if np.any(self.elements <= 0) or np.any(self.elements > 118):
            raise ValueError("element token outside the periodic table")
        if len(np.unique(self.elements)) != len(self.elements):
            raise ValueError("composition element tokens must be unique")
        if np.any(self.fractions < 0) or not np.isclose(self.fractions.sum(), 1.0, atol=1e-5):
            raise ValueError("composition fractions must be non-negative and sum to one")
        if (
            self.surface_elements.ndim != 1
            or self.surface_fractions.ndim != 1
            or len(self.surface_elements) != len(self.surface_fractions)
        ):
            raise ValueError("surface composition tokens are not aligned")
        if len(self.surface_elements):
            if np.any(self.surface_elements <= 0) or np.any(
                self.surface_elements > 118
            ):
                raise ValueError("surface element token outside the periodic table")
            if len(np.unique(self.surface_elements)) != len(
                self.surface_elements
            ):
                raise ValueError("surface element tokens must be unique")
            if np.any(self.surface_fractions < 0) or not np.isclose(
                self.surface_fractions.sum(), 1.0, atol=1e-5
            ):
                raise ValueError(
                    "surface fractions must be non-negative and sum to one"
                )
        if self.curve_axis.ndim != 1 or self.curve_values.ndim != 2:
            raise ValueError("curve axis/values have invalid dimensions")
        if len(self.curve_axis) != len(self.curve_values):
            raise ValueError("curve axis and values are not aligned")
        if self.curve_values.shape[1] != 2 or self.curve_channel_mask.shape != (2,):
            raise ValueError("curves must use the two-channel measurement contract")
        if self.condition_values.shape != (len(CONDITION_NAMES),):
            raise ValueError("condition vector has the wrong width")
        if self.condition_mask.shape != self.condition_values.shape:
            raise ValueError("condition masks are not aligned")
        arrays = (
            self.fractions,
            self.curve_axis,
            self.curve_values,
            self.condition_values,
            self.condition_mask,
            self.surface_fractions,
        )
        if any(not np.all(np.isfinite(array)) for array in arrays):
            raise ValueError("sample contains non-finite numeric values")
        if self.target is not None and not math.isfinite(float(self.target)):
            raise ValueError("target must be finite")
        if self.target_name not in TARGET_NAMES:
            raise ValueError(f"unsupported target name: {self.target_name}")
        categorical_ids = (
            ("reaction_id", self.reaction_id, len(REACTION_NAMES)),
            (
                "modality_id",
                self.modality_id,
                len(MEASUREMENT_MODALITY_NAMES),
            ),
            ("program_id", self.program_id, len(PROGRAM_NAMES)),
        )
        for name, identifier, cardinality in categorical_ids:
            if identifier < 0 or identifier >= cardinality:
                raise ValueError(f"{name} is outside the categorical schema")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sha256(path: Path, expected: str) -> None:
    observed = sha256(path)
    if observed != expected:
        raise ValueError(f"SHA-256 mismatch for {path}: {observed} != {expected}")


def read_pinned_bytes(
    path: Path,
    *,
    expected_sha256: str | None,
    expected_size: int | None,
) -> bytes:
    """Hash and consume one no-follow file descriptor without reopening."""

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path.expanduser().absolute(), flags)
    with os.fdopen(descriptor, "rb") as handle:
        observed_size = os.fstat(handle.fileno()).st_size
        if expected_size is not None and observed_size != expected_size:
            raise ValueError(
                f"byte-size mismatch for {path}: "
                f"{observed_size} != {expected_size}"
            )
        payload = handle.read()
    if expected_sha256 is not None:
        observed_hash = hashlib.sha256(payload).hexdigest()
        if observed_hash != expected_sha256:
            raise ValueError(
                f"SHA-256 mismatch for {path}: "
                f"{observed_hash} != {expected_sha256}"
            )
    return payload


def _handle_sha256(handle: Any) -> str:
    digest = hashlib.sha256()
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(chunk)
    return digest.hexdigest()


def _validate_requested_path_components(path: Path) -> None:
    """Reject mutable or foreign symlink components before resolution."""

    current = Path(path.anchor)
    for part in path.parts[1:]:
        parent = current
        current = current / part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            continue
        parent_metadata = parent.stat()
        parent_shared = parent_metadata.st_mode & (
            stat.S_IWGRP | stat.S_IWOTH
        )
        if parent_shared and not parent_metadata.st_mode & stat.S_ISVTX:
            raise PermissionError(
                f"untrusted writable directory in output path: {parent}"
            )
        if stat.S_ISLNK(metadata.st_mode):
            if metadata.st_uid not in {0, os.geteuid()}:
                raise PermissionError(
                    f"foreign symlink in output path: {current}"
                )
            if parent_shared:
                raise PermissionError(
                    f"mutable symlink parent in output path: {parent}"
                )


@contextmanager
def _trusted_directory(path: Path) -> Iterable[tuple[int, Path]]:
    """Open a private write directory and pin subsequent operations to it."""

    requested = path.expanduser().absolute()
    _validate_requested_path_components(requested)
    requested.mkdir(parents=True, exist_ok=True)
    _validate_requested_path_components(requested)
    resolved = requested.resolve(strict=True)
    for ancestor in (resolved, *resolved.parents):
        metadata = ancestor.stat()
        shared_writable = metadata.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
        if shared_writable and not metadata.st_mode & stat.S_ISVTX:
            raise PermissionError(
                f"untrusted writable directory in output path: {ancestor}"
            )
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(resolved, flags)
    try:
        metadata = os.fstat(descriptor)
        path_metadata = resolved.stat()
        if (
            metadata.st_uid != os.geteuid()
            or metadata.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
            or (metadata.st_dev, metadata.st_ino)
            != (path_metadata.st_dev, path_metadata.st_ino)
        ):
            raise PermissionError(
                f"output directory must be private and user-owned: {resolved}"
            )
        yield descriptor, resolved
    finally:
        os.close(descriptor)


def _temporary_file_descriptor(directory_descriptor: int, prefix: str) -> tuple[int, str]:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_NOFOLLOW", 0)
    for _ in range(20):
        name = f".{prefix}.{secrets.token_hex(16)}.partial"
        try:
            return (
                os.open(
                    name,
                    flags,
                    0o600,
                    dir_fd=directory_descriptor,
                ),
                name,
            )
        except FileExistsError:
            continue
    raise FileExistsError("could not create an exclusive temporary file")


def _reject_symlink_entry(
    directory_descriptor: int, name: str
) -> None:
    try:
        metadata = os.stat(
            name,
            dir_fd=directory_descriptor,
            follow_symlinks=False,
        )
    except FileNotFoundError:
        return
    if stat.S_ISLNK(metadata.st_mode):
        raise ValueError(f"output destination must not be a symlink: {name}")


def download_pinned(
    url: str,
    destination: Path,
    expected_sha256: str,
    expected_size: int,
) -> Path:
    """Download atomically and reject any version drift."""

    destination = destination.expanduser()
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "CollectiveExpDataIndex-catalyst-attention/1.0"},
    )
    with _trusted_directory(destination.parent) as (
        directory_descriptor,
        resolved_parent,
    ):
        _reject_symlink_entry(directory_descriptor, destination.name)
        read_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            existing_descriptor = os.open(
                destination.name,
                read_flags,
                dir_fd=directory_descriptor,
            )
        except FileNotFoundError:
            pass
        else:
            observed_size = os.fstat(existing_descriptor).st_size
            with os.fdopen(existing_descriptor, "rb") as handle:
                observed = _handle_sha256(handle)
            if observed_size != expected_size or observed != expected_sha256:
                raise ValueError(
                    f"pinned file mismatch for {destination}: "
                    f"bytes={observed_size}, sha256={observed}"
                )
            return resolved_parent / destination.name
        descriptor, temporary_name = _temporary_file_descriptor(
            directory_descriptor, destination.name
        )
        try:
            with os.fdopen(descriptor, "wb") as handle:
                with urllib.request.urlopen(request, timeout=120) as response:
                    content_length = response.headers.get("Content-Length")
                    if (
                        content_length is not None
                        and int(content_length) != expected_size
                    ):
                        raise ValueError(
                            "download Content-Length does not match "
                            f"the pinned size for {destination.name}"
                        )
                    downloaded = 0
                    while chunk := response.read(1024 * 1024):
                        downloaded += len(chunk)
                        if downloaded > expected_size:
                            raise ValueError(
                                f"download exceeded pinned size for "
                                f"{destination.name}"
                            )
                        handle.write(chunk)
                    if downloaded != expected_size:
                        raise ValueError(
                            f"download size mismatch for {destination.name}: "
                            f"{downloaded} != {expected_size}"
                        )
                handle.flush()
                os.fsync(handle.fileno())
            verification_descriptor = os.open(
                temporary_name,
                read_flags,
                dir_fd=directory_descriptor,
            )
            with os.fdopen(verification_descriptor, "rb") as handle:
                observed = _handle_sha256(handle)
            if observed != expected_sha256:
                raise ValueError(
                    f"SHA-256 mismatch for downloaded {destination.name}: "
                    f"{observed} != {expected_sha256}"
                )
            os.replace(
                temporary_name,
                destination.name,
                src_dir_fd=directory_descriptor,
                dst_dir_fd=directory_descriptor,
            )
        finally:
            try:
                os.unlink(temporary_name, dir_fd=directory_descriptor)
            except FileNotFoundError:
                pass
    return resolved_parent / destination.name


def atomic_write_text(destination: Path, text: str) -> None:
    """Write UTF-8 text relative to an opened private directory."""

    destination = destination.expanduser()
    with _trusted_directory(destination.parent) as (
        directory_descriptor,
        _,
    ):
        _reject_symlink_entry(directory_descriptor, destination.name)
        descriptor, temporary_name = _temporary_file_descriptor(
            directory_descriptor, destination.name
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(
                temporary_name,
                destination.name,
                src_dir_fd=directory_descriptor,
                dst_dir_fd=directory_descriptor,
            )
        finally:
            try:
                os.unlink(temporary_name, dir_fd=directory_descriptor)
            except FileNotFoundError:
                pass


def _condition_vector(**values: float | None) -> tuple[np.ndarray, np.ndarray]:
    row = np.zeros(len(CONDITION_NAMES), dtype=np.float32)
    mask = np.zeros(len(CONDITION_NAMES), dtype=np.float32)
    for name, value in values.items():
        if name not in CONDITION_NAMES:
            raise KeyError(f"unknown condition: {name}")
        if value is None or not math.isfinite(float(value)):
            continue
        index = CONDITION_NAMES.index(name)
        row[index] = float(value)
        mask[index] = 1.0
    return row, mask


def _composition(symbols: Iterable[str], values: Iterable[float]) -> tuple[np.ndarray, np.ndarray]:
    pairs = [
        (ATOMIC_NUMBER[symbol], float(value))
        for symbol, value in zip(symbols, values, strict=True)
        if float(value) > 0
    ]
    if not pairs:
        raise ValueError("empty catalyst composition")
    pairs.sort(key=lambda pair: pair[0])
    elements = np.asarray([pair[0] for pair in pairs], dtype=np.int64)
    fractions = np.asarray([pair[1] for pair in pairs], dtype=np.float32)
    fractions /= fractions.sum()
    return elements, fractions


def _program_id(name: str) -> int:
    try:
        return PROGRAM_NAMES.index(name)
    except ValueError:
        return 0


def _reaction_id(name: str) -> int:
    try:
        return REACTION_NAMES.index(name)
    except ValueError:
        return 0


def _modality_id(name: str) -> int:
    try:
        return MEASUREMENT_MODALITY_NAMES.index(name)
    except ValueError:
        return 0


def target_id(name: str) -> int:
    try:
        return TARGET_NAMES.index(name)
    except ValueError:
        return 0


def _read_excel_member(archive: zipfile.ZipFile, member: str) -> dict[str, pd.DataFrame]:
    payload = archive.read(member)
    return {
        sheet: pd.read_excel(io.BytesIO(payload), sheet_name=sheet).apply(
            pd.to_numeric, errors="raise"
        )
        for sheet in ("UV", "metals", "overpotential")
    }


def load_specgen_archive(path: Path, verify: bool = True) -> list[CatalystSample]:
    """Load the source and four complete derivative OER systems."""

    payload = read_pinned_bytes(
        path,
        expected_sha256=SPECGEN_SHA256 if verify else None,
        expected_size=SPECGEN_BYTES if verify else None,
    )
    members = {
        "specgen_source": "SpecGen/data/data.xlsx",
        "specgen_A": "SpecGen/data/transfer_A.xlsx",
        "specgen_B": "SpecGen/data/transfer_B.xlsx",
        "specgen_C": "SpecGen/data/transfer_C.xlsx",
        "specgen_D": "SpecGen/data/transfer_D.xlsx",
    }
    ligand = {
        "specgen_source": (2.0, 0.0, 0.0),
        "specgen_A": (2.0, 1.0, 0.0),
        "specgen_B": (3.0, 0.0, 0.0),
        "specgen_C": (2.0, 0.0, float(ATOMIC_NUMBER["Fe"])),
        "specgen_D": (2.0, 0.0, float(ATOMIC_NUMBER["Mn"])),
    }
    samples: list[CatalystSample] = []
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        for program, member in members.items():
            frames = _read_excel_member(archive, member)
            spectra = frames["UV"]
            metals = frames["metals"]
            outcomes = frames["overpotential"]["overpotential"].to_numpy(dtype=float)
            axis = np.asarray(spectra.columns, dtype=np.float32)
            if len(spectra) != len(metals) or len(spectra) != len(outcomes):
                raise ValueError(f"unaligned SpecGen sheets in {member}")
            carboxyl, amino, substitution = ligand[program]
            condition_values, condition_mask = _condition_vector(
                current_density_mA_cm2=10.0,
                ligand_carboxyl_count=carboxyl,
                ligand_amino_count=amino,
                substitution_atomic_number=substitution if substitution else None,
            )
            for index in range(len(spectra)):
                elements, fractions = _composition(
                    [str(column) for column in metals.columns],
                    metals.iloc[index].to_numpy(dtype=float),
                )
                primary = spectra.iloc[index].to_numpy(dtype=np.float32)
                values = np.column_stack(
                    [primary, np.zeros_like(primary)]
                ).astype(np.float32)
                # The source records potential vs RHE.  Convert to OER
                # overpotential in mV, matching the repository protocol.
                target = (float(outcomes[index]) - 1.23) * 1000.0
                sample = CatalystSample(
                    sample_id=f"{program}-{index:04d}",
                    program=program,
                    elements=elements,
                    fractions=fractions,
                    curve_axis=axis.copy(),
                    curve_values=values,
                    curve_channel_mask=np.asarray([1.0, 0.0], dtype=np.float32),
                    condition_values=condition_values.copy(),
                    condition_mask=condition_mask.copy(),
                    reaction_id=_reaction_id("OER"),
                    modality_id=_modality_id("UV_VIS_NIR"),
                    program_id=_program_id(program),
                    target=target,
                    target_name="oer_overpotential_mV",
                    group_id=program,
                    provenance={
                        "doi": "10.1038/s44160-025-00983-5",
                        "archive_sha256": SPECGEN_SHA256,
                        "member": member,
                        "row": index,
                    },
                )
                sample.validate()
                samples.append(sample)
    return samples


_COMPOSITION_PATTERN = re.compile(r"([A-Z][a-z]?)-([0-9]*\.?[0-9]+)")


def parse_ocx24_composition(value: str) -> tuple[np.ndarray, np.ndarray]:
    pairs = _COMPOSITION_PATTERN.findall(str(value))
    if not pairs:
        raise ValueError(f"cannot parse OCx24 composition: {value!r}")
    return _composition(
        [symbol for symbol, _ in pairs],
        [float(fraction) for _, fraction in pairs],
    )


def load_ocx24_csv(path: Path, target_name: str = "fe_co", verify: bool = True) -> list[CatalystSample]:
    """Load a selected OCx24 endpoint without discarding condition/provenance."""

    payload = read_pinned_bytes(
        path,
        expected_sha256=OCX24_SHA256 if verify else None,
        expected_size=OCX24_BYTES if verify else None,
    )
    frame = pd.read_csv(io.BytesIO(payload))
    allowed_targets = {
        "voltage",
        "fe_h2",
        "fe_co",
        "fe_ch4",
        "fe_c2h4",
        "fe_gas_total",
        "fe_liquid",
    }
    if target_name not in allowed_targets:
        raise ValueError(f"unsupported OCx24 target: {target_name}")
    samples: list[CatalystSample] = []
    for index, row in frame.iterrows():
        target = row.get(target_name)
        if pd.isna(target):
            continue
        elements, fractions = parse_ocx24_composition(str(row["xrf comp"]))
        condition_values, condition_mask = _condition_vector(
            current_density_mA_cm2=float(row["current density"]),
        )
        program = f"ocx24_{row['source']}"
        sample_id = str(row["sample id"])
        sample = CatalystSample(
            sample_id=f"{sample_id}|{row['reaction']}|{float(row['current density']):g}",
            program=program,
            elements=elements,
            fractions=fractions,
            curve_axis=np.zeros(0, dtype=np.float32),
            curve_values=np.zeros((0, 2), dtype=np.float32),
            curve_channel_mask=np.zeros(2, dtype=np.float32),
            condition_values=condition_values,
            condition_mask=condition_mask,
            reaction_id=_reaction_id(str(row["reaction"])),
            modality_id=_modality_id("none"),
            program_id=_program_id(program),
            target=float(target),
            target_name=target_name,
            group_id=sample_id,
            provenance={
                "dataset": "OCx24",
                "source_commit": "a838178c0b6cef68ed6b23167cc93c98ee26d2f7",
                "row": int(index),
                "batch": None if pd.isna(row.get("batch number")) else int(row["batch number"]),
                "batch_date": None if pd.isna(row.get("batch date")) else int(row["batch date"]),
            },
        )
        sample.validate()
        samples.append(sample)
    return samples


_LSV_NAME = re.compile(
    r"^SECCM_dataset/Au-Ir-Rh_(?P<library>[^_]+)_SECCM_area_(?P<area>\d+)_"
    r"x=(?P<x>-?[0-9.]+)_y=(?P<y>-?[0-9.]+)_LSV\.csv$"
)


def _zip_csv(archive: zipfile.ZipFile, member: str) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(archive.read(member)))


def load_seccm_archives(
    seccm_path: Path,
    edx_path: Path,
    xps_path: Path | None = None,
    target_name: str = "log10_k0",
    verify: bool = True,
) -> list[CatalystSample]:
    """Align Au-Ir-Rh compositions, optional surface state, LSVs, and fits.

    The fitted kinetic targets are derived from the same LSV and are therefore
    suitable for representation smoke tests, not independent mechanistic proof.
    """

    seccm_payload = read_pinned_bytes(
        seccm_path,
        expected_sha256=SECCM_SHA256 if verify else None,
        expected_size=SECCM_BYTES if verify else None,
    )
    edx_payload = read_pinned_bytes(
        edx_path,
        expected_sha256=SECCM_EDX_SHA256 if verify else None,
        expected_size=SECCM_EDX_BYTES if verify else None,
    )
    xps_payload = (
        read_pinned_bytes(
            xps_path,
            expected_sha256=SECCM_XPS_SHA256 if verify else None,
            expected_size=SECCM_XPS_BYTES if verify else None,
        )
        if xps_path is not None
        else None
    )
    if target_name not in {"log10_k0", "alpha", "i_lim"}:
        raise ValueError(f"unsupported SECCM target: {target_name}")
    with zipfile.ZipFile(io.BytesIO(edx_payload)) as edx_archive:
        compositions: dict[tuple[str, int], tuple[np.ndarray, np.ndarray]] = {}
        for library in ("Au-rich", "Ir-rich", "Rh-rich"):
            frame = _zip_csv(edx_archive, f"EDX_dataset/Au-Ir-Rh_{library}_EDX.csv")
            for _, row in frame.iterrows():
                compositions[(library, int(row["Area"]))] = _composition(
                    ("Au", "Ir", "Rh"),
                    (row["Au [at.%]"], row["Ir [at.%]"], row["Rh [at.%]"]),
                )
    xps_lookup: dict[tuple[str, int], tuple[np.ndarray, np.ndarray]] = {}
    if xps_payload is not None:
        with zipfile.ZipFile(io.BytesIO(xps_payload)) as xps_archive:
            for library in ("Au-rich", "Ir-rich", "Rh-rich"):
                member = f"XPS_dataset/Au-Ir-Rh_{library}_XPS_predicted.csv"
                frame = _zip_csv(xps_archive, member)
                for _, row in frame.iterrows():
                    xps_lookup[(library, int(row["Area"]))] = _composition(
                        ("Au", "Ir", "Rh"),
                        (
                            row["Au [at.%]"],
                            row["Ir [at.%]"],
                            row["Rh [at.%]"],
                        ),
                    )
    with zipfile.ZipFile(io.BytesIO(seccm_payload)) as seccm_archive:
        fits = _zip_csv(seccm_archive, "SECCM_dataset/LSV_fit_parameters.csv")
        fit_lookup = {
            (str(row["Library"]), int(row["Area"])): row
            for _, row in fits.iterrows()
        }
        samples: list[CatalystSample] = []
        for member in sorted(seccm_archive.namelist()):
            match = _LSV_NAME.search(member)
            if not match:
                continue
            library = match.group("library")
            area = int(match.group("area"))
            fit = fit_lookup.get((library, area))
            composition = compositions.get((library, area))
            if fit is None or composition is None:
                continue
            curve = _zip_csv(seccm_archive, member)
            axis = curve["Potential vs. RHE [V]"].to_numpy(dtype=np.float32)
            primary = curve["Current density [A/cm^2]"].to_numpy(dtype=np.float32)
            uncertainty = curve["Standard deviation [A/cm^2]"].to_numpy(dtype=np.float32)
            if target_name == "log10_k0":
                target = math.log10(float(fit["k^0 [cm/s]"]))
            elif target_name == "alpha":
                target = float(fit["alpha [a.u.]"])
            else:
                target = float(fit["i_lim [A/cm^2]"])
            condition_values, condition_mask = _condition_vector()
            elements, fractions = composition
            surface = xps_lookup.get(
                (library, area),
                (
                    np.zeros(0, dtype=np.int64),
                    np.zeros(0, dtype=np.float32),
                ),
            )
            sample = CatalystSample(
                sample_id=f"seccm-{library}-{area:03d}",
                program=f"seccm_{library}",
                elements=elements,
                fractions=fractions,
                curve_axis=axis,
                curve_values=np.column_stack([primary, uncertainty]).astype(np.float32),
                curve_channel_mask=np.ones(2, dtype=np.float32),
                condition_values=condition_values,
                condition_mask=condition_mask,
                reaction_id=_reaction_id("HER"),
                modality_id=_modality_id("LSV"),
                program_id=_program_id(f"seccm_{library}"),
                target=target,
                target_name=target_name,
                group_id=library,
                surface_elements=surface[0],
                surface_fractions=surface[1],
                provenance={
                    "doi": "10.5281/zenodo.20439519",
                    "seccm_sha256": SECCM_SHA256,
                    "edx_sha256": SECCM_EDX_SHA256,
                    "xps_sha256": SECCM_XPS_SHA256 if xps_path is not None else None,
                    "member": member,
                    "area": area,
                    "x_mm": float(match.group("x")),
                    "y_mm": float(match.group("y")),
                    "xps_surface_composition_available": bool(len(surface[0])),
                    "target_is_curve_derived": True,
                },
            )
            sample.validate()
            samples.append(sample)
    return samples


def samples_manifest(samples: Iterable[CatalystSample]) -> dict[str, Any]:
    rows = list(samples)
    by_program: dict[str, int] = {}
    by_target: dict[str, int] = {}
    for sample in rows:
        by_program[sample.program] = by_program.get(sample.program, 0) + 1
        by_target[sample.target_name] = by_target.get(sample.target_name, 0) + 1
    return {
        "samples": len(rows),
        "programs": dict(sorted(by_program.items())),
        "targets": dict(sorted(by_target.items())),
        "with_curves": sum(bool(len(sample.curve_axis)) for sample in rows),
        "with_uncertainty": sum(bool(sample.curve_channel_mask[1]) for sample in rows),
        "with_surface_composition": sum(
            bool(len(sample.surface_elements)) for sample in rows
        ),
        "with_targets": sum(sample.target is not None for sample in rows),
        "unique_groups": len({sample.group_id for sample in rows}),
    }


def write_manifest(path: Path, samples: Iterable[CatalystSample]) -> None:
    atomic_write_text(
        path,
        json.dumps(samples_manifest(samples), indent=2, sort_keys=True) + "\n",
    )
