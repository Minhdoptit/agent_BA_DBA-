"""Word Document (.docx) Exporter for BA AI Agent.

Converts structured Markdown SRS specifications into formatted Microsoft Word documents.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

try:
    import docx
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml import OxmlElement, parse_xml
    from docx.oxml.ns import nsdecls, qn
except ImportError:
    docx = None


def export_markdown_to_docx(markdown_content: str, output_path: str | Path, title: str = "Software Requirements Specification") -> bool:
    """Parses markdown text and generates a formatted Microsoft Word .docx document."""
    if not docx:
        return False

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = docx.Document()

    # Set page margins (1 inch)
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    lines = markdown_content.splitlines()
    in_code_block = False
    code_lines: List[str] = []
    in_table = False
    table_lines: List[str] = []

    def flush_table():
        nonlocal in_table, table_lines
        if not table_lines:
            return
        
        parsed_rows = []
        for tl in table_lines:
            # Skip separator line like |:---|:---|
            if re.match(r"^\|[\s\-:|]+\|$", tl.strip()):
                continue
            cols = [c.strip() for c in tl.strip().strip("|").split("|")]
            if any(cols):
                parsed_rows.append(cols)

        if parsed_rows:
            max_cols = max(len(r) for r in parsed_rows)
            table = doc.add_table(rows=len(parsed_rows), cols=max_cols)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER

            for r_idx, row_data in enumerate(parsed_rows):
                for c_idx in range(max_cols):
                    cell = table.cell(r_idx, c_idx)
                    cell.text = row_data[c_idx] if c_idx < len(row_data) else ""
                    # Style header row
                    if r_idx == 0:
                        shading_elm = parse_xml(r'<w:shd {} w:fill="E2E8F0"/>'.format(nsdecls('w')))
                        cell._tc.get_or_add_tcPr().append(shading_elm)
                        for p in cell.paragraphs:
                            for run in p.runs:
                                run.bold = True
            doc.add_paragraph()  # spacing
        table_lines = []
        in_table = False

    def flush_code():
        nonlocal in_code_block, code_lines
        if not code_lines:
            return
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.4)
        run = p.add_run("\n".join(code_lines))
        run.font.name = "Consolas"
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(40, 50, 60)
        code_lines = []
        in_code_block = False

    for line in lines:
        stripped = line.strip()

        # Handle Code block delimiters
        if stripped.startswith("```"):
            if in_code_block:
                flush_code()
            else:
                if in_table:
                    flush_table()
                in_code_block = True
                code_lines = []
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        # Handle Markdown Tables
        if stripped.startswith("|") and stripped.endswith("|"):
            in_table = True
            table_lines.append(stripped)
            continue
        elif in_table:
            flush_table()

        if not stripped:
            continue

        # Handle Headings
        if stripped.startswith("# "):
            h = doc.add_heading(stripped[2:].strip(), level=0)
            h.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif stripped.startswith("## "):
            doc.add_heading(stripped[3:].strip(), level=1)
        elif stripped.startswith("### "):
            doc.add_heading(stripped[4:].strip(), level=2)
        elif stripped.startswith("#### "):
            doc.add_heading(stripped[5:].strip(), level=3)
        elif stripped.startswith("- ") or stripped.startswith("* "):
            clean_text = stripped[2:].strip()
            # Clean basic bold markdown **text**
            clean_text = re.sub(r"\*\*(.*?)\*\*", r"\1", clean_text)
            clean_text = re.sub(r"`(.*?)`", r"\1", clean_text)
            doc.add_paragraph(clean_text, style="List Bullet")
        elif stripped.startswith("> "):
            clean_text = stripped[2:].strip()
            clean_text = re.sub(r"\*\*(.*?)\*\*", r"\1", clean_text)
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.3)
            r = p.add_run(clean_text)
            r.italic = True
            r.font.color.rgb = RGBColor(90, 100, 110)
        else:
            clean_text = re.sub(r"\*\*(.*?)\*\*", r"\1", stripped)
            clean_text = re.sub(r"`(.*?)`", r"\1", clean_text)
            doc.add_paragraph(clean_text)

    if in_table:
        flush_table()
    if in_code_block:
        flush_code()

    doc.save(str(output_path))
    return True
