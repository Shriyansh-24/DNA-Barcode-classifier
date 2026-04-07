"""
BOLD API Fetcher
================
Fetches real COI-5P sequences from BOLD Systems for a target species list,
then writes / updates reference_db.csv.

Two BOLD APIs are attempted in order:
  1. BOLD Portal API (new, ~2024) — portal.boldsystems.org
     Three-step: preprocessor → query_id → download TSV/JSON
  2. BOLD v3 Public API (legacy, very reliable) — v3.boldsystems.org
     One-step: returns FASTA directly

Run this script once before starting the Streamlit app, or use the
"Refresh Database" button in the app sidebar which calls fetch_all().

Usage:
    python bold_fetcher.py                  # fetch all species, write CSV
    python bold_fetcher.py --species "Panthera leo"   # single species test
"""

import requests
import re
import time
import pandas as pd
import csv
import json
import argparse
import sys
from pathlib import Path
from io import StringIO

# ─── Target Species List ──────────────────────────────────────────────────────
# Edit this list to add or remove species.
TARGET_SPECIES = [
    "Acinonyx jubatus",        # Cheetah
    "Panthera leo",            # African Lion
    "Panthera pardus",         # Leopard
    "Pan troglodytes",         # Common Chimpanzee
    "Smutsia temminckii",      # Temminck's Pangolin
    "Caracal caracal",         # Caracal
    "Felis margarita",         # Sand Cat
    "Papio hamadryas",         # Hamadryas Baboon
    "Falco cherrug",           # Saker Falcon
    "Falco peregrinus",        # Peregrine Falcon
    "Psittacus erithacus",     # African Grey Parrot
    "Pycnonotus leucotis",     # White-eared Bulbul
    "Chlamydotis undulata",    # Houbara Bustard
    "Carduelis carduelis",     # European Goldfinch
    "Uromastyx aegyptia",      # Egyptian Mastigure / Spiny-tailed Lizard
    "Testudo graeca",          # Spur-thighed Tortoise
    "Trachemys scripta",       # Red-eared Slider
    "Crocodylus niloticus",    # Nile Crocodile
    "Anguilla anguilla",       # European Eel
    "Glaucostegus cemiculus",  # Smalltooth Sawfish
]

# ─── Species Metadata (CITES / IUCN / etc.) ───────────────────────────────────
# This is the only part you still manually maintain — BOLD doesn't carry CITES data.
SPECIES_META = {
    "Acinonyx jubatus":       {"common_name": "Cheetah",                  "iucn": "VU",  "cites_appendix": "I",  "emoji": "🐆", "native_range": "Africa and central Iran",                         "trafficking_note": "Live cubs traded as exotic pets in Gulf region."},
    "Panthera leo":           {"common_name": "African Lion",             "iucn": "VU",  "cites_appendix": "II", "emoji": "🦁", "native_range": "Sub-Saharan Africa; Gir Forest India",             "trafficking_note": "Bones used as tiger-bone substitute in TCM."},
    "Panthera pardus":        {"common_name": "Leopard",                  "iucn": "VU",  "cites_appendix": "I",  "emoji": "🐆", "native_range": "Africa and Asia",                                  "trafficking_note": "Skin and bones trafficked widely."},
    "Pan troglodytes":        {"common_name": "Common Chimpanzee",        "iucn": "EN",  "cites_appendix": "I",  "emoji": "🐒", "native_range": "Equatorial Africa",                               "trafficking_note": "Bushmeat and live infant pet trade."},
    "Smutsia temminckii":     {"common_name": "Temminck's Pangolin",      "iucn": "VU",  "cites_appendix": "I",  "emoji": "🦔", "native_range": "East and Southern Africa",                        "trafficking_note": "Most trafficked mammal; scales used in TCM."},
    "Caracal caracal":        {"common_name": "Caracal",                  "iucn": "LC",  "cites_appendix": "II", "emoji": "🐱", "native_range": "Africa, Middle East, Central and South Asia",     "trafficking_note": "Traded as exotic pet especially in Gulf states."},
    "Felis margarita":        {"common_name": "Sand Cat",                 "iucn": "LC",  "cites_appendix": "II", "emoji": "🐱", "native_range": "North Africa, Arabian Peninsula, Central Asia",   "trafficking_note": "Exotic pet trade; elusive desert specialist."},
    "Papio hamadryas":        {"common_name": "Hamadryas Baboon",         "iucn": "LC",  "cites_appendix": "II", "emoji": "🐒", "native_range": "Horn of Africa, Arabian Peninsula",              "trafficking_note": "Live animal trade for research and pets."},
    "Falco cherrug":          {"common_name": "Saker Falcon",             "iucn": "EN",  "cites_appendix": "II", "emoji": "🦅", "native_range": "Central Europe to Central Asia",                 "trafficking_note": "Highly prized for falconry in Gulf states."},
    "Falco peregrinus":       {"common_name": "Peregrine Falcon",         "iucn": "LC",  "cites_appendix": "I",  "emoji": "🦅", "native_range": "Cosmopolitan",                                    "trafficking_note": "Falconry trade; fastest animal on Earth."},
    "Psittacus erithacus":    {"common_name": "African Grey Parrot",      "iucn": "EN",  "cites_appendix": "I",  "emoji": "🦜", "native_range": "Equatorial Africa",                              "trafficking_note": "World's most trafficked parrot species."},
    "Pycnonotus leucotis":    {"common_name": "White-eared Bulbul",       "iucn": "LC",  "cites_appendix": "II", "emoji": "🐦", "native_range": "Middle East to South Asia",                      "trafficking_note": "Songbird trade; popular cage bird in Gulf."},
    "Chlamydotis undulata":   {"common_name": "Houbara Bustard",          "iucn": "VU",  "cites_appendix": "I",  "emoji": "🦃", "native_range": "Canary Islands to Central Asia",                 "trafficking_note": "Prized falconry quarry; massive harvest pressure."},
    "Carduelis carduelis":    {"common_name": "European Goldfinch",       "iucn": "LC",  "cites_appendix": "II", "emoji": "🐦", "native_range": "Europe, North Africa, Western and Central Asia",  "trafficking_note": "Most captured songbird in Mediterranean."},
    "Uromastyx aegyptia":     {"common_name": "Egyptian Spiny-tailed Lizard", "iucn": "VU", "cites_appendix": "II", "emoji": "🦎", "native_range": "North Africa and Middle East",              "trafficking_note": "Exotic pet trade; eaten locally."},
    "Testudo graeca":         {"common_name": "Spur-thighed Tortoise",    "iucn": "VU",  "cites_appendix": "II", "emoji": "🐢", "native_range": "North Africa, Southern Europe, Middle East",     "trafficking_note": "One of the most traded tortoises globally."},
    "Trachemys scripta":      {"common_name": "Red-eared Slider",         "iucn": "LC",  "cites_appendix": "II", "emoji": "🐢", "native_range": "Southern USA; invasive worldwide",              "trafficking_note": "Invasive pet trade species — import controlled in EU."},
    "Crocodylus niloticus":   {"common_name": "Nile Crocodile",           "iucn": "LC",  "cites_appendix": "I",  "emoji": "🐊", "native_range": "Sub-Saharan Africa and Madagascar",             "trafficking_note": "Skin for luxury leather; live animal trade."},
    "Anguilla anguilla":      {"common_name": "European Eel",             "iucn": "CR",  "cites_appendix": "II", "emoji": "🐟", "native_range": "Europe and North Africa (Atlantic coast)",        "trafficking_note": "Glass eels trafficked to Asia for aquaculture."},
    "Glaucostegus cemiculus": {"common_name": "Smalltooth Sawfish",       "iucn": "CR",  "cites_appendix": "I",  "emoji": "🦈", "native_range": "Eastern Atlantic and Mediterranean",             "trafficking_note": "Rostrum (saw) traded as curio and TCM ingredient."},
}

CSV_PATH = Path(__file__).parent / "reference_db.csv"
CSV_COLUMNS = [
    "species_id", "scientific_name", "common_name",
    "kingdom", "phylum", "class_", "order", "family", "genus",
    "iucn", "cites_appendix", "native_range", "emoji", "trafficking_note",
    "gene", "accession", "sequence"
]

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _species_id(name: str) -> str:
    """Convert 'Panthera leo' → 'panthera_leo'"""
    return name.lower().replace(" ", "_")


def _clean_seq(seq: str) -> str:
    """Strip whitespace, digits, dashes, keep only ACGT."""
    s = re.sub(r"[\s\d\-\.\*]", "", seq).upper()
    return re.sub(r"[^ACGT]", "", s)


def _parse_fasta(fasta_text: str) -> list[dict]:
    """Parse a multi-FASTA string → list of {header, sequence}."""
    records = []
    current_header = None
    current_seq_parts = []
    for line in fasta_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if current_header is not None:
                records.append({
                    "header": current_header,
                    "sequence": _clean_seq("".join(current_seq_parts))
                })
            current_header = line[1:]
            current_seq_parts = []
        else:
            current_seq_parts.append(line)
    if current_header is not None:
        records.append({
            "header": current_header,
            "sequence": _clean_seq("".join(current_seq_parts))
        })
    return records


def _extract_accession(header: str) -> str:
    """Pull process ID / accession from a BOLD FASTA header."""
    parts = header.split("|")
    return parts[0].strip() if parts else header[:20]


# ─── BOLD v3 API (legacy — very reliable, returns FASTA directly) ─────────────

def fetch_v3(species_name: str, max_seqs: int = 5) -> list[dict]:
    """
    BOLD v3 Public API sequence endpoint.
    GET http://v3.boldsystems.org/index.php/API_Public/sequence
         ?taxon=<name>&marker=COI-5P
    Returns list of {accession, sequence} dicts.
    """
    url = "http://v3.boldsystems.org/index.php/API_Public/sequence"
    params = {"taxon": species_name, "marker": "COI-5P"}
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        records = _parse_fasta(resp.text)
        # Filter: keep only sequences >= 400 bp (full barcodes)
        good = [r for r in records if len(r["sequence"]) >= 400]
        # Return up to max_seqs, picking the longest ones
        good.sort(key=lambda x: len(x["sequence"]), reverse=True)
        return [{"accession": _extract_accession(r["header"]),
                 "sequence": r["sequence"]} for r in good[:max_seqs]]
    except Exception as e:
        print(f"    [v3 API error] {species_name}: {e}")
        return []


# ─── BOLD Portal API (new 2024 — 3-step token flow) ──────────────────────────

def fetch_portal(species_name: str, max_seqs: int = 5) -> list[dict]:
    """
    BOLD Portal API (portal.boldsystems.org).
    Step 1: preprocessor → get validated query string
    Step 2: /api/query → get query_id token
    Step 3: /api/documents/<query_id>/download?format=tsv → stream TSV rows
    """
    base = "https://portal.boldsystems.org"
    headers = {"Accept": "application/json"}

    try:
        # Step 1 — Preprocess query
        pre_url = f"{base}/api/query/preprocessor"
        pre_resp = requests.get(
            pre_url,
            params={"query": f"tax:{species_name};marker:COI-5P"},
            headers=headers, timeout=20
        )
        pre_resp.raise_for_status()
        pre_data = pre_resp.json()
        validated_query = pre_data.get("validated_query", f"tax:{species_name}")

        # Step 2 — Get query token
        q_url = f"{base}/api/query"
        q_resp = requests.get(
            q_url,
            params={"query": validated_query, "extent": max_seqs},
            headers=headers, timeout=20
        )
        q_resp.raise_for_status()
        query_id = q_resp.json().get("query_id")
        if not query_id:
            return []

        # Step 3 — Download TSV
        dl_url = f"{base}/api/documents/{query_id}/download"
        dl_resp = requests.get(
            dl_url,
            params={"format": "tsv"},
            timeout=60, stream=True
        )
        dl_resp.raise_for_status()

        tsv_text = dl_resp.text
        reader = csv.DictReader(StringIO(tsv_text), delimiter="\t")
        results = []
        for row in reader:
            seq = _clean_seq(row.get("nucleotides", "") or row.get("sequence", ""))
            acc = row.get("processid", row.get("recordID", "unknown"))
            marker = row.get("marker_code", row.get("markercode", ""))
            if "COI" in marker.upper() and len(seq) >= 400:
                results.append({"accession": acc, "sequence": seq})
            if len(results) >= max_seqs:
                break
        return results

    except Exception as e:
        print(f"    [Portal API error] {species_name}: {e}")
        return []


# ─── Main Fetcher ─────────────────────────────────────────────────────────────

def fetch_species(species_name: str, max_seqs: int = 5, verbose: bool = True) -> list[dict]:
    """
    Fetch up to max_seqs COI sequences for species_name.
    Tries Portal API first, falls back to v3 API.
    Returns list of row-dicts ready to write to CSV.
    """
    if verbose:
        print(f"  Fetching: {species_name}")

    meta = SPECIES_META.get(species_name, {})
    sid = _species_id(species_name)
    name_parts = species_name.split()
    genus = name_parts[0] if name_parts else ""

    base_row = {
        "species_id":      sid,
        "scientific_name": species_name,
        "common_name":     meta.get("common_name", ""),
        "kingdom":         "Animalia",
        "phylum":          "Chordata",
        "class_":          "",          # filled below if we get taxonomy
        "order":           "",
        "family":          "",
        "genus":           genus,
        "iucn":            meta.get("iucn", "DD"),
        "cites_appendix":  meta.get("cites_appendix", ""),
        "native_range":    meta.get("native_range", ""),
        "emoji":           meta.get("emoji", "🐾"),
        "trafficking_note": meta.get("trafficking_note", ""),
        "gene":            "COI-5P",
    }

    # Try Portal API first, then v3
    seqs = fetch_portal(species_name, max_seqs=max_seqs)
    if not seqs:
        if verbose:
            print(f"    Portal returned 0 — trying v3 API...")
        time.sleep(0.5)
        seqs = fetch_v3(species_name, max_seqs=max_seqs)

    if not seqs:
        if verbose:
            print(f"    ⚠️  No sequences found for {species_name}")
        return []

    if verbose:
        print(f"    ✓ Got {len(seqs)} sequences "
              f"(lengths: {[len(s['sequence']) for s in seqs]})")

    rows = []
    for s in seqs:
        row = dict(base_row)
        row["accession"] = s["accession"]
        row["sequence"]  = s["sequence"]
        rows.append(row)

    return rows


def fetch_all(
    species_list: list[str] = None,
    max_seqs_per_species: int = 5,
    output_path: Path = CSV_PATH,
    overwrite: bool = False,
    verbose: bool = True,
):
    """
    Fetch sequences for all species and write/update the CSV.

    Args:
        species_list:           List of scientific names. Defaults to TARGET_SPECIES.
        max_seqs_per_species:   How many BOLD sequences to pull per species (3–10).
        output_path:            Where to write the CSV.
        overwrite:              If False, skip species already in the CSV.
        verbose:                Print progress.
    """
    if species_list is None:
        species_list = TARGET_SPECIES

    # Load existing CSV if present and not overwriting
    existing_ids = set()
    existing_rows = []
    if output_path.exists() and not overwrite:
        try:
            existing_df = pd.read_csv(output_path, dtype=str).fillna("")
            existing_ids = set(existing_df["species_id"].unique())
            existing_rows = existing_df.to_dict("records")
            if verbose:
                print(f"Loaded existing CSV: {len(existing_rows)} rows, "
                      f"{len(existing_ids)} species already present.")
        except Exception:
            pass

    all_rows = list(existing_rows)
    failed = []

    for i, name in enumerate(species_list, 1):
        sid = _species_id(name)
        if sid in existing_ids and not overwrite:
            if verbose:
                print(f"  [{i}/{len(species_list)}] Skipping {name} (already in CSV)")
            continue

        if verbose:
            print(f"\n[{i}/{len(species_list)}]", end=" ")

        rows = fetch_species(name, max_seqs=max_seqs_per_species, verbose=verbose)

        if rows:
            # Remove old entries for this species if overwriting
            all_rows = [r for r in all_rows if r.get("species_id") != sid]
            all_rows.extend(rows)
        else:
            failed.append(name)

        # Be polite to BOLD servers
        time.sleep(1.0)

    # Write CSV
    df = pd.DataFrame(all_rows, columns=CSV_COLUMNS)
    df.to_csv(output_path, index=False)

    if verbose:
        print(f"\n{'='*60}")
        print(f"✓ CSV written to: {output_path}")
        print(f"  Total rows:    {len(df)}")
        print(f"  Total species: {df['species_id'].nunique()}")
        if failed:
            print(f"\n⚠️  Failed to fetch ({len(failed)} species):")
            for f in failed:
                print(f"   - {f}")
            print("  → These species need manual sequences added to the CSV.")

    return df


# ─── CLI entry point ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch COI sequences from BOLD and build reference_db.csv"
    )
    parser.add_argument(
        "--species", type=str, default=None,
        help="Single species to test (e.g. 'Panthera leo')"
    )
    parser.add_argument(
        "--max-seqs", type=int, default=5,
        help="Max sequences per species (default: 5)"
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="Re-fetch even species already in the CSV"
    )
    args = parser.parse_args()

    if args.species:
        print(f"\nTesting single species: {args.species}")
        rows = fetch_species(args.species, max_seqs=args.max_seqs)
        if rows:
            print(f"\nGot {len(rows)} sequences:")
            for r in rows:
                print(f"  {r['accession']} — {len(r['sequence'])} bp")
                print(f"  {r['sequence'][:80]}...")
        else:
            print("No sequences returned.")
    else:
        fetch_all(
            max_seqs_per_species=args.max_seqs,
            overwrite=args.overwrite,
        )
