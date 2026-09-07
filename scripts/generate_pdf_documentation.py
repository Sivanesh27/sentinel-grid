"""
High-quality PDF Documentation Generator for Sentinel Grid using ReportLab.
Produces a formatted PDF document covering complete technical and non-technical specifications.
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

PDF_OUTPUT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../Sentinel_Grid_Documentation.pdf"))


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 11 * 72 - 36, "SENTINEL GRID // PS-26187 TECHNICAL & SYSTEM DOCUMENTATION")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 11 * 72 - 42, 8.5 * 72 - 54, 11 * 72 - 42)

        # Footer
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * 72 - 54, 36, footer_text)
        self.drawString(54, 36, "CONFIDENTIAL & PROPRIETARY — SMART INDIA HACKATHON 2026")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 46, 8.5 * 72 - 54, 46)
        self.restoreState()


def build_pdf():
    doc = SimpleDocTemplate(
        PDF_OUTPUT_PATH,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0284c7"),
        spaceAfter=14
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#0369a1"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6
    )

    body_bold = ParagraphStyle(
        'Body_Bold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=body_style,
        fontName='Courier-Bold',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#090f1d")
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#1e293b")
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=table_cell_style,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor("#0f172a")
    )

    story = []

    # ==================== COVER / HEADER ====================
    story.append(Paragraph("SENTINEL GRID", title_style))
    story.append(Paragraph("Autonomous AI Video Analytics & Threat Fusion Platform for Border CCTV Surveillance", subtitle_style))
    story.append(Paragraph("<b>Smart India Hackathon 2026</b> &nbsp;|&nbsp; Problem Statement: <b>PS-26187</b> &nbsp;|&nbsp; Version: <b>1.0 Production Prototype</b>", body_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceBefore=6, spaceAfter=14))

    # ==================== SECTION 1: NON-TECHNICAL DOCUMENTATION ====================
    story.append(Paragraph("1. Executive & Non-Technical Documentation", h1_style))

    story.append(Paragraph("1.1 Problem Statement & Background", h2_style))
    story.append(Paragraph(
        "Securing hundreds of kilometers of national border sectors and tactical perimeters presents critical operational challenges. "
        "Human operators monitoring dozens of CCTV and thermal screens suffer a <b>90% drop in vigilance after 20–30 minutes</b>. "
        "Simultaneously, conventional motion-sensor algorithms generate hundreds of false alarms per day from swaying trees, shadows, wind, and wildlife. "
        "Crucially, legacy systems lack <b>directional intelligence</b> (distinguishing an intruder entering a zone vs. someone turning back) "
        "and produce arbitrary black-box risk scores without natural language explanations.",
        body_style
    ))

    story.append(Paragraph("1.2 The Sentinel Grid Solution", h2_style))
    story.append(Paragraph(
        "<b>Sentinel Grid</b> transforms standard CCTV, thermal, and PTZ cameras into an autonomous tactical perimeter defense matrix. "
        "The system continuously scans live streams, tracks moving persons and vehicles, evaluates virtual fence perimeters, "
        "reads vehicle license plates, and calculates an <b>explainable, trust-weighted threat assessment score (0–100)</b> with natural language narratives.",
        body_style
    ))

    # Capabilities Table
    story.append(Paragraph("1.3 Core Capabilities & Operational Value", h2_style))
    cap_data = [
        [Paragraph("Feature / Capability", table_header_style), Paragraph("What It Does", table_header_style), Paragraph("Operational Impact", table_header_style)],
        [
            Paragraph("Multi-Target Tracking", table_cell_bold),
            Paragraph("YOLOv8 + ByteTrack persistent tracking for persons, cars, trucks, motorcycles.", table_cell_style),
            Paragraph("Retains target ID identity across temporary visual occlusions.", table_cell_style)
        ],
        [
            Paragraph("Directional Fence Breach", table_cell_bold),
            Paragraph("Distinguishes between Inbound Intrusions (85-100% Critical Alert) and Outbound Retreats (15-25% Silent Audit).", table_cell_style),
            Paragraph("Eliminates false alarms from friendly patrols and retreating individuals.", table_cell_style)
        ],
        [
            Paragraph("Drag-and-Drop Perimeter Calibration", table_cell_bold),
            Paragraph("Operators drag and reshape virtual polygon corners directly on live dashboard video tiles.", table_cell_style),
            Paragraph("Zero code needed; tactical officers align perimeters in seconds.", table_cell_style)
        ],
        [
            Paragraph("Edge ANPR Plate Reader", table_cell_bold),
            Paragraph("Automated crop, bilateral filtering, and EasyOCR alphanumeric character recognition.", table_cell_style),
            Paragraph("Audits authorized vs. unauthorized vehicular ingress.", table_cell_style)
        ],
        [
            Paragraph("Explainable Risk Engine", table_cell_bold),
            Paragraph("Transparent mathematical formulation combining breach, dwell time, group size, and night multipliers.", table_cell_style),
            Paragraph("Provides plain-English explanations for rapid military/police dispatch.", table_cell_style)
        ],
        [
            Paragraph("Night-Vision CLAHE Enhancer", table_cell_bold),
            Paragraph("Adaptive local contrast equalization on the CIE LAB Lightness channel.", table_cell_style),
            Paragraph("Enhances low-light and infrared camera footage dynamically.", table_cell_style)
        ]
    ]

    cap_table = Table(cap_data, colWidths=[1.4 * inch, 2.7 * inch, 2.7 * inch])
    cap_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(cap_table)
    story.append(Spacer(1, 10))

    # ==================== SECTION 2: TECHNICAL DOCUMENTATION ====================
    story.append(PageBreak())
    story.append(Paragraph("2. Complete Technical Specifications", h1_style))

    story.append(Paragraph("2.1 System Architecture & Data Flow", h2_style))
    story.append(Paragraph(
        "Sentinel Grid operates as a 6-tier pipeline: "
        "<b>1. Ingestion Layer</b> (Simulated RTSP / Video Source with automatic 640x480 normalization) &rarr; "
        "<b>2. Perception Layer</b> (CLAHE Contrast Enhancer + YOLOv8 Nano Perception) &rarr; "
        "<b>3. Tracking Layer</b> (ByteTrack Multi-Object Tracker with bottom-center ground coordinates) &rarr; "
        "<b>4. Spatial & Semantic Analytics</b> (Shapely Polygon Point-in-Polygon + EasyOCR ANPR) &rarr; "
        "<b>5. Trust-Weighted Fusion Engine</b> (Composite Scorer + Natural Language Narrative Generator) &rarr; "
        "<b>6. Persistence & Real-time Distribution</b> (SQLite Database + FastAPI WebSockets to React Dashboard).",
        body_style
    ))

    story.append(Paragraph("2.2 Mathematical Formulation of Risk Scoring", h2_style))
    story.append(Paragraph(
        "The composite risk score <b>R &isin; [0, 100]</b> for any tracked identity is defined as:",
        body_style
    ))

    # Math Box
    formula_text = (
        "<b>R = min(100, max(0, S_base &times; M_night + S_vehicle))</b><br/><br/>"
        "Where:<br/>"
        "&bull; <b>S_base = W_breach + W_dwell + W_group + P_confidence</b><br/>"
        "&bull; <b>W_breach</b> = 85.0 (Inbound Intrusion) | 20.0 (Outbound Safe Retreat) | 0.0 (No Breach)<br/>"
        "&bull; <b>W_dwell</b> = min(20.0, (t_zone_dwell / 5.0) &times; 5.0)  [Increments every 5s]<br/>"
        "&bull; <b>W_group</b> = (N_nearby - 1) &times; 8.0  [Proximity radius: 120px]<br/>"
        "&bull; <b>P_confidence</b> = -10.0 if YOLO confidence &lt; 0.45, else 0.0<br/>"
        "&bull; <b>M_night</b> = 1.25 if night-mode active and target in breach state, else 1.00<br/>"
        "&bull; <b>S_vehicle</b> = +5.0 if ANPR license plate registered"
    )
    formula_table = Table([[Paragraph(formula_text, callout_style)]], colWidths=[6.8 * inch])
    formula_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#0284c7")),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(formula_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("2.3 Directional Crossing Logic: Inbound vs. Outbound", h2_style))
    story.append(Paragraph(
        "Using Shapely geometry point containment and vector analysis &Delta;v = (x_t - x_{t-1}, y_t - y_{t-1}):",
        body_style
    ))
    story.append(Paragraph(
        "&bull; <b>Case A: Inbound Intrusion (Safe &rarr; Restricted)</b>: Triggers <b>CRITICAL ALARM (85–100% Risk)</b>, "
        "pulsing red bounding box, and instant WebSocket dispatch of base64 JPEG snapshot.<br/>"
        "&bull; <b>Case B: Outbound Retreat (Restricted &rarr; Safe)</b>: De-escalates threat to <b>LOW (15–25% Risk)</b>. "
        "Does NOT sound emergency sirens; silently logs crossing timestamps to SQLite tables <i>breach_events</i> and <i>tracks</i> for audit.",
        bullet_style
    ))

    # Database Table
    story.append(Paragraph("2.4 SQLite Database Schema", h2_style))
    db_data = [
        [Paragraph("Table Name", table_header_style), Paragraph("Primary Columns & Types", table_header_style), Paragraph("Purpose / Retention", table_header_style)],
        [
            Paragraph("tracks", table_cell_bold),
            Paragraph("track_id (INT), camera_id (TEXT), class_name (TEXT), confidence (FLOAT), total_dwell_time (FLOAT), max_risk_score (FLOAT), plate_number (TEXT)", table_cell_style),
            Paragraph("Persistent track registry and behavioral statistics.", table_cell_style)
        ],
        [
            Paragraph("breach_events", table_cell_bold),
            Paragraph("camera_id (TEXT), track_id (INT), fence_name (TEXT), direction ('inbound'/'outbound'), timestamp (DATETIME), position_x, position_y", table_cell_style),
            Paragraph("Audit trail of all physical and virtual boundary transitions.", table_cell_style)
        ],
        [
            Paragraph("alerts", table_cell_bold),
            Paragraph("alert_id (UUID), camera_id (TEXT), risk_score (FLOAT), severity ('CRITICAL'/'HIGH'), explanation (TEXT), snapshot_base64 (TEXT), acknowledged (BOOL)", table_cell_style),
            Paragraph("Historical security alerts with evidence snapshots.", table_cell_style)
        ]
    ]
    db_table = Table(db_data, colWidths=[1.2 * inch, 3.2 * inch, 2.4 * inch])
    db_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(db_table)
    story.append(Spacer(1, 10))

    # ==================== SECTION 3: DEPLOYMENT & COMPARISON ====================
    story.append(PageBreak())
    story.append(Paragraph("3. Deployment & Operational Matrix", h1_style))

    story.append(Paragraph("3.1 Prototype vs. Full Production Comparison", h2_style))
    prod_data = [
        [Paragraph("Pillar", table_header_style), Paragraph("Prototype (Hackathon MVP)", table_header_style), Paragraph("Production Tactical Deployment", table_header_style)],
        [
            Paragraph("Ingestion Protocol", table_cell_bold),
            Paragraph("Looped .mp4 video files / Synthetic generator", table_cell_style),
            Paragraph("Hardened RTSP / ONVIF Profile S/T/G over fiber / tactical radio mesh", table_cell_style)
        ],
        [
            Paragraph("Sensors", table_cell_bold),
            Paragraph("RGB Optical + Simulated Night Vision", table_cell_style),
            Paragraph("Long-Range Cooled Mid-Wave Infrared (MWIR) FLIR + Low-Light Starvis", table_cell_style)
        ],
        [
            Paragraph("Compute Edge", table_cell_bold),
            Paragraph("Multi-threaded CPU / Standard Docker", table_cell_style),
            Paragraph("NVIDIA Jetson AGX Orin Industrial (275 TOPS, MIL-STD-810G ruggedized)", table_cell_style)
        ],
        [
            Paragraph("Acceleration", table_cell_bold),
            Paragraph("PyTorch CPU Inference (torch.inference_mode)", table_cell_style),
            Paragraph("TensorRT FP16 / INT8 quantized execution (>120 FPS per core)", table_cell_style)
        ],
        [
            Paragraph("Persistence", table_cell_bold),
            Paragraph("SQLite local file storage (sentinel.db)", table_cell_style),
            Paragraph("Distributed PostgreSQL / TimescaleDB cluster + MinIO S3 object storage", table_cell_style)
        ],
        [
            Paragraph("Networking", table_cell_bold),
            Paragraph("Local WebSockets & REST API", table_cell_style),
            Paragraph("Secure WebSockets (WSS), MQTT broker, and MIL-STD-188 tactical mesh", table_cell_style)
        ]
    ]
    prod_table = Table(prod_data, colWidths=[1.3 * inch, 2.6 * inch, 2.9 * inch])
    prod_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(prod_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("3.2 Quick Launch Commands", h2_style))
    code_box_text = (
        "# Option A: Single-Command Docker Deployment<br/>"
        "<b>docker compose up --build</b><br/><br/>"
        "# Option B: Local Native Launch<br/>"
        "# 1. Backend Service (FastAPI + YOLOv8 + ByteTrack):<br/>"
        "cd \"backend\" &amp;&amp; .\\venv\\Scripts\\activate<br/>"
        "<b>uvicorn app.main:app --host 0.0.0.0 --port 8000</b><br/><br/>"
        "# 2. Frontend Command Center (React 18 + Vite):<br/>"
        "cd \"frontend\" &amp;&amp; <b>npm run dev</b><br/><br/>"
        "# URLs: Dashboard -> <u>http://localhost:3000</u> | API Docs -> <u>http://localhost:8000/docs</u>"
    )
    code_table = Table([[Paragraph(code_box_text, callout_style)]], colWidths=[6.8 * inch])
    code_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#090f1d")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#334155")),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    # Adjust text color for dark code box
    code_callout_style = ParagraphStyle(
        'DarkCallout',
        parent=callout_style,
        textColor=colors.HexColor("#38bdf8")
    )
    code_table = Table([[Paragraph(code_box_text, code_callout_style)]], colWidths=[6.8 * inch])
    code_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#090f1d")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#00f0ff")),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(code_table)

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF documentation at: {PDF_OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()
