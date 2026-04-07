# 🧬 WildGuard — DNA Forensics Platform
### CITES Enforcement Tool · Hamad International Airport (

*THIS IS A STUDENT MADE PROJECT NOT RELATED TO ANY GOVERNMENT OR INSTITUITION. THE TITLE IS JUST AN EXAMPLE OF AN USE CASE OF THE APP*

Real-time species identification from COI-5P DNA sequences.
Built for customs officers and wildlife forensics specialists.

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Fetch real COI sequences from BOLD Systems
```bash
python bold_fetcher.py
```
This queries the BOLD Systems public API and downloads up to 5 real
COI-5P sequences per species, writing them to `reference_db.csv`.

Options:
```bash
python bold_fetcher.py --max-seqs 8               # fetch 8 sequences per species
python bold_fetcher.py --overwrite                 # re-fetch everything fresh
python bold_fetcher.py --species "Falco cherrug"   # test a single species
```

### 3. Launch the app
```bash
streamlit run app.py
```

---

## Target Species (20 Priority Forensic Taxa)

| Species | Common Name | CITES | IUCN |
|---|---|---|---|
| Acinonyx jubatus | Cheetah | I | VU |
| Panthera leo | African Lion | II | VU |
| Panthera pardus | Leopard | I | VU |
| Pan troglodytes | Common Chimpanzee | I | EN |
| Smutsia temminckii | Temminck's Pangolin | I | VU |
| Caracal caracal | Caracal | II | LC |
| Felis margarita | Sand Cat | II | LC |
| Papio hamadryas | Hamadryas Baboon | II | LC |
| Falco cherrug | Saker Falcon | II | EN |
| Falco peregrinus | Peregrine Falcon | I | LC |
| Psittacus erithacus | African Grey Parrot | I | EN |
| Pycnonotus leucotis | White-eared Bulbul | II | LC |
| Chlamydotis undulata | Houbara Bustard | I | VU |
| Carduelis carduelis | European Goldfinch | II | LC |
| Uromastyx aegyptia | Egyptian Spiny-tailed Lizard | II | VU |
| Testudo graeca | Spur-thighed Tortoise | II | VU |
| Trachemys scripta | Red-eared Slider | II | LC |
| Crocodylus niloticus | Nile Crocodile | I | LC |
| Anguilla anguilla | European Eel | II | CR |
| Glaucostegus cemiculus | Smalltooth Sawfish | I | CR |

*More species planned to be added weekly, trying to scale the project properly to its not too slow*

---

## Project Structure

```
wildlife_dna_app/
├── app.py               Streamlit UI (Officer + Specialist views)
├── bold_fetcher.py      BOLD API client (Portal API + v3 fallback)
├── reference_db.py      CSV loader, exposes REFERENCE_DATABASE + SPECIES_METADATA
├── dna_engine.py        Sanitizer, k-mer vectorizer, Random Forest classifier
├── report_generator.py  PDF forensic report generator (ReportLab)
├── reference_db.csv     Built by bold_fetcher.py — real BOLD sequences
└── requirements.txt
```

---

## How Analysis Works

```
Input (paste / .fasta upload)
         |
    [SANITIZER]        strips FASTA headers, spaces, non-ACGT chars
         |
  [K-MER VECTORIZER]   k=4 sliding window → 256-dim frequency vector
         |
 [COSINE SIMILARITY]   compare against all 20 reference centroids
         |
  [RANDOM FOREST]      200-tree vote across all species classes
         |
 [CONFIDENCE LOGIC]    HIGH >=98% | AMBIGUOUS 95-97% | LOW <95%
         |
    [OUTPUT]           Traffic light, CITES action, PDF report
```

---

## Adding More Species (To be added later)

1. Add entry to `SPECIES_META` dict in `bold_fetcher.py`
2. Add species name to `TARGET_SPECIES` list in `bold_fetcher.py`
3. Run `python bold_fetcher.py` — skips already-fetched species automatically

---

## Data Sources

- **Sequences**: BOLD Systems (boldsystems.org) — vouchered COI-5P barcodes
- **CITES status**: manually curated in `bold_fetcher.py`
- **IUCN status**: manually curated, verify latest at iucnredlist.org

---
