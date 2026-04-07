"""
DNA Analysis Engine
Sanitization → K-mer Vectorization → RF Classification → Confidence Scoring
"""

import re
import math
import numpy as np
from collections import Counter
from itertools import product
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import normalize


class DNAAnalysisEngine:
    """
    COI-based species identification engine.
    Pipeline: sanitize → k-mer features → cosine similarity → RF confidence → E-value
    """

    HIGH_SIMILARITY_THRESHOLD = 98.0
    AMBIGUOUS_LOW_THRESHOLD = 95.0
    HIGH_EVALUE_EXP = -100

    def __init__(self, reference_db: dict):
        self.reference_db = reference_db
        self.clf = None
        self.ref_vectors = {}
        self.species_ids = list(reference_db.keys())
        self._kmer_size = 4

    # ─── Sanitization ─────────────────────────────────────────────────────────
    def sanitize(self, raw: str) -> dict:
        """Strip FASTA header, whitespace, non-ACGT chars, convert to uppercase."""
        raw_len = len(raw.strip())
        had_header = False
        lines = raw.strip().splitlines()

        # Strip FASTA header(s)
        seq_lines = []
        for line in lines:
            if line.startswith(">") or line.startswith(";"):
                had_header = True
                continue
            seq_lines.append(line)

        joined = "".join(seq_lines)
        # Remove whitespace, digits, dashes, dots
        pre_clean = re.sub(r"[\s\d\-\.\*]", "", joined).upper()
        # Keep only ACGT (IUPAC ambiguous → remove for MVP)
        clean = re.sub(r"[^ACGT]", "", pre_clean)

        return {
            "clean_seq": clean,
            "raw_len": raw_len,
            "clean_len": len(clean),
            "had_header": had_header,
            "removed_chars": raw_len - len(clean),
        }

    # ─── K-mer Vectorization ───────────────────────────────────────────────────
    def kmer_vector(self, seq: str, k: int = 4) -> np.ndarray:
        """Count all k-mers in sequence, return normalized frequency vector."""
        all_kmers = ["".join(p) for p in product("ACGT", repeat=k)]
        kmer_index = {km: i for i, km in enumerate(all_kmers)}
        vec = np.zeros(4**k)
        for i in range(len(seq) - k + 1):
            km = seq[i:i+k]
            if km in kmer_index:
                vec[kmer_index[km]] += 1
        total = vec.sum()
        if total > 0:
            vec = vec / total
        return vec

    def top_kmers(self, seq: str, k: int = 4, n: int = 20):
        """Return top-n most frequent k-mers."""
        counts = Counter(seq[i:i+k] for i in range(len(seq)-k+1) if all(c in "ACGT" for c in seq[i:i+k]))
        return counts.most_common(n)

    # ─── Fit reference model ───────────────────────────────────────────────────
    def fit(self, kmer_size: int = 4):
        """Pre-compute reference k-mer vectors and train RF classifier.
        Supports both old single 'sequence' key and new multi-sequence 'sequences' list.
        When multiple sequences exist, stores their centroid vector for cosine similarity.
        """
        self._kmer_size = kmer_size
        X, y = [], []

        for sid, data in self.reference_db.items():
            # Support both formats: 'sequences' (list) and 'sequence' (str)
            seqs = data.get("sequences", None)
            if seqs is None:
                single = data.get("sequence", "")
                seqs = [single] if single else []

            # Filter too-short sequences
            seqs = [s for s in seqs if len(s) >= 100]
            if not seqs:
                continue

            # Build centroid vector — average k-mer profile across all accessions
            all_vecs = [self.kmer_vector(s, k=kmer_size) for s in seqs]
            centroid = np.mean(all_vecs, axis=0)
            self.ref_vectors[sid] = centroid  # used for cosine similarity

            # Augment training data with sub-sequence windows from every accession
            for seq in seqs:
                for start in range(0, max(1, len(seq) - 200), 50):
                    sub = seq[start:start + 300]
                    if len(sub) >= 100:
                        X.append(self.kmer_vector(sub, k=kmer_size))
                        y.append(sid)
                # Also train on full sequence
                X.append(self.kmer_vector(seq, k=kmer_size))
                y.append(sid)

        self.clf = RandomForestClassifier(
            n_estimators=200, max_depth=None, random_state=42,
            class_weight="balanced", n_jobs=-1
        )
        self.clf.fit(np.array(X), y)

    # ─── Similarity scoring ────────────────────────────────────────────────────
    def cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)
        if n1 == 0 or n2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (n1 * n2)) * 100.0

    def compute_evalue(self, similarity: float, query_len: int, db_size: int = 20) -> str:
        """Approximate E-value based on similarity score and sequence length."""
        if similarity >= 99.5:
            exp = -150
        elif similarity >= 98.0:
            exp = -120
        elif similarity >= 97.0:
            exp = -90
        elif similarity >= 95.0:
            exp = -60
        elif similarity >= 90.0:
            exp = -40
        else:
            exp = max(-10, int(-similarity / 3))

        # Adjust by sequence length
        length_factor = max(0, int(math.log10(query_len / 200 + 0.01)))
        exp = exp - length_factor
        return f"10^{exp}"

    def gc_content(self, seq: str) -> float:
        if not seq:
            return 0.0
        gc = seq.count("G") + seq.count("C")
        return (gc / len(seq)) * 100.0

    # ─── Main Analysis ────────────────────────────────────────────────────────
    def analyze(self, raw_input: str, kmer_size: int = 4, strict: bool = False) -> dict:
        """Full analysis pipeline. Returns structured result dict."""

        # 1. Sanitize
        san = self.sanitize(raw_input)
        seq = san["clean_seq"]

        if len(seq) < 100:
            return {**san, "error": f"Sequence too short after sanitization ({len(seq)} bp). Minimum 100 bp required.", "top_match": None}

        # 2. Re-fit if kmer size changed
        if kmer_size != self._kmer_size:
            self.fit(kmer_size)
            self._kmer_size = kmer_size

        # 3. Vectorize query
        q_vec = self.kmer_vector(seq, k=kmer_size)

        # 4. Compute similarities against all reference sequences
        similarities = {}
        for sid, ref_vec in self.ref_vectors.items():
            similarities[sid] = self.cosine_similarity(q_vec, ref_vec)

        # Sort candidates
        candidates = sorted(
            [{"species_id": k, "similarity": v} for k, v in similarities.items()],
            key=lambda x: x["similarity"],
            reverse=True
        )

        top = candidates[0]
        sim = top["similarity"]

        # 5. RF probability scores
        proba = self.clf.predict_proba([q_vec])[0]
        classes = self.clf.classes_
        rf_scores = {c: p for c, p in zip(classes, proba)}

        # 6. Determine confidence level
        high_thresh = 98.0 if not strict else 99.0
        amb_low = 95.0 if not strict else 97.0

        # Check for ties (top-2 within 1%)
        tie = len(candidates) > 1 and (candidates[0]["similarity"] - candidates[1]["similarity"]) < 1.0

        if sim >= high_thresh and not tie:
            confidence = "HIGH"
        elif sim >= amb_low or (sim >= high_thresh and tie):
            confidence = "AMBIGUOUS"
        else:
            confidence = "LOW"

        # 7. E-value
        # Support both 'sequences' list (new) and 'sequence' str (legacy)
        _top_entry = self.reference_db[top["species_id"]]
        _ref_seqs  = _top_entry.get("sequences") or [_top_entry.get("sequence", "")]
        ref_seq    = max(_ref_seqs, key=len)          # longest accession as representative
        ref_seq_len = len(ref_seq)
        evalue = self.compute_evalue(sim, len(seq), db_size=len(self.reference_db))

        # 8. Alignment stats (approximate)
        aligned     = min(len(seq), ref_seq_len)
        identities  = int(aligned * sim / 100)
        gaps        = max(0, abs(len(seq) - ref_seq_len))

        # 9. Top k-mers for visualisation
        kmer_top20 = self.top_kmers(seq, k=kmer_size, n=20)

        return {
            **san,
            "error": None,
            "top_match": top,
            "candidates": candidates,
            "similarity": sim,
            "confidence_level": confidence,
            "evalue": evalue,
            "ref_len": len(ref_seq),
            "aligned_positions": aligned,
            "identities": identities,
            "gaps": gaps,
            "gc_content": self.gc_content(seq),
            "kmer_top20": kmer_top20,
            "rf_top_score": rf_scores.get(top["species_id"], 0.0),
        }
