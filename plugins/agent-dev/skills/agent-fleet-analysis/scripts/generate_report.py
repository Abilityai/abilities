#!/usr/bin/env python3
"""
Agent Fleet Analysis — PDF Report Generator
ability.ai light-mode design: #F4F4F5 page · white cards · #DC2828 red accent.

Usage:
    python3 generate_report.py --data fleet_data.json --output /path/to/report.pdf
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from reportlab.lib.colors import HexColor, black, white, Color
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm, mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether, PageBreak,
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError:
    print("ERROR: ReportLab not installed. Run: pip install reportlab", file=sys.stderr)
    sys.exit(1)

# ── Try to register DM Sans (falls back to Helvetica silently) ────────────────
FONT_NORMAL = 'Helvetica'
FONT_BOLD   = 'Helvetica-Bold'
FONT_MONO   = 'Courier'

# ── ability.ai palette ────────────────────────────────────────────────────────
PAGE_BG    = HexColor('#F4F4F5')   # site --bg-page
CARD_BG    = HexColor('#FFFFFF')   # site --bg-card
CARD_ALT   = HexColor('#F5F4F4')   # site --ab-card-alt
INK        = HexColor('#1D1D1F')   # site --text-primary
FOIL       = HexColor('#565659')   # site --text-muted
CHROME     = HexColor('#676A75')   # site --ab-chrome
HAIRLINE   = HexColor('#D4D4D8')   # site --border-subtle / --ab-hairline
RED        = HexColor('#DC2828')   # site --accent-glow-red (THE brand accent)
RED_MUTED  = HexColor('#B85050')   # site --ab-red
RED_TINT   = HexColor('#FEF2F2')   # red/0.08 approximation for tint cells
GREEN_AB   = HexColor('#2F9E6B')   # site --ab-strong
AMBER_AB   = HexColor('#E8855A')   # site --ab-amber
BLUE_AB    = HexColor('#5C6B8C')   # site --ab-blue
SCORE_BAD  = HexColor('#DC2828')   # early stage
SCORE_WARN = HexColor('#E8855A')   # needs improvement / functional
SCORE_OK   = HexColor('#2F9E6B')   # well-designed

# ── Page geometry ─────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
ML = MR = 1.8 * cm
MT = 2.0 * cm
MB = 2.2 * cm
CW = PAGE_W - ML - MR


# ── Style helpers ─────────────────────────────────────────────────────────────
def ps(name, **kw):
    defaults = dict(fontName=FONT_NORMAL, fontSize=9, textColor=FOIL,
                    leading=13, spaceAfter=0)
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)


STYLES = {
    'body':    ps('body', textColor=FOIL, leading=13),
    'bullet':  ps('bullet', textColor=FOIL, leftIndent=10, spaceAfter=3, leading=13),
    'caption': ps('caption', fontSize=7.5, textColor=CHROME, spaceAfter=2),
    'mono':    ps('mono', fontName=FONT_MONO, fontSize=7.5, leading=10,
                  textColor=FOIL),
    'th':      ps('th', fontName=FONT_BOLD, fontSize=8, textColor=FOIL, leading=11),
    'td':      ps('td', fontSize=8, textColor=FOIL, leading=11),
    'td_bold': ps('td_bold', fontName=FONT_BOLD, fontSize=8.5,
                  textColor=INK, leading=11),
    'phase_h': ps('phase_h', fontName=FONT_BOLD, fontSize=9,
                  textColor=INK, spaceAfter=4, leading=12),
    'phase_i': ps('phase_i', fontSize=8, textColor=FOIL, leading=11, leftIndent=8),
}


# ── Score helpers ─────────────────────────────────────────────────────────────
def score_color(score):
    if score >= 80:
        return SCORE_OK
    if score >= 60:
        return AMBER_AB
    if score >= 40:
        return SCORE_WARN
    return SCORE_BAD


def score_label(score):
    if score >= 80:
        return 'Well-designed'
    if score >= 60:
        return 'Functional'
    if score >= 40:
        return 'Needs improvement'
    return 'Early stage'


# ── Section heading — red left accent + bold title ────────────────────────────
def section_head(title):
    h = ps('sh', fontName=FONT_BOLD, fontSize=11, textColor=INK,
           leading=14, spaceBefore=0, spaceAfter=0)
    data = [['', Paragraph(title, h)]]
    t = Table(data, colWidths=[4, CW - 4])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (0, -1), RED),
        ('BACKGROUND',    (1, 0), (1, -1), CARD_BG),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING',   (1, 0), (1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX',           (0, 0), (-1, -1), 0.5, HAIRLINE),
    ]))
    return t


# ── Card wrapper — white card with hairline border ────────────────────────────
def card(content_elems, padding=10):
    """Wrap a list of elements inside a white card."""
    t = Table([[content_elems]], colWidths=[CW])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), CARD_BG),
        ('BOX',           (0, 0), (-1, -1), 0.5, HAIRLINE),
        ('TOPPADDING',    (0, 0), (-1, -1), padding),
        ('BOTTOMPADDING', (0, 0), (-1, -1), padding),
        ('LEFTPADDING',   (0, 0), (-1, -1), padding),
        ('RIGHTPADDING',  (0, 0), (-1, -1), padding),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))
    return t


# ── Page background + footer ──────────────────────────────────────────────────
def draw_page(canvas, doc):
    canvas.saveState()

    # Page background
    canvas.setFillColor(PAGE_BG)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Footer separator
    y_line = MB - 2 * mm
    y_text = MB - 5.5 * mm
    canvas.setStrokeColor(HAIRLINE)
    canvas.setLineWidth(0.5)
    canvas.line(ML, y_line, PAGE_W - MR, y_line)

    canvas.setFont(FONT_NORMAL, 7)
    canvas.setFillColor(CHROME)
    canvas.drawString(ML, y_text, 'Agent Fleet Analysis  ·  ability.ai')
    canvas.drawRightString(PAGE_W - MR, y_text, f'Page {canvas.getPageNumber()}')

    canvas.restoreState()


# ── Header block ──────────────────────────────────────────────────────────────
def header_block(data):
    n_agents  = len(data.get('agents', []))
    generated = data.get('generated_at', 'Today')
    scan_path = data.get('scan_path', '.')

    title_ps = ps('title', fontName=FONT_BOLD, fontSize=22, textColor=INK,
                  leading=26)
    sub_ps   = ps('sub', fontSize=9, textColor=FOIL, leading=13)
    meta_ps  = ps('meta', fontSize=8, textColor=CHROME, leading=12,
                  alignment=TA_RIGHT)
    badge_ps = ps('badge', fontName=FONT_BOLD, fontSize=9, textColor=CARD_BG,
                  leading=12, alignment=TA_CENTER)

    # Score badge (fleet average)
    agents = data.get('agents', [])
    if agents:
        avg = sum(a.get('maturity_score', a.get('trinity_score', 0))
                  for a in agents) // max(len(agents), 1)
        avg_label = score_label(avg)
        avg_color = score_color(avg)
    else:
        avg, avg_label, avg_color = 0, '—', CHROME

    badge = Table(
        [[Paragraph(f'{avg}%', badge_ps)],
         [Paragraph(avg_label, ps('bl', fontSize=7, textColor=CARD_BG,
                                  leading=9, alignment=TA_CENTER))]],
        colWidths=[60],
    )
    badge.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), avg_color),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 4),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('ROUNDEDCORNERS', [6]),
    ]))

    # Red accent strip (left) + title (middle) + meta + badge (right)
    row = [[
        '',
        [Paragraph('Agent Fleet Analysis', title_ps),
         Spacer(1, 3),
         Paragraph(
             f'Fleet maturity report  ·  {n_agents} agent{"s" if n_agents != 1 else ""} scanned',
             sub_ps,
         )],
        [badge,
         Spacer(1, 4),
         Paragraph(f'{generated}', meta_ps),
         Paragraph(scan_path, ps('sp', fontSize=7, textColor=CHROME,
                                 leading=9, alignment=TA_RIGHT))],
    ]]
    t = Table(row, colWidths=[5, CW * 0.60, CW * 0.40 - 5])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (0, -1), RED),
        ('BACKGROUND',    (1, 0), (-1, -1), CARD_BG),
        ('BOX',           (0, 0), (-1, -1), 0.5, HAIRLINE),
        ('TOPPADDING',    (0, 0), (-1, -1), 18),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 18),
        ('LEFTPADDING',   (1, 0), (1, -1), 16),
        ('RIGHTPADDING',  (-1, 0), (-1, -1), 16),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN',         (-1, 0), (-1, -1), 'RIGHT'),
    ]))
    return [t, Spacer(1, 14)]


# ── Executive Summary ─────────────────────────────────────────────────────────
def exec_summary(data):
    elems = [section_head('Executive Summary'), Spacer(1, 8)]
    summary = data.get('executive_summary', [])

    body_ps = ps('ebody', textColor=FOIL, leading=14, fontSize=9)
    bul_ps  = ps('ebul', textColor=FOIL, leading=13, fontSize=9,
                 leftIndent=12, spaceAfter=4)

    if isinstance(summary, str):
        elems.append(Paragraph(summary, body_ps))
    else:
        for pt in summary:
            elems.append(Paragraph(
                f'<font color="#DC2828">—</font>  {pt}', bul_ps))

    elems.append(Spacer(1, 12))
    return elems


# ── Score helper ──────────────────────────────────────────────────────────────
def agent_score(ag):
    """Return (score, kind): maturity for claude-code agents, readiness otherwise."""
    if ag.get('migration_readiness') is not None:
        return ag['migration_readiness'], 'readiness'
    return ag.get('maturity_score', ag.get('trinity_score', 0)), 'maturity'


# ── Agent Inventory ───────────────────────────────────────────────────────────
def agent_inventory(data):
    agents = data.get('agents', [])
    elems  = [section_head('Agent Inventory'), Spacer(1, 8)]

    if not agents:
        elems.append(Paragraph('No agents found.', STYLES['body']))
        return elems

    headers = ['Agent', 'Paradigm', 'Purpose', 'Role', 'Autonomy', 'Score', 'Key Gaps']
    hrow = [Paragraph(h, ps('th2', fontName=FONT_BOLD, fontSize=8,
                             textColor=FOIL, leading=11))
            for h in headers]
    rows = [hrow]

    for ag in agents:
        score, kind = agent_score(ag)
        gaps  = ag.get('gaps', [])
        gap_str = '; '.join(g.split('→')[0].strip() if '→' in g else g
                            for g in gaps[:2])
        if len(gaps) > 2:
            gap_str += f' +{len(gaps)-2}'

        sc = score_color(score)
        score_ps = ps('sc2', fontName=FONT_BOLD, fontSize=9, textColor=sc, leading=11)
        rows.append([
            Paragraph(f'<b>{ag.get("name","?")}</b>', STYLES['td_bold']),
            Paragraph(ag.get('paradigm', 'claude-code'), STYLES['td']),
            Paragraph((ag.get('purpose') or '—')[:55], STYLES['td']),
            Paragraph(ag.get('role', 'specialist'), STYLES['td']),
            Paragraph(ag.get('autonomy_level', 'basic'), STYLES['td']),
            Paragraph(f'<b>{score}%</b>', score_ps),
            Paragraph(gap_str or '—', STYLES['td']),
        ])

    cw = [CW * r for r in (0.13, 0.10, 0.20, 0.09, 0.11, 0.08, 0.29)]
    t = Table(rows, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), CARD_ALT),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [CARD_BG, CARD_ALT]),
        ('BOX',           (0, 0), (-1, -1), 0.5, HAIRLINE),
        ('INNERGRID',     (0, 0), (-1, -1), 0.3, HAIRLINE),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 7),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 7),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('LINEABOVE',     (0, 1), (-1, 1), 1, RED),
    ]))
    elems.append(t)

    legend_ps = ps('leg', fontSize=7.5, textColor=CHROME, spaceAfter=0)
    elems.append(Spacer(1, 5))
    elems.append(Paragraph(
        f'<font color="#2F9E6B"><b>80-100 Well-designed</b></font>  '
        f'<font color="#E8855A"><b>60-79 Functional · 40-59 Needs improvement</b></font>  '
        f'<font color="#DC2828"><b>0-39 Early stage</b></font>   '
        f'Score = fleet maturity for claude-code agents; migration readiness for other paradigms.',
        legend_ps,
    ))
    elems.append(Spacer(1, 12))
    return elems


# ── Fleet Diagram ─────────────────────────────────────────────────────────────
def fleet_diagram(data):
    topology = data.get('fleet_topology', {})
    diagram  = topology.get('ascii_diagram', '')
    notes    = topology.get('notes', [])

    elems = [section_head('Fleet Architecture'), Spacer(1, 8)]

    if diagram:
        lines = diagram.replace('\\n', '\n').split('\n')
        diagram_content = []
        for line in lines:
            safe = (line
                    .replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;')
                    .replace(' ', '&nbsp;'))
            diagram_content.append(Paragraph(safe, STYLES['mono']))

        box = Table([[diagram_content]], colWidths=[CW])
        box.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), CARD_BG),
            ('BOX',           (0, 0), (-1, -1), 0.5, HAIRLINE),
            ('TOPPADDING',    (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING',   (0, 0), (-1, -1), 16),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 16),
        ]))
        elems.append(box)

    if notes:
        elems.append(Spacer(1, 6))
        note_ps = ps('note', textColor=FOIL, fontSize=8.5, leading=13,
                     leftIndent=12, spaceAfter=3)
        for note in notes:
            elems.append(Paragraph(
                f'<font color="#DC2828">—</font>  {note}', note_ps))

    elems.append(Spacer(1, 12))
    return elems


# ── Architecture Recommendations ──────────────────────────────────────────────
def fleet_recommendations(data):
    topology = data.get('fleet_topology', {})
    notes    = topology.get('notes', [])
    hub      = topology.get('hub')
    kb       = topology.get('knowledge_brain')
    managers = topology.get('domain_managers', [])
    specs    = topology.get('specialists', [])

    elems = [section_head('Architecture Recommendations'), Spacer(1, 8)]

    recs = []
    if hub:
        recs.append(('Hub / Orchestrator', hub,
                     'Single entry point for routing work across the fleet. All user-facing '
                     'requests arrive here; the hub delegates to domain managers and specialists.'))
    else:
        recs.append(('Hub / Orchestrator', 'None identified',
                     'No hub agent detected. Designate the highest-scoring agent as your '
                     'orchestrator and give it a clear directive: route work, don\'t do everything.'))

    if kb:
        recs.append(('Knowledge Brain', kb,
                     'Holds institutional memory that other agents query. Wire domain managers '
                     'to consult this agent before answering questions that require context.'))
    else:
        recs.append(('Knowledge Brain', 'Not present — recommend adding',
                     'Your fleet lacks a shared knowledge layer. A Cornelius-style agent — a '
                     'long-running agent with structured memory — lets every other agent query '
                     'for institutional knowledge, market context, and strategic guidance.'))

    if managers:
        recs.append(('Domain Managers', ', '.join(managers),
                     'Own a domain (product, marketing, finance) and coordinate the specialists '
                     'beneath them. Each should have a clear scope and explicit delegation rules.'))

    if specs:
        recs.append(('Specialists', ', '.join(specs),
                     'Execute specific tasks. Give each agent structured skills so its capabilities '
                     'are discoverable by domain managers.'))

    recs.append(('Canon Layer', 'Not yet adopted',
                 'Agents that produce shared facts write them to canon/agents/<name>/. Consuming '
                 'agents read current data without ad-hoc queries — the connective tissue of a '
                 'coherent, non-redundant fleet.'))

    cat_ps  = ps('rcat', fontName=FONT_BOLD, fontSize=8.5, textColor=INK, leading=12)
    val_ps  = ps('rval', fontName=FONT_BOLD, fontSize=8, textColor=RED, leading=11)
    body_ps = ps('rbod', fontSize=8, textColor=FOIL, leading=11, spaceAfter=0)

    rows = []
    for cat, val, desc in recs:
        rows.append([
            Paragraph(cat, cat_ps),
            [Paragraph(val, val_ps), Spacer(1, 2), Paragraph(desc, body_ps)],
        ])

    t = Table(rows, colWidths=[CW * 0.22, CW * 0.78])
    t.setStyle(TableStyle([
        ('VALIGN',         (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [CARD_BG, CARD_ALT]),
        ('BOX',            (0, 0), (-1, -1), 0.5, HAIRLINE),
        ('INNERGRID',      (0, 0), (-1, -1), 0.3, HAIRLINE),
        ('TOPPADDING',     (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING',  (0, 0), (-1, -1), 8),
        ('LEFTPADDING',    (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',   (0, 0), (-1, -1), 10),
        ('LINEAFTER',      (0, 0), (0, -1), 1.5, RED),
    ]))
    elems.append(t)

    if notes:
        elems.append(Spacer(1, 8))
        note_ps = ps('anote', textColor=FOIL, fontSize=8.5, leading=13,
                     leftIndent=12, spaceAfter=3)
        for note in notes:
            elems.append(Paragraph(f'<font color="#DC2828">—</font>  {note}', note_ps))

    elems.append(Spacer(1, 12))
    return elems


# ── Marketplace Upgrade Paths ─────────────────────────────────────────────────
def upgrade_paths_section(data):
    paths = data.get('upgrade_paths', [])
    if not paths:
        return []

    elems = [section_head('Making Your Agents Useful — Marketplace Upgrade Paths'),
             Spacer(1, 8)]

    intro_ps = ps('upi', fontSize=8.5, textColor=FOIL, leading=12, spaceAfter=8)
    elems.append(Paragraph(
        'Each recommendation below maps to an installable skill from the abilities '
        'plugin marketplace — run the skill on the target agent and the upgrade is applied. '
        'This is what turns the report into a work order.', intro_ps))

    headers = ['Need', 'Install', 'Target agent(s)', 'Why']
    hrow = [Paragraph(h, ps('uph', fontName=FONT_BOLD, fontSize=8,
                             textColor=FOIL, leading=11))
            for h in headers]
    rows = [hrow]

    skill_ps = ps('ups', fontName=FONT_BOLD, fontSize=8, textColor=RED, leading=11)
    for p_ in paths:
        rows.append([
            Paragraph(p_.get('need', '—'), STYLES['td_bold']),
            Paragraph(f"/{p_.get('skill', '—')}", skill_ps),
            Paragraph(', '.join(p_.get('targets', [])) or '—', STYLES['td']),
            Paragraph(p_.get('note', ''), STYLES['td']),
        ])

    cw = [CW * r for r in (0.16, 0.26, 0.20, 0.38)]
    t = Table(rows, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), CARD_ALT),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [CARD_BG, CARD_ALT]),
        ('BOX',           (0, 0), (-1, -1), 0.5, HAIRLINE),
        ('INNERGRID',     (0, 0), (-1, -1), 0.3, HAIRLINE),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING',   (0, 0), (-1, -1), 7),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 7),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('LINEABOVE',     (0, 1), (-1, 1), 1, RED),
    ]))
    elems.append(t)
    elems.append(Spacer(1, 12))
    return elems


# ── Per-agent Detail Cards ────────────────────────────────────────────────────
def per_agent_details(data):
    agents = data.get('agents', [])
    if not agents:
        return []

    elems = [section_head('Agent Detail Cards'), Spacer(1, 8)]

    role_colors = {
        'hub':             INK,
        'orchestrator':    INK,
        'knowledge':       BLUE_AB,
        'knowledge brain': BLUE_AB,
        'domain-manager':  HexColor('#2D6A4F'),
        'domain manager':  HexColor('#2D6A4F'),
        'specialist':      FOIL,
    }

    for idx, ag in enumerate(agents):
        name     = ag.get('name', 'Unknown')
        score, kind = agent_score(ag)
        label    = score_label(score)
        sc       = score_color(score)
        role     = ag.get('role', 'specialist')
        paradigm = ag.get('paradigm', 'claude-code')
        purpose  = ag.get('purpose') or ''
        autonomy = ag.get('autonomy_level', 'basic')
        gaps     = ag.get('gaps', [])
        wins     = ag.get('quick_wins', [])
        structs  = ag.get('structural_changes', [])

        role_color = role_colors.get(role.lower(), FOIL)

        # ── Agent header strip ─────────────────────────────────────────────
        name_ps  = ps('an', fontName=FONT_BOLD, fontSize=13, textColor=CARD_BG, leading=16)
        role_ps  = ps('ar', fontName=FONT_BOLD, fontSize=7.5, textColor=CARD_BG, leading=10)
        score_ps = ps('as', fontName=FONT_BOLD, fontSize=22, textColor=CARD_BG,
                      leading=26, alignment=TA_RIGHT)
        lbl_ps   = ps('al', fontSize=7.5, textColor=CARD_BG, leading=10, alignment=TA_RIGHT)

        role_line = role.upper() if paradigm == 'claude-code' else f'{role.upper()} · {paradigm.upper()}'
        hdr = Table([[
            [Paragraph(name, name_ps), Paragraph(role_line, role_ps)],
            [Paragraph(f'{score}%', score_ps), Paragraph(f'{label} · {kind}', lbl_ps)],
        ]], colWidths=[CW * 0.70, CW * 0.30])
        hdr.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), role_color),
            ('TOPPADDING',    (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING',   (0, 0), (0, -1), 16),
            ('RIGHTPADDING',  (-1, 0), (-1, -1), 16),
            ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        card_elems = [hdr]

        # ── Purpose + autonomy ─────────────────────────────────────────────
        if purpose:
            meta_ps = ps('ameta', fontSize=8.5, textColor=FOIL, leading=12, spaceAfter=2)
            auto_ps = ps('aauto', fontSize=7.5, textColor=CHROME, leading=10)
            card_elems.append(Spacer(1, 10))
            card_elems.append(Paragraph(purpose[:260] + ('…' if len(purpose) > 260 else ''), meta_ps))
            card_elems.append(Spacer(1, 2))
            card_elems.append(Paragraph(
                f'Autonomy level: <b>{autonomy}</b> · Paradigm: <b>{paradigm}</b>', auto_ps))

        card_elems.append(Spacer(1, 8))

        # ── Gaps + wins two-column ─────────────────────────────────────────
        col_h  = ps('ch', fontName=FONT_BOLD, fontSize=8.5, textColor=INK,
                    leading=11, spaceAfter=4)
        gi_ps  = ps('gi', fontSize=8, textColor=INK, leading=11,
                    leftIndent=4, spaceAfter=1, fontName=FONT_BOLD)
        gd_ps  = ps('gd', fontSize=7.5, textColor=FOIL, leading=10,
                    leftIndent=14, spaceAfter=5)
        wi_ps  = ps('wi', fontSize=8, textColor=FOIL, leading=11,
                    leftIndent=4, spaceAfter=2)
        si_ps  = ps('si', fontSize=8, textColor=CHROME, leading=11,
                    leftIndent=4, spaceAfter=2)

        gap_items = [Paragraph('Gaps to address', col_h)]
        if gaps:
            for g in gaps:
                short  = g.split('→')[0].strip() if '→' in g else g
                detail = g.split('→', 1)[1].strip() if '→' in g else ''
                gap_items.append(Paragraph(
                    f'<font color="#DC2828">▸</font> {short[:70]}', gi_ps))
                if detail:
                    gap_items.append(Paragraph(detail[:200], gd_ps))
        else:
            gap_items.append(Paragraph('No gaps — well-structured.', STYLES['td']))

        win_items = [Paragraph('Quick wins', col_h)]
        if wins:
            for w in wins:
                win_items.append(Paragraph(
                    f'<font color="#2F9E6B">✓</font>  {w}', wi_ps))
        else:
            win_items.append(Paragraph('Structural work needed first.', STYLES['td']))

        if structs:
            win_items.append(Spacer(1, 6))
            win_items.append(Paragraph('Longer-term changes', col_h))
            for s in structs:
                win_items.append(Paragraph(f'◷  {s}', si_ps))

        two_col = Table([[gap_items, win_items]],
                        colWidths=[CW * 0.54, CW * 0.46])
        two_col.setStyle(TableStyle([
            ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
            ('BOX',           (0, 0), (-1, -1), 0.5, HAIRLINE),
            ('INNERGRID',     (0, 0), (-1, -1), 0.3, HAIRLINE),
            ('BACKGROUND',    (0, 0), (0, -1), CARD_BG),
            ('BACKGROUND',    (1, 0), (1, -1), CARD_ALT),
            ('TOPPADDING',    (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING',   (0, 0), (-1, -1), 12),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 12),
        ]))
        card_elems.append(two_col)

        elems.append(KeepTogether(card_elems))
        if idx < len(agents) - 1:
            elems.append(Spacer(1, 16))

    elems.append(Spacer(1, 12))
    return elems


# ── Roadmap ───────────────────────────────────────────────────────────────────
def migration_roadmap(data):
    roadmap = data.get('roadmap', {})
    elems   = [section_head('Fleet Improvement Roadmap'), Spacer(1, 8)]

    phase_defs = [
        ('phase1', 'Phase 1 — Fix foundations',        RED,    CARD_BG),
        ('phase2', 'Phase 2 — Build capabilities',     INK,    CARD_BG),
        ('phase3', 'Phase 3 — Connect the fleet',      FOIL,   CARD_ALT),
        ('phase4', 'Phase 4 — Autonomous deployment',  CHROME, CARD_ALT),
    ]

    cells = []
    for key, default_title, title_color, bg in phase_defs:
        phase = roadmap.get(key, {})
        if not phase:
            continue
        title = phase.get('title', default_title)
        items = phase.get('items', [])
        head = ps('ph2', fontName=FONT_BOLD, fontSize=8.5, textColor=title_color,
                  leading=12, spaceAfter=5)
        item_ps = ps('pi2', fontSize=8, textColor=FOIL, leading=11,
                     leftIndent=8, spaceAfter=2)
        cell = [Paragraph(title.replace('\n', '<br/>'), head)]
        for item in items:
            cell.append(Paragraph(
                f'<font color="#DC2828">·</font> {item}', item_ps))
        cells.append((cell, bg))

    if not cells:
        elems.append(Paragraph('No roadmap data.', STYLES['body']))
        return elems

    n     = len(cells)
    col_w = CW / n

    style_cmds = [
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('BOX',           (0, 0), (-1, -1), 0.5, HAIRLINE),
        ('INNERGRID',     (0, 0), (-1, -1), 0.3, HAIRLINE),
        ('TOPPADDING',    (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
        ('LINEABOVE',     (0, 0), (0, -1), 3, RED),
    ]
    for i, (_, bg) in enumerate(cells):
        style_cmds.append(('BACKGROUND', (i, 0), (i, 0), bg))

    table = Table([[c for c, _ in cells]], colWidths=[col_w] * n)
    table.setStyle(TableStyle(style_cmds))
    elems.append(table)
    elems.append(Spacer(1, 12))
    return elems


# ── Quick Wins ────────────────────────────────────────────────────────────────
def quick_wins(data):
    wins  = data.get('quick_wins', [])
    elems = [section_head('Quick Wins'), Spacer(1, 8)]

    if not wins:
        elems.append(Paragraph('No quick wins identified.', STYLES['body']))
        return elems

    win_ps = ps('qw', fontSize=9, textColor=FOIL, leading=13,
                leftIndent=12, spaceAfter=4)
    mid   = (len(wins) + 1) // 2
    left  = [Paragraph(f'<font color="#2F9E6B">✓</font>  {w}', win_ps)
             for w in wins[:mid]]
    right = [Paragraph(f'<font color="#2F9E6B">✓</font>  {w}', win_ps)
             for w in wins[mid:]]

    t = Table([[left, right]], colWidths=[CW / 2 - 4, CW / 2 - 4])
    t.setStyle(TableStyle([
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
    ]))
    elems.append(t)
    elems.append(Spacer(1, 10))
    return elems


# ── Main ──────────────────────────────────────────────────────────────────────
def build_story(data):
    story = []
    story.extend(header_block(data))
    story.extend(exec_summary(data))
    story.extend(agent_inventory(data))
    story.extend(fleet_diagram(data))
    story.extend(fleet_recommendations(data))
    story.extend(upgrade_paths_section(data))
    story.extend(per_agent_details(data))
    story.extend(migration_roadmap(data))
    story.extend(quick_wins(data))
    return story


def generate(data_path, output_path):
    with open(data_path) as f:
        data = json.load(f)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=ML, rightMargin=MR,
        topMargin=MT,  bottomMargin=MB + 6 * mm,
        title='Agent Fleet Analysis',
        author='ability.ai',
    )
    doc.build(build_story(data), onFirstPage=draw_page, onLaterPages=draw_page)
    print(f'PDF written: {output_path}')


def write_markdown(data_path, md_path):
    """Render the same data JSON as a markdown report — the agent-consumable
    twin of the PDF. Intended to be handed to agents (or committed) as the
    work order for executing the roadmap."""
    with open(data_path) as f:
        data = json.load(f)

    L = []
    L.append('# Agent Fleet Analysis')
    L.append('')
    L.append(f"Generated: {data.get('generated_at', '')}  ")
    L.append(f"Scan path: `{data.get('scan_path', '')}`")
    L.append('')
    L.append('> This markdown report is the machine-readable twin of the PDF. Every gap,')
    L.append('> quick win, and roadmap item below is agent-executable — hand this file to')
    L.append('> a Claude Code session (or the fleet hub) and it can apply the changes.')
    L.append('')

    L.append('## Executive Summary')
    L.append('')
    for line in data.get('executive_summary', []):
        L.append(f'- {line}')
    L.append('')

    L.append('## Fleet Inventory')
    L.append('')
    L.append('| Agent | Paradigm | Role | Autonomy | Score | Status |')
    L.append('|-------|----------|------|----------|-------|--------|')
    for a in data.get('agents', []):
        score, kind = agent_score(a)
        L.append(f"| {a['name']} | {a.get('paradigm', 'claude-code')} | {a.get('role', '')} "
                 f"| {a.get('autonomy_level', '')} | {score}% {kind} | {a.get('score_label', '')} |")
    L.append('')

    topo = data.get('fleet_topology', {})
    L.append('## Fleet Topology')
    L.append('')
    if topo.get('ascii_diagram'):
        L.append('```')
        L.append(topo['ascii_diagram'])
        L.append('```')
        L.append('')
    hub = topo.get('hub') or 'none designated'
    brain = topo.get('knowledge_brain') or 'none — recommend adding one'
    L.append(f'- **Hub:** {hub}')
    L.append(f'- **Knowledge brain:** {brain}')
    if topo.get('domain_managers'):
        L.append(f"- **Domain managers:** {', '.join(topo['domain_managers'])}")
    if topo.get('specialists'):
        L.append(f"- **Specialists:** {', '.join(topo['specialists'])}")
    L.append('')
    for note in topo.get('notes', []):
        L.append(f'> {note}')
        L.append('>')
    if topo.get('notes'):
        L.pop()  # drop trailing '>'
    L.append('')

    if data.get('upgrade_paths'):
        L.append('## Making Your Agents Useful — Marketplace Upgrade Paths')
        L.append('')
        L.append('Each item maps a fleet need to an installable skill from the abilities')
        L.append('plugin marketplace. Run the skill on the target agent to apply the upgrade.')
        L.append('')
        for up in data['upgrade_paths']:
            targets = ', '.join(up.get('targets', [])) or 'fleet-wide'
            note = f" — {up['note']}" if up.get('note') else ''
            L.append(f"- [ ] **{up.get('need', '')}**: run `/{up.get('skill', '')}` on {targets}{note}")
        L.append('')

    L.append('## Per-Agent Details')
    L.append('')
    for a in data.get('agents', []):
        score, kind = agent_score(a)
        L.append(f"### {a['name']} — {score}% {kind} ({a.get('score_label', '')})")
        L.append('')
        L.append(f"- **Directory:** `{a.get('dir', '')}`")
        L.append(f"- **Paradigm:** {a.get('paradigm', 'claude-code')}")
        L.append(f"- **Role:** {a.get('role', '')}")
        L.append(f"- **Autonomy:** {a.get('autonomy_level', '')}")
        L.append(f"- **Purpose:** {a.get('purpose', '')}")
        L.append('')
        if a.get('gaps'):
            L.append('**Gaps**')
            L.append('')
            for g in a['gaps']:
                L.append(f'- [ ] {g}')
            L.append('')
        if a.get('quick_wins'):
            L.append('**Quick wins (mechanical — an agent applies these in minutes)**')
            L.append('')
            for w in a['quick_wins']:
                L.append(f'- [ ] {w}')
            L.append('')
        if a.get('structural_changes'):
            L.append('**Structural changes (need an operator design decision first)**')
            L.append('')
            for c in a['structural_changes']:
                L.append(f'- [ ] {c}')
            L.append('')

    L.append('## Improvement Roadmap')
    L.append('')
    L.append('All four phases are agent-executable. Run them as a sequence, not a calendar —')
    L.append('a single working session can take a fleet through phases 1-3 and deploy in hours.')
    L.append('')
    roadmap = data.get('roadmap', {})
    for key in ('phase1', 'phase2', 'phase3', 'phase4'):
        ph = roadmap.get(key)
        if not ph:
            continue
        L.append(f"### {ph.get('title', key)}")
        L.append('')
        for item in ph.get('items', []):
            L.append(f'- [ ] {item}')
        L.append('')

    L.append('## Top Quick Wins (fleet-wide)')
    L.append('')
    for i, w in enumerate(data.get('quick_wins', []), 1):
        L.append(f'{i}. {w}')
    L.append('')

    Path(md_path).parent.mkdir(parents=True, exist_ok=True)
    Path(md_path).write_text('\n'.join(L) + '\n')
    print(f'Markdown written: {md_path}')


def main():
    p = argparse.ArgumentParser(description='Generate Agent Fleet Analysis report (PDF + optional markdown)')
    p.add_argument('--data',     required=True, help='JSON data file path')
    p.add_argument('--output',   required=True, help='Output PDF path')
    p.add_argument('--markdown', help='Also write a markdown report to this path')
    args = p.parse_args()

    if not Path(args.data).exists():
        print(f'ERROR: data file not found: {args.data}', file=sys.stderr)
        sys.exit(1)

    generate(args.data, args.output)
    if args.markdown:
        write_markdown(args.data, args.markdown)


if __name__ == '__main__':
    main()
