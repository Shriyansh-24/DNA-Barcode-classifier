"""
Reference Database Loader
=========================
Reads reference_db.csv (built by bold_fetcher.py) and exposes two dicts:

    REFERENCE_DATABASE  — used by DNAAnalysisEngine
    SPECIES_METADATA    — used by app.py for display

If the CSV doesnt exist yet, shows a clear error telling you to run bold_fetcher.py first.
"""

import re
import pandas as pd
from pathlib import Path

CSV_PATH = Path(__file__).parent / "reference_db.csv"


def _clean_seq(seq: str) -> str:
    s = re.sub(r"[\s\d\-\.\*]", "", str(seq)).upper()
    return re.sub(r"[^ACGT]", "", s)


def _load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str).fillna("")
    df = df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)
    df["sequence"] = df["sequence"].apply(_clean_seq)
    df = df[df["sequence"].str.len() >= 100].reset_index(drop=True)
    return df


def _build_reference_database(df: pd.DataFrame) -> dict:
    db = {}
    for species_id, group in df.groupby("species_id", sort=False):
        sequences = group["sequence"].tolist()
        row = group.iloc[0]
        db[species_id] = {
            "species_id": species_id,
            "sequences":  sequences,
            "taxonomy": {
                "kingdom": row.get("kingdom", "Animalia"),
                "phylum":  row.get("phylum", "Chordata"),
                "class_":  row.get("class_", ""),
                "order":   row.get("order", ""),
                "family":  row.get("family", ""),
                "genus":   row.get("genus", ""),
                "species": row.get("scientific_name", "").split()[-1],
            }
        }
    return db


def _build_species_metadata(df: pd.DataFrame) -> dict:
    meta = {}
    for species_id, group in df.groupby("species_id", sort=False):
        row = group.iloc[0]
        meta[species_id] = {
            "scientific_name":  row.get("scientific_name", ""),
            "common_name":      row.get("common_name", ""),
            "kingdom":          row.get("kingdom", "Animalia"),
            "phylum":           row.get("phylum", "Chordata"),
            "class_":           row.get("class_", ""),
            "order":            row.get("order", ""),
            "family":           row.get("family", ""),
            "genus":            row.get("genus", ""),
            "iucn":             row.get("iucn", "DD"),
            "cites_appendix":   row.get("cites_appendix", ""),
            "native_range":     row.get("native_range", ""),
            "emoji":            row.get("emoji", "🐾"),
            "trafficking_note": row.get("trafficking_note", ""),
            "gene":             row.get("gene", "COI-5P"),
            "n_sequences":      len(group),
            "accessions":       group["accession"].tolist() if "accession" in group.columns else [],
        }
    return meta


# ── Load on import ─────────────────────────────────────────────────────────────
if not CSV_PATH.exists():
    raise FileNotFoundError(
        "\n"
        "reference_db.csv not found!\n"
        "Run this first to fetch real sequences from BOLD:\n\n"
        "    python bold_fetcher.py\n\n"
        "This will create reference_db.csv with real COI sequences.\n"
    )

try:
    _df = _load_csv(CSV_PATH)
    if len(_df) == 0:
        raise ValueError("reference_db.csv is empty or has no valid sequences (>=100 bp).")
    REFERENCE_DATABASE = _build_reference_database(_df)
    SPECIES_METADATA   = _build_species_metadata(_df)
except FileNotFoundError:
    raise
except Exception as e:
    raise RuntimeError(f"Failed to load reference_db.csv: {e}")
