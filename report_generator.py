"""
Forensic PDF Report Generator
Generates professional CITES enforcement reports for wildlife DNA cases
"""

from io import BytesIO
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False


def generate_pdf_report(result: dict, meta: dict, case_id: str, kmer_size: int) -> bytes:
    """Generate a professional forensic PDF report."""

    if not REPORTLAB_OK:
        # Fallback: plain text PDF-like content
        buf = BytesIO()
        buf.write(b"Reportlab not available. Install with: pip install reportlab")
        return buf.getvalue()

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
        title=f"WildGuard Forensic Report {case_id}"
    )

    # ─── Styles ───────────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()
    dark_bg = colors.HexColor("#0a0e1a")
    accent = colors.HexColor("#00b4ff")
    green = colors.HexColor("#00cc66")
    yellow = colors.HexColor("#ffcc00")
    red = colors.HexColor("#ff3b5c")
    light_text = colors.HexColor("#e8edf5")
    muted = colors.HexColor("#8899bb")
    border_col = colors.HexColor("#1e2d4a")
    card_bg = colors.HexColor("#141c2e")

    conf_color = {"HIGH": green, "AMBIGUOUS": yellow, "LOW": red}.get(
        result.get("confidence_level", "LOW"), red
    )

    title_style = ParagraphStyle("title", parent=styles["Title"],
        fontName="Helvetica-Bold", fontSize=18, textColor=accent,
        spaceAfter=4, alignment=TA_CENTER)
    sub_style = ParagraphStyle("sub", parent=styles["Normal"],
        fontName="Helvetica", fontSize=8, textColor=muted,
        spaceAfter=12, alignment=TA_CENTER)
    heading_style = ParagraphStyle("heading", parent=styles["Heading2"],
        fontName="Helvetica-Bold", fontSize=11, textColor=accent,
        spaceBefore=12, spaceAfter=4)
    body_style = ParagraphStyle("body", parent=styles["Normal"],
        fontName="Helvetica", fontSize=9, textColor=light_text,
        spaceAfter=4, leading=14)
    label_style = ParagraphStyle("label", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=8, textColor=muted,
        spaceAfter=2)
    mono_style = ParagraphStyle("mono", parent=styles["Code"],
        fontName="Courier", fontSize=7.5, textColor=accent,
        backColor=dark_bg, borderPadding=6, spaceAfter=6,
        leading=12, wordWrap="CJK")

    story = []

    # ─── Header Banner ────────────────────────────────────────────────────────
    header_data = [[
        Paragraph("🧬 WILDGUARD DNA FORENSICS PLATFORM", title_style),
    ]]
    header_tbl = Table(header_data, colWidths=[170*mm])
    header_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), dark_bg),
        ("TOPPADDING", (0,0), (-1,-1), 12),
        ("BOTTOMPADDING", (0,0), (-1,-1), 12),
        ("BOX", (0,0), (-1,-1), 1, accent),
        ("ROUNDEDCORNERS", [6,6,6,6]),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("CITES ENFORCEMENT — OFFICIAL FORENSIC CASE RECORD", sub_style))

    # ─── Case Info ────────────────────────────────────────────────────────────
    now = datetime.now()
    case_data = [
        ["Case ID", case_id, "Date", now.strftime("%Y-%m-%d")],
        ["Station", "HIA Wildlife Screening Unit", "Time", now.strftime("%H:%M:%S AST")],
        ["Analyst", "Automated System (WildGuard v2.1)", "K-mer Size", f"{kmer_size}-mer"],
    ]
    case_tbl = Table(case_data, colWidths=[35*mm, 65*mm, 25*mm, 45*mm])
    case_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), card_bg),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("TEXTCOLOR", (0,0), (0,-1), muted),
        ("TEXTCOLOR", (2,0), (2,-1), muted),
        ("TEXTCOLOR", (1,0), (1,-1), light_text),
        ("TEXTCOLOR", (3,0), (3,-1), light_text),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME", (2,0), (2,-1), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), 0.5, border_col),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [card_bg, dark_bg]),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(case_tbl)
    story.append(Spacer(1, 6*mm))

    # ─── Confidence Result ────────────────────────────────────────────────────
    story.append(Paragraph("IDENTIFICATION RESULT", heading_style))

    conf_level = result.get("confidence_level", "LOW")
    conf_label = {
        "HIGH": "HIGH CONFIDENCE IDENTIFICATION",
        "AMBIGUOUS": "AMBIGUOUS — MULTIPLE CANDIDATES DETECTED",
        "LOW": "IDENTIFICATION NOT POSSIBLE — MANUAL REVIEW REQUIRED"
    }[conf_level]

    result_data = [
        [Paragraph(f"<b>{conf_label}</b>",
                   ParagraphStyle("cl", parent=body_style, textColor=conf_color, fontSize=11))],
    ]
    result_tbl = Table(result_data, colWidths=[170*mm])
    result_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), card_bg),
        ("BOX", (0,0), (-1,-1), 2, conf_color),
        ("TOPPADDING", (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("LEFTPADDING", (0,0), (-1,-1), 12),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
    ]))
    story.append(result_tbl)
    story.append(Spacer(1, 4*mm))

    # ─── Species Info ─────────────────────────────────────────────────────────
    if conf_level != "LOW" and meta:
        story.append(Paragraph("SPECIES IDENTIFICATION", heading_style))

        cites_app = meta.get("cites_appendix", "")
        cites_label = f"CITES Appendix {cites_app}" if cites_app else "Not CITES Listed"
        iucn = meta.get("iucn", "DD")

        species_data = [
            ["Scientific Name", meta.get("scientific_name", "—"), "CITES Status", cites_label],
            ["Common Name", meta.get("common_name", "—"), "IUCN Status", iucn],
            ["Order", meta.get("order", "—"), "Family", meta.get("family", "—")],
            ["Native Range", meta.get("native_range", "—"), "Trafficking Note", meta.get("trafficking_note", "—")],
        ]
        sp_tbl = Table(species_data, colWidths=[35*mm, 65*mm, 30*mm, 40*mm])
        sp_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), card_bg),
            ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
            ("FONTSIZE", (0,0), (-1,-1), 8),
            ("TEXTCOLOR", (0,0), (-1,-1), light_text),
            ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
            ("FONTNAME", (2,0), (2,-1), "Helvetica-Bold"),
            ("TEXTCOLOR", (0,0), (0,-1), muted),
            ("TEXTCOLOR", (2,0), (2,-1), muted),
            ("GRID", (0,0), (-1,-1), 0.5, border_col),
            ("ROWBACKGROUNDS", (0,0), (-1,-1), [card_bg, dark_bg]),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
        ]))
        story.append(sp_tbl)
        story.append(Spacer(1, 4*mm))

    # ─── Metrics ─────────────────────────────────────────────────────────────
    story.append(Paragraph("MOLECULAR ANALYSIS METRICS", heading_style))
    metrics_data = [
        ["Metric", "Value", "Metric", "Value"],
        ["Similarity Score", f"{result.get('similarity', 0):.2f}%",
         "E-Value", result.get("evalue", "—")],
        ["Query Length", f"{result.get('clean_len', 0)} bp",
         "Reference Length", f"{result.get('ref_len', 0)} bp"],
        ["Aligned Positions", f"{result.get('aligned_positions', 0)} bp",
         "GC Content", f"{result.get('gc_content', 0):.1f}%"],
        ["Identities", f"{result.get('identities', 0)} nt",
         "Gaps", f"{result.get('gaps', 0)} nt"],
    ]
    met_tbl = Table(metrics_data, colWidths=[45*mm, 40*mm, 45*mm, 40*mm])
    met_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), dark_bg),
        ("TEXTCOLOR", (0,0), (-1,0), accent),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8.5),
        ("FONTNAME", (0,1), (0,-1), "Helvetica-Bold"),
        ("FONTNAME", (2,1), (2,-1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0,1), (0,-1), muted),
        ("TEXTCOLOR", (2,1), (2,-1), muted),
        ("TEXTCOLOR", (1,1), (1,-1), light_text),
        ("TEXTCOLOR", (3,1), (3,-1), light_text),
        ("BACKGROUND", (0,1), (-1,-1), card_bg),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [card_bg, dark_bg]),
        ("GRID", (0,0), (-1,-1), 0.5, border_col),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(met_tbl)
    story.append(Spacer(1, 4*mm))

    # ─── Top Candidates ────────────────────────────────────────────────────────
    story.append(Paragraph("TOP SPECIES CANDIDATES", heading_style))
    cand_data = [["Rank", "Species", "Similarity (%)", "Status"]]
    for i, c in enumerate(result.get("candidates", [])[:5]):
        from reference_db import SPECIES_METADATA
        m = SPECIES_METADATA.get(c["species_id"], {})
        cites = m.get("cites_appendix", "—")
        cand_data.append([
            str(i+1),
            m.get("scientific_name", c["species_id"]),
            f"{c['similarity']:.2f}",
            f"CITES App. {cites}" if cites != "—" else "Not Listed"
        ])
    cand_tbl = Table(cand_data, colWidths=[15*mm, 70*mm, 40*mm, 45*mm])
    cand_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), dark_bg),
        ("TEXTCOLOR", (0,0), (-1,0), accent),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8.5),
        ("BACKGROUND", (0,1), (-1,-1), card_bg),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [card_bg, dark_bg]),
        ("TEXTCOLOR", (0,1), (-1,-1), light_text),
        ("GRID", (0,0), (-1,-1), 0.5, border_col),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("FONTNAME", (1,1), (1,-1), "Helvetica-Oblique"),
    ]))
    story.append(cand_tbl)
    story.append(Spacer(1, 4*mm))

    # ─── Query Sequence ───────────────────────────────────────────────────────
    story.append(Paragraph("QUERY SEQUENCE (first 300 bp)", heading_style))
    seq_text = result.get("clean_seq", "")[:300]
    if seq_text:
        # Format in lines of 60
        lines = [seq_text[i:i+60] for i in range(0, len(seq_text), 60)]
        story.append(Paragraph("<br/>".join(lines), mono_style))

    # ─── Legal Notice ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=border_col))
    story.append(Spacer(1, 3*mm))
    notice_style = ParagraphStyle("notice", parent=styles["Normal"],
        fontName="Helvetica", fontSize=7, textColor=muted,
        spaceAfter=4, leading=11)
    story.append(Paragraph(
        "<b>LEGAL NOTICE:</b> This report is generated by the WildGuard DNA Forensics Platform "
        "for use by authorized customs and wildlife enforcement officers. Results are based on "
        "k-mer similarity analysis against a curated COI reference database (BOLD Systems / MIDORI2). "
        "Identification results with HIGH confidence (>98% similarity) are suitable for field "
        "enforcement action subject to officer judgment. AMBIGUOUS results require specialist review "
        "before enforcement action. This document may be used as supporting evidence in accordance "
        "with CITES (Convention on International Trade in Endangered Species of Wild Fauna and Flora) "
        "regulations and applicable national legislation.",
        notice_style
    ))
    story.append(Paragraph(
        f"Generated: {now.strftime('%Y-%m-%d %H:%M:%S')} AST  ·  Case: {case_id}  ·  "
        f"WildGuard v2.1  ·  CONFIDENTIAL — LAW ENFORCEMENT USE ONLY",
        ParagraphStyle("footer", parent=notice_style, alignment=TA_CENTER, textColor=muted)
    ))

    doc.build(story)
    return buf.getvalue()
