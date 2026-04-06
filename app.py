"""
WildGuard DNA Forensics Platform
CITES Enforcement Tool for Wildlife Trafficking Detection
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from io import StringIO, BytesIO
import re
import json
from datetime import datetime
import base64

from reference_db import REFERENCE_DATABASE, SPECIES_METADATA
from dna_engine import DNAAnalysisEngine
from report_generator import generate_pdf_report

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WildGuard | DNA Forensics",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg-primary: #0a0e1a;
    --bg-secondary: #111827;
    --bg-card: #141c2e;
    --accent-green: #00ff88;
    --accent-yellow: #ffd700;
    --accent-red: #ff3b5c;
    --accent-blue: #00b4ff;
    --text-primary: #e8edf5;
    --text-secondary: #8899bb;
    --border: #1e2d4a;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--bg-primary);
    color: var(--text-primary);
}

.stApp { background-color: var(--bg-primary); }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1322 0%, #0a0e1a 100%);
    border-right: 1px solid var(--border);
}

/* Headers */
h1, h2, h3 { font-family: 'Space Mono', monospace; }

/* Cards */
.dna-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin: 10px 0;
}

/* Traffic Light */
.tl-green {
    background: linear-gradient(135deg, #002a1a, #004d2e);
    border: 2px solid var(--accent-green);
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    box-shadow: 0 0 30px rgba(0,255,136,0.15);
}
.tl-yellow {
    background: linear-gradient(135deg, #2a2000, #4d3d00);
    border: 2px solid var(--accent-yellow);
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    box-shadow: 0 0 30px rgba(255,215,0,0.15);
}
.tl-red {
    background: linear-gradient(135deg, #2a0010, #4d001e);
    border: 2px solid var(--accent-red);
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    box-shadow: 0 0 30px rgba(255,59,92,0.2);
}

/* Metric tiles */
.metric-tile {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
    text-align: center;
}
.metric-value {
    font-family: 'Space Mono', monospace;
    font-size: 1.8rem;
    font-weight: 700;
}
.metric-label {
    color: var(--text-secondary);
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-top: 4px;
}

/* CITES Badge */
.cites-I { background: #ff3b5c22; border: 1px solid #ff3b5c; color: #ff3b5c; border-radius: 6px; padding: 3px 10px; font-size: 0.8rem; font-family: 'Space Mono', monospace; }
.cites-II { background: #ffd70022; border: 1px solid #ffd700; color: #ffd700; border-radius: 6px; padding: 3px 10px; font-size: 0.8rem; font-family: 'Space Mono', monospace; }
.cites-III { background: #00b4ff22; border: 1px solid #00b4ff; color: #00b4ff; border-radius: 6px; padding: 3px 10px; font-size: 0.8rem; font-family: 'Space Mono', monospace; }
.cites-none { background: #88998b22; border: 1px solid #889988; color: #889988; border-radius: 6px; padding: 3px 10px; font-size: 0.8rem; font-family: 'Space Mono', monospace; }

/* IUCN */
.iucn-CR { color: #ff3b5c; font-weight: 600; }
.iucn-EN { color: #ff7c44; font-weight: 600; }
.iucn-VU { color: #ffd700; font-weight: 600; }
.iucn-NT { color: #00b4ff; }
.iucn-LC { color: #00ff88; }

/* Code/Sequence display */
.seq-display {
    font-family: 'Space Mono', monospace;
    font-size: 0.72rem;
    background: #050810;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px;
    word-break: break-all;
    color: #4dbbff;
    line-height: 1.8;
}

/* Action boxes */
.action-arrest { background: #ff3b5c18; border-left: 4px solid #ff3b5c; padding: 12px 16px; border-radius: 0 8px 8px 0; margin: 8px 0; }
.action-hold { background: #ffd70018; border-left: 4px solid #ffd700; padding: 12px 16px; border-radius: 0 8px 8px 0; margin: 8px 0; }
.action-review { background: #00b4ff18; border-left: 4px solid #00b4ff; padding: 12px 16px; border-radius: 0 8px 8px 0; margin: 8px 0; }

/* Divider */
.hline { border: none; border-top: 1px solid var(--border); margin: 20px 0; }

/* Buttons */
.stButton>button {
    background: linear-gradient(135deg, #001a3a, #002a5c);
    color: var(--accent-blue);
    border: 1px solid var(--accent-blue);
    border-radius: 8px;
    font-family: 'Space Mono', monospace;
    font-size: 0.8rem;
    letter-spacing: 1px;
    transition: all 0.2s;
}
.stButton>button:hover {
    background: linear-gradient(135deg, #002a5c, #003d80);
    box-shadow: 0 0 15px rgba(0,180,255,0.3);
}

/* Logo */
.logo-text {
    font-family: 'Space Mono', monospace;
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--accent-blue);
    letter-spacing: 2px;
}
.logo-sub {
    font-size: 0.65rem;
    color: var(--text-secondary);
    letter-spacing: 3px;
    text-transform: uppercase;
}

/* Taxonomy tree */
.taxon-row { display: flex; align-items: center; padding: 4px 0; font-size: 0.85rem; }
.taxon-rank { color: var(--text-secondary); width: 100px; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; }
.taxon-val { color: var(--text-primary); font-style: italic; }

/* Top candidate rows */
.candidate-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    border-radius: 8px;
    background: #0d1527;
    margin: 4px 0;
    border: 1px solid var(--border);
}

/* Warning banner */
.warn-banner {
    background: linear-gradient(90deg, #2a1500, #1a0d00);
    border: 1px solid #ff7c44;
    border-radius: 10px;
    padding: 14px 20px;
    margin: 10px 0;
    color: #ff9955;
    font-size: 0.85rem;
}

.stTextArea textarea {
    background: #050810 !important;
    color: #4dbbff !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.75rem !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

div[data-testid="stExpander"] {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)


# ─── Initialize Engine ────────────────────────────────────────────────────────
@st.cache_resource
def load_engine():
    engine = DNAAnalysisEngine(REFERENCE_DATABASE)
    engine.fit()
    return engine


engine = load_engine()


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:10px 0 20px'>
        <div class='logo-text'>🧬 WILDGUARD</div>
        <div class='logo-sub'>DNA Forensics Platform v2.1</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### ⚙️ Project Settings")

    kmer_size = st.selectbox("K-mer Size", [3, 4, 5], index=1, help="Larger k-mers = more specific but slower")
    min_seq_len = st.slider("Min. Sequence Length (bp)", 100, 400, 200)
    max_seq_len = st.slider("Max. Sequence Length (bp)", 500, 800, 658, help="Standard COI barcode = 658 bp")
    show_all_candidates = st.checkbox("Show all top-10 candidates", value=False)
    strict_mode = st.checkbox("Strict Mode (raise thresholds)", value=False)

    st.markdown("---")
    st.markdown("#### 📊 Reference Database")
    st.markdown(f"""
    <div class='dna-card' style='padding:12px'>
        <div style='font-size:0.78rem; color:#8899bb; letter-spacing:1px; text-transform:uppercase'>Status</div>
        <div style='color:#00ff88; font-family:monospace; font-size:0.9rem; margin-top:4px'>● ONLINE</div>
        <div style='margin-top:10px; font-size:0.78rem; color:#8899bb'>Species Loaded</div>
        <div style='font-family:monospace; color:#e8edf5'>{len(REFERENCE_DATABASE)} taxa</div>
        <div style='margin-top:8px; font-size:0.78rem; color:#8899bb'>Source</div>
        <div style='font-size:0.8rem; color:#00b4ff'>BOLD + MIDORI2</div>
        <div style='margin-top:8px; font-size:0.78rem; color:#8899bb'>Gene Target</div>
        <div style='font-size:0.8rem'>COI (5' region)</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🏛️ Authority")
    st.markdown("""
    <div style='font-size:0.75rem; color:#8899bb; line-height:1.8'>
    🌍 CITES Convention (1973)<br>
    📋 IUCN Red List Categories<br>
    🔬 BOLD Systems v4<br>
    🗄️ MIDORI2 (GenBank curated)
    </div>
    """, unsafe_allow_html=True)


# ─── Main Dashboard ───────────────────────────────────────────────────────────
st.markdown("""
<div style='display:flex; align-items:center; gap:16px; margin-bottom:6px'>
    <div>
        <h1 style='margin:0; font-size:1.6rem; letter-spacing:2px'>WILDLIFE DNA FORENSICS</h1>
        <div style='color:#8899bb; font-size:0.8rem; letter-spacing:3px; text-transform:uppercase'>
            CITES Enforcement · Hamad International Airport · Real-time Species ID
        </div>
    </div>
</div>
<hr style='border:none; border-top:1px solid #1e2d4a; margin:12px 0 24px'>
""", unsafe_allow_html=True)

# ─── Input Section ────────────────────────────────────────────────────────────
col_input, col_info = st.columns([3, 2])

with col_input:
    st.markdown("### 📥 Sequence Input")
    input_mode = st.radio("Input Mode", ["Paste Raw/FASTA", "Upload .fasta File"], horizontal=True)

    raw_input = ""
    if input_mode == "Paste Raw/FASTA":
        raw_input = st.text_area(
            "DNA Sequence (COI gene)",
            height=160,
            placeholder=">Sample_ID\nATGGCAGTTAGACAAATAGCCATTCGCAACAATTGGCCATCCAGGAGCCTCAGTTGGAGATGATCAA...",
            help="Paste raw sequence or FASTA format. Non-ACGT characters will be stripped automatically."
        )
    else:
        uploaded = st.file_uploader("Upload FASTA File", type=["fasta", "fa", "txt"])
        if uploaded:
            raw_input = uploaded.read().decode("utf-8", errors="ignore")
            st.success(f"✓ File loaded: `{uploaded.name}` ({len(raw_input)} chars)")

    analyze_btn = st.button("🔬 ANALYZE SEQUENCE", use_container_width=True)

with col_info:
    st.markdown("### 🎯 Quick Reference")
    st.markdown("""
    <div class='dna-card'>
        <div style='font-size:0.78rem; color:#8899bb; text-transform:uppercase; letter-spacing:1px; margin-bottom:10px'>Confidence Thresholds</div>
        <div style='display:flex; align-items:center; gap:8px; margin:6px 0'>
            <div style='width:12px;height:12px;border-radius:50%;background:#00ff88'></div>
            <span style='font-size:0.82rem'><b>HIGH</b> — &gt;98% + E &lt; 10⁻¹⁰⁰</span>
        </div>
        <div style='display:flex; align-items:center; gap:8px; margin:6px 0'>
            <div style='width:12px;height:12px;border-radius:50%;background:#ffd700'></div>
            <span style='font-size:0.82rem'><b>AMBIGUOUS</b> — 95–97% or multi-hit</span>
        </div>
        <div style='display:flex; align-items:center; gap:8px; margin:6px 0'>
            <div style='width:12px;height:12px;border-radius:50%;background:#ff3b5c'></div>
            <span style='font-size:0.82rem'><b>LOW</b> — &lt;95% / Manual Review</span>
        </div>
        <hr class='hline'>
        <div style='font-size:0.78rem; color:#8899bb; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px'>CITES Appendices</div>
        <div style='font-size:0.8rem; line-height:1.9'>
            <span class='cites-I'>APP. I</span> Trade prohibited<br>
            <span class='cites-II'>APP. II</span> Permit required<br>
            <span class='cites-III'>APP. III</span> One-country control<br>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── Analysis Pipeline ────────────────────────────────────────────────────────
if analyze_btn or st.session_state.get("last_result"):

    if analyze_btn and raw_input.strip():
        with st.spinner("🧬 Sanitizing sequence..."):
            result = engine.analyze(raw_input, kmer_size=kmer_size, strict=strict_mode)
            st.session_state["last_result"] = result
            st.session_state["raw_input"] = raw_input

    result = st.session_state.get("last_result")
    raw_input_stored = st.session_state.get("raw_input", raw_input)

    if not result:
        st.warning("No sequence provided.")
        st.stop()

    if result["error"]:
        st.error(f"⚠️ {result['error']}")
        st.stop()

    # ── Sanitization Report ──
    with st.expander("🧹 Sanitization Report", expanded=False):
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("Input Length", f"{result['raw_len']} bp")
        sc2.metric("Cleaned Length", f"{result['clean_len']} bp")
        sc3.metric("Removed Chars", result['removed_chars'])
        sc4.metric("Header Stripped", "Yes" if result['had_header'] else "No")
        st.markdown(f"""<div class='seq-display'>{result['clean_seq'][:300]}{'...' if len(result['clean_seq'])>300 else ''}</div>""", unsafe_allow_html=True)

    st.markdown("<hr class='hline'>", unsafe_allow_html=True)

    # ── TIER 1: OFFICER VIEW ──────────────────────────────────────────────────
    st.markdown("## 👮 OFFICER VIEW")

    top = result["top_match"]
    confidence = result["confidence_level"]
    similarity = result["similarity"]
    meta = SPECIES_METADATA.get(top["species_id"], {})

    # Traffic Light
    tl_class = {"HIGH": "tl-green", "AMBIGUOUS": "tl-yellow", "LOW": "tl-red"}[confidence]
    tl_icon = {"HIGH": "🟢", "AMBIGUOUS": "🟡", "LOW": "🔴"}[confidence]
    tl_label = {
        "HIGH": "HIGH CONFIDENCE IDENTIFICATION",
        "AMBIGUOUS": "AMBIGUOUS — MULTIPLE CANDIDATES",
        "LOW": "IDENTIFICATION NOT POSSIBLE"
    }[confidence]
    tl_color = {"HIGH": "#00ff88", "AMBIGUOUS": "#ffd700", "LOW": "#ff3b5c"}[confidence]

    col_tl, col_species, col_action = st.columns([1.2, 1.8, 1.8])

    with col_tl:
        st.markdown(f"""
        <div class='{tl_class}'>
            <div style='font-size:3rem'>{tl_icon}</div>
            <div style='font-family:monospace; font-size:0.7rem; color:{tl_color}; letter-spacing:1.5px; margin-top:8px'>{tl_label}</div>
            <div style='font-size:2rem; font-weight:700; color:{tl_color}; font-family:monospace; margin-top:10px'>{similarity:.1f}%</div>
            <div style='font-size:0.7rem; color:#8899bb; margin-top:2px'>SIMILARITY SCORE</div>
            <div style='font-size:0.85rem; color:{tl_color}; font-family:monospace; margin-top:8px'>E = {result["evalue"]}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_species:
        if confidence != "LOW":
            iucn = meta.get("iucn", "DD")
            iucn_class = f"iucn-{iucn}" if iucn in ["CR","EN","VU","NT","LC"] else ""
            cites_app = meta.get("cites_appendix", "")
            cites_class = f"cites-{cites_app}" if cites_app else "cites-none"
            cites_label = f"CITES APP. {cites_app}" if cites_app else "NOT LISTED"

            st.markdown(f"""
            <div class='dna-card'>
                <div style='font-size:0.7rem; color:#8899bb; letter-spacing:2px; text-transform:uppercase'>Identified Species</div>
                <div style='font-size:1.4rem; font-style:italic; font-weight:600; color:#e8edf5; margin:6px 0'>{meta.get("scientific_name","—")}</div>
                <div style='font-size:0.9rem; color:#8899bb'>"{meta.get("common_name","—")}"</div>
                <hr class='hline'>
                <div style='display:flex; gap:8px; flex-wrap:wrap; margin:8px 0'>
                    <span class='{cites_class}'>{cites_label}</span>
                    <span class='{iucn_class}' style='font-size:0.85rem'>IUCN: {iucn}</span>
                </div>
                <div style='margin-top:10px; font-size:0.8rem; color:#8899bb'>🌍 Native Range</div>
                <div style='font-size:0.82rem; margin-top:3px'>{meta.get("native_range","Unknown")}</div>
                <div style='margin-top:8px; font-size:0.8rem; color:#8899bb'>🔬 Taxonomy</div>
                <div style='font-size:0.8rem; font-style:italic; margin-top:3px'>
                {meta.get("order","")} › {meta.get("family","")} › <b>{meta.get("genus","")}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Specimen image placeholder
            emoji = meta.get("emoji", "🐾")
            st.markdown(f"""
            <div style='background:#050810; border:1px dashed #1e2d4a; border-radius:10px; 
                        padding:20px; text-align:center; margin-top:8px'>
                <div style='font-size:3.5rem'>{emoji}</div>
                <div style='font-size:0.68rem; color:#445566; margin-top:6px; letter-spacing:1px'>
                REPRESENTATIVE IMAGE PLACEHOLDER<br>{meta.get("scientific_name","")}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='dna-card' style='border-color:#ff3b5c44'>
                <div style='color:#ff3b5c; font-size:1.1rem; font-weight:600'>⚠️ UNIDENTIFIABLE</div>
                <div style='color:#8899bb; margin-top:8px; font-size:0.85rem'>
                Sequence quality or divergence is too low for reliable species assignment.<br><br>
                <b>Action:</b> Refer to laboratory for Sanger sequencing confirmation.
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_action:
        st.markdown("#### 🚨 Legal Recommendation")

        if confidence == "HIGH":
            cites_app = meta.get("cites_appendix", "")
            if cites_app == "I":
                st.markdown("""
                <div class='action-arrest'>
                    <b style='color:#ff3b5c'>⛔ IMMEDIATE DETENTION REQUIRED</b><br>
                    <span style='font-size:0.82rem'>CITES Appendix I — Commercial trade <b>strictly prohibited</b>.
                    Detain shipment and notify CITES National Authority within 24 hours.
                    Seize specimen as evidence.</span>
                </div>
                """, unsafe_allow_html=True)
            elif cites_app == "II":
                st.markdown("""
                <div class='action-hold'>
                    <b style='color:#ffd700'>🔒 HOLD FOR DOCUMENTATION CHECK</b><br>
                    <span style='font-size:0.82rem'>CITES Appendix II — Valid export/import permit required.
                    Verify CITES permit authenticity. Contact exporting country authority if suspect.</span>
                </div>
                """, unsafe_allow_html=True)
            elif cites_app == "III":
                st.markdown("""
                <div class='action-review'>
                    <b style='color:#00b4ff'>📋 DOCUMENTATION REVIEW</b><br>
                    <span style='font-size:0.82rem'>CITES Appendix III — Certificate of origin required from 
                    listing country. Check CITES permit database.</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class='dna-card' style='border-color:#00ff8844'>
                    <b style='color:#00ff88'>✅ NOT CITES LISTED</b><br>
                    <span style='font-size:0.82rem'>Species not currently on CITES appendices. 
                    Check national legislation and verify IUCN status before release.</span>
                </div>
                """, unsafe_allow_html=True)

        elif confidence == "AMBIGUOUS":
            st.markdown("""
            <div class='warn-banner'>
                ⚠️ <b>HOLD SHIPMENT PENDING SPECIALIST REVIEW</b><br>
                Multiple species candidates identified. At least one candidate is CITES-listed.
                Do not release until specialist confirms identity.
            </div>
            """, unsafe_allow_html=True)
            st.markdown("**Top Candidates:**")
            for i, cand in enumerate(result["candidates"][:3]):
                m = SPECIES_METADATA.get(cand["species_id"], {})
                cites = m.get("cites_appendix","—")
                st.markdown(f"""
                <div class='candidate-row'>
                    <div>
                        <span style='color:#8899bb; font-size:0.75rem'>#{i+1}</span>
                        <span style='font-style:italic; margin-left:8px'>{m.get("scientific_name","?")}</span>
                    </div>
                    <div style='display:flex; gap:8px; align-items:center'>
                        <span style='font-family:monospace; color:#00b4ff'>{cand["similarity"]:.1f}%</span>
                        <span class='cites-{"I" if cites=="I" else ("II" if cites=="II" else "none")}'>
                            {"APP. "+cites if cites != "—" else "—"}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        else:
            st.markdown("""
            <div class='action-review'>
                <b style='color:#00b4ff'>🔬 REFER TO SPECIALIST LABORATORY</b><br>
                <span style='font-size:0.82rem'>Sequence below identification threshold.
                Send sample for validated Sanger sequencing. Do not release shipment pending confirmation.</span>
            </div>
            """, unsafe_allow_html=True)

        # Case ID
        case_id = f"WG-{datetime.now().strftime('%Y%m%d')}-{abs(hash(result['clean_seq']))%10000:04d}"
        st.markdown(f"""
        <div style='margin-top:16px; padding:10px; background:#050810; border-radius:8px; 
                    border:1px solid #1e2d4a; font-family:monospace; font-size:0.75rem'>
            🆔 Case ID: <b style='color:#00b4ff'>{case_id}</b><br>
            🕐 Timestamp: <span style='color:#8899bb'>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} AST</span><br>
            📍 Station: <span style='color:#8899bb'>HIA Terminal — Wildlife Screening Unit</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr class='hline'>", unsafe_allow_html=True)

    # ── TIER 2: SPECIALIST VIEW ───────────────────────────────────────────────
    with st.expander("🔬 SPECIALIST / TECHNICAL DETAILS", expanded=False):
        st.markdown("### Technical Analysis Details")

        t1, t2, t3 = st.columns(3)
        with t1:
            st.markdown(f"""
            <div class='metric-tile'>
                <div class='metric-value' style='color:#00b4ff'>{result['similarity']:.2f}%</div>
                <div class='metric-label'>Pairwise Similarity</div>
            </div>""", unsafe_allow_html=True)
        with t2:
            st.markdown(f"""
            <div class='metric-tile'>
                <div class='metric-value' style='color:#00ff88'>{result['evalue']}</div>
                <div class='metric-label'>E-Value</div>
            </div>""", unsafe_allow_html=True)
        with t3:
            st.markdown(f"""
            <div class='metric-tile'>
                <div class='metric-value' style='color:#ffd700'>{result['clean_len']}</div>
                <div class='metric-label'>Sequence Length (bp)</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("---")
        col_kmer, col_tax = st.columns([3, 2])

        with col_kmer:
            st.markdown("#### K-mer Distribution (Top 20)")
            kmer_df = pd.DataFrame(result["kmer_top20"], columns=["K-mer", "Count"])
            fig = px.bar(
                kmer_df, x="K-mer", y="Count",
                color="Count",
                color_continuous_scale=[[0, "#001a3a"], [0.5, "#00b4ff"], [1, "#00ff88"]],
                template="plotly_dark",
            )
            fig.update_layout(
                plot_bgcolor="#0a0e1a", paper_bgcolor="#0a0e1a",
                font_color="#e8edf5", margin=dict(l=20, r=20, t=20, b=40),
                coloraxis_showscale=False, height=300,
                xaxis=dict(tickfont=dict(size=9, family="Space Mono")),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_tax:
            st.markdown("#### Taxonomic Hierarchy")
            if confidence != "LOW" and meta:
                ranks = [
                    ("Kingdom", meta.get("kingdom", "Animalia")),
                    ("Phylum", meta.get("phylum", "—")),
                    ("Class", meta.get("class_", "—")),
                    ("Order", meta.get("order", "—")),
                    ("Family", meta.get("family", "—")),
                    ("Genus", meta.get("genus", "—")),
                    ("Species", meta.get("scientific_name", "—")),
                ]
                for rank, val in ranks:
                    depth = ["Kingdom","Phylum","Class","Order","Family","Genus","Species"].index(rank)
                    st.markdown(f"""
                    <div class='taxon-row' style='padding-left:{depth*8}px'>
                        <span class='taxon-rank'>{rank}</span>
                        <span class='taxon-val' style='{"font-size:0.95rem;color:#00ff88;font-weight:600" if rank=="Species" else ""}'>{val}</span>
                    </div>""", unsafe_allow_html=True)

        st.markdown("---")
        if not show_all_candidates:
            cand_show = result["candidates"][:5]
        else:
            cand_show = result["candidates"][:10]

        st.markdown(f"#### Top {len(cand_show)} Species Candidates")
        scores = [c["similarity"] for c in cand_show]
        labels = [SPECIES_METADATA.get(c["species_id"], {}).get("scientific_name", c["species_id"]) for c in cand_show]
        colors = ["#00ff88" if s >= 98 else "#ffd700" if s >= 95 else "#ff3b5c" for s in scores]

        fig2 = go.Figure(go.Bar(
            x=scores, y=labels, orientation="h",
            marker_color=colors,
            text=[f"{s:.1f}%" for s in scores],
            textposition="outside",
            textfont=dict(family="Space Mono", size=10, color="#e8edf5"),
        ))
        fig2.update_layout(
            plot_bgcolor="#0a0e1a", paper_bgcolor="#0a0e1a",
            font_color="#e8edf5", height=max(200, len(cand_show) * 45),
            margin=dict(l=10, r=60, t=10, b=10),
            xaxis=dict(range=[min(scores)-5, 103], title="Similarity %", tickfont=dict(family="Space Mono", size=9)),
            yaxis=dict(tickfont=dict(family="Space Mono", size=9, color="#8899bb")),
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown("#### Raw Alignment Statistics")
        align_df = pd.DataFrame({
            "Metric": ["Query Length", "Ref Length", "Aligned Positions", "Identities", "Gaps", "GC Content", "K-mer Size"],
            "Value": [
                f"{result['clean_len']} bp",
                f"{result['ref_len']} bp",
                f"{result['aligned_positions']} bp",
                f"{result['identities']} ({result['similarity']:.1f}%)",
                f"{result['gaps']}",
                f"{result['gc_content']:.1f}%",
                f"{kmer_size}-mer"
            ]
        })
        st.dataframe(align_df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("#### 📄 Download Forensic Report")

        pdf_bytes = generate_pdf_report(result, meta, case_id, kmer_size)
        st.download_button(
            label="⬇️  DOWNLOAD FORENSIC PDF REPORT",
            data=pdf_bytes,
            file_name=f"WildGuard_Report_{case_id}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    # ── Database Browser ──────────────────────────────────────────────────────
    st.markdown("<hr class='hline'>", unsafe_allow_html=True)
    with st.expander("🗂️ REFERENCE DATABASE BROWSER", expanded=False):
        st.markdown("### 20 High-Priority Forensic Species")
        rows = []
        for sid, m in SPECIES_METADATA.items():
            rows.append({
                "Scientific Name": m.get("scientific_name", ""),
                "Common Name": m.get("common_name", ""),
                "Order": m.get("order", ""),
                "IUCN": m.get("iucn", ""),
                "CITES": m.get("cites_appendix", "—"),
                "Native Range": m.get("native_range", ""),
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True, height=400)


elif not analyze_btn:
    # Landing state
    st.markdown("""
    <div style='text-align:center; padding:60px 20px; opacity:0.7'>
        <div style='font-size:4rem; margin-bottom:16px'>🧬</div>
        <div style='font-family:monospace; font-size:1.1rem; color:#8899bb; letter-spacing:2px'>
            READY FOR SEQUENCE INPUT
        </div>
        <div style='font-size:0.8rem; color:#445566; margin-top:8px'>
            Paste a COI DNA sequence or upload a .fasta file to begin forensic analysis
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Show species grid
    st.markdown("### 🌍 Monitored Species (Priority Forensic Taxa)")
    cols = st.columns(5)
    species_list = list(SPECIES_METADATA.values())
    for i, s in enumerate(species_list):
        with cols[i % 5]:
            cites = s.get("cites_appendix","")
            iucn = s.get("iucn","")
            badge_color = "#ff3b5c" if cites=="I" else "#ffd700" if cites=="II" else "#00b4ff"
            st.markdown(f"""
            <div class='dna-card' style='padding:12px; text-align:center; min-height:130px'>
                <div style='font-size:2rem'>{s.get("emoji","🐾")}</div>
                <div style='font-size:0.72rem; font-style:italic; color:#e8edf5; margin:4px 0; line-height:1.3'>{s.get("scientific_name","")}</div>
                <div style='font-size:0.65rem; color:#8899bb'>{s.get("common_name","")}</div>
                <div style='margin-top:6px'>
                    <span style='font-size:0.62rem; background:{badge_color}22; border:1px solid {badge_color}; 
                                 color:{badge_color}; border-radius:4px; padding:2px 6px; font-family:monospace'>
                        {"APP."+cites if cites else "—"} · {iucn}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
