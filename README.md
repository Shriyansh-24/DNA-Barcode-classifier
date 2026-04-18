# WildGuard DNA Classifier

WildGuard is a Streamlit-based wildlife DNA forensics app for rapid species identification from COI barcode sequences. It combines sequence sanitization, k-mer feature extraction, similarity scoring, and a Random Forest classifier to support CITES-focused enforcement workflows.

This is a student project and is not affiliated with any government institution. The title and enforcement framing are example use cases for demonstration.

## What This Project Does

- Accepts raw DNA or FASTA sequence input.
- Sanitizes and validates sequence data (ACGT-only cleaning).
- Compares query DNA against a local reference database built from BOLD Systems.
- Produces confidence-based identification outcomes: HIGH, AMBIGUOUS, or LOW.
- Displays legal context (CITES / IUCN metadata) for identified species.
- Generates downloadable forensic PDF reports.

## Main Components

- `app.py`: Streamlit UI and end-to-end analysis workflow.
- `dna_engine.py`: Core analysis engine (sanitization, k-mers, RF model, scoring).
- `reference_db.py`: Loads and structures `reference_db.csv` into runtime dictionaries.
- `bold_fetcher.py`: Fetches COI-5P sequences from BOLD APIs and writes/updates `reference_db.csv`.
- `report_generator.py`: Builds forensic PDF output (ReportLab-based).
- `reference_db.csv`: Local sequence and species metadata store used at runtime.

## Requirements

- Python 3.10+ recommended
- Internet connection for live BOLD fetch operations

Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

1. Ensure dependencies are installed.
2. Verify `reference_db.csv` exists (already present in this repository).
3. Launch the app:
```bash
streamlit run app.py
```

4. Open the local Streamlit URL shown in terminal (usually `http://localhost:8501`).

## Refreshing / Rebuilding the Reference Database

You can rebuild from terminal:

```bash
python bold_fetcher.py
```

Useful options:

```bash
python bold_fetcher.py --species "Panthera leo"
python bold_fetcher.py --max-seqs 8
python bold_fetcher.py --overwrite
```

The app also provides a sidebar button to refresh from BOLD API directly.

## Adding More Species to the Database

You have two supported ways to add species:

### Option A: Add Species via BOLD Fetcher (Recommended)

1. Open `bold_fetcher.py`.
2. Add the scientific name to `TARGET_SPECIES`, for example:

```python
TARGET_SPECIES = [
	# existing species...
	"Loxodonta africana",
]
```

3. Add metadata for the same species in `SPECIES_META` using the exact same scientific name key:

```python
SPECIES_META = {
	# existing species...
	"Loxodonta africana": {
		"common_name": "African Elephant",
		"iucn": "EN",
		"cites_appendix": "I",
		"emoji": "🐘",
		"native_range": "Sub-Saharan Africa",
		"trafficking_note": "Ivory trade pressure.",
	},
}
```

4. Rebuild the CSV:

```bash
python bold_fetcher.py --overwrite
```

5. Restart or rerun the Streamlit app so it reloads `reference_db.csv`.

Important:
- The `TARGET_SPECIES` name and `SPECIES_META` key must match exactly.
- The fetcher pulls COI-5P sequences and keeps valid barcode-like entries.
- If a species returns no records, test it alone with:

```bash
python bold_fetcher.py --species "Loxodonta africana"
```

### Option B: Add Species Manually to CSV

If BOLD fetch is unavailable, append rows directly to `reference_db.csv`.

Required columns:

`species_id, scientific_name, common_name, kingdom, phylum, class_, order, family, genus, iucn, cites_appendix, native_range, emoji, trafficking_note, gene, accession, sequence`

Guidelines:
- Use one row per accession/sequence.
- Keep DNA sequence as A/C/G/T characters.
- Use sequences at least 100 bp long (shorter rows are filtered out at load time).

After saving the CSV, restart/rerun the app.

## Input and Output

### Inputs

- Raw nucleotide sequence (COI target)
- FASTA text
- Uploaded FASTA files (`.fasta`, `.fa`, `.txt`)

### Outputs

- Species match candidates with similarity percentages
- Confidence classification (HIGH / AMBIGUOUS / LOW)
- Alignment-like metrics (length, identities, gaps, GC content, E-value estimate)
- Technical visualizations (k-mer distribution and candidate chart)
- PDF forensic report download

## How Identification Works (High Level)

1. Sanitize query sequence (remove headers/noise, keep A/C/G/T).
2. Convert sequence to normalized k-mer vectors.
3. Compute cosine similarity against reference species centroid vectors.
4. Use Random Forest probabilities as additional support signal.
5. Apply thresholds and tie logic to assign confidence level.

## Notes

- The model requires a minimum cleaned sequence length of 100 bp.
- Best results are typically near full COI barcode lengths.
- Species metadata (CITES/IUCN/common names/range) is carried in `reference_db.csv` rows.

## Troubleshooting

- `reference_db.csv not found`:
	- Run `python bold_fetcher.py` or place a valid CSV in the project root.

- `No sequences found` during fetch:
	- Retry later (API/network issues) or reduce request scope with `--species`.

- PDF generation fallback message:
	- Ensure `reportlab` is installed from `requirements.txt`.
