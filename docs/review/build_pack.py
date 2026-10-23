#!/usr/bin/env python3
"""Build the electrical review pack: one PDF with a project overview, the brief, schematic, layout, spec, board README,
SPICE results and datasheet cross-check, plus a cover page with contents.

Markdown is converted with pandoc (GitHub flavour), printed with Chrome (headless) and merged with PDFKit
(macOS). Repo links become plain text, since the reader has the PDF, not the repo.
Run: python3 docs/review/build_pack.py   ->   docs/review/electrical-review-pack.pdf
"""
import datetime
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/review/electrical-review-pack.pdf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PCB = ROOT / "pcb/motion-board"

# (bookmark title, source); .md files are rendered, .pdf files are included as they are, a list of images
# becomes a page of figures.
PARTS = [
    ("Project overview", ROOT / "docs/review/project-overview.md"),
    ("Review brief and questions", ROOT / "docs/review/electrical-review.md"),
    ("Schematic", PCB / "fab/rbg3-motion-schematic.pdf"),
    ("PCB layout (one layer per page)", PCB / "fab/rbg3-motion-layout.pdf"),
    ("3D renders", [PCB / f"fab/rbg3-motion-3d-{v}.png" for v in ("iso", "top", "bottom")]),
    ("Electrical specification", ROOT / "docs/spec/02-electrical.md"),
    ("Motion board README", PCB / "README.md"),
    ("SPICE simulations", PCB / "sim/README.md"),
    ("SPICE results table", PCB / "sim/results.md"),
    ("Datasheet cross-check", ROOT / "docs/datasheets/CROSSCHECK.md"),
]

CSS = """
@page { size: A4; margin: 16mm 15mm; }
body { font: 10pt/1.45 -apple-system, "Helvetica Neue", Arial, sans-serif; color: #111; }
h1 { font-size: 17pt; border-bottom: 2px solid #333; padding-bottom: 4px; }
h2 { font-size: 13pt; margin-top: 1.4em; border-bottom: 1px solid #bbb; }
h3 { font-size: 11pt; }
h1, h2, h3 { break-after: avoid; }
table { border-collapse: collapse; margin: 8px 0; font-size: 8.5pt; width: 100%; }
th, td { border: 1px solid #bbb; padding: 3px 5px; vertical-align: top; text-align: left; }
th { background: #eee; }
tr { break-inside: avoid; }
code { font: 8.5pt Menlo, monospace; background: #f3f3f3; padding: 0 2px; }
pre { background: #f3f3f3; padding: 6px; white-space: pre-wrap; font-size: 8pt; }
pre code { background: none; }
img { max-width: 100%; max-height: 120mm; break-inside: avoid; }
figure { margin: 0 0 8mm; break-inside: avoid; text-align: center; }
figure img { max-height: 115mm; }
figcaption { font-size: 8.5pt; color: #444; }
.src { color: #666; font-size: 8pt; margin-bottom: 6px; }
.cover h1 { font-size: 24pt; border: none; margin-top: 60mm; }
.cover td.n { text-align: right; width: 18mm; }
"""


def html_page(body, title):
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title>" \
           f"<style>{CSS}</style></head><body>{body}</body></html>"


def render_md(src: Path):
    body = subprocess.run(["pandoc", "-f", "gfm", "-t", "html", str(src)],
                          check=True, capture_output=True, text=True).stdout
    # Images: absolute file URLs. Links: keep the text only.
    body = re.sub(r'src="(?!https?:|file:)([^"]+)"',
                  lambda m: f'src="{(src.parent / m.group(1)).resolve().as_uri()}"', body)
    body = re.sub(r'<a href="[^"]*">(.*?)</a>', r"\1", body, flags=re.S)
    rel = src.relative_to(ROOT)
    return f'<div class="src">Source: {rel}</div>' + body


def render_images(title, images):
    figs = "".join(f'<figure><img src="{img.as_uri()}"><figcaption>{img.relative_to(ROOT)}</figcaption></figure>'
                   for img in images)
    return f"<h1>{title}</h1><p>Rendered by KiCad from the board file. The ESP32 and TMC2209 modules plug " \
           f"into the empty sockets and are not drawn; J1 (XT30) has no 3D model.</p>{figs}"


def source_label(src):
    return f"{src[0].parent.relative_to(ROOT)}/*.png" if isinstance(src, list) else str(src.relative_to(ROOT))


def chrome_pdf(html: str, out: Path, tmp: Path):
    page = tmp / (out.stem + ".html")
    page.write_text(html)
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    "--allow-file-access-from-files", f"--print-to-pdf={out}", page.as_uri()],
                   check=True, capture_output=True)


def page_count(pdf: Path):
    data = pdf.read_bytes()
    return len(re.findall(rb"/Type\s*/Page[^s]", data))


def main():
    rev = subprocess.run(["git", "-C", str(ROOT), "describe", "--always", "--dirty"],
                         capture_output=True, text=True).stdout.strip()
    spec = re.search(r"Draft (v[\d.]+)", (ROOT / "docs/spec/00-overview.md").read_text()).group(1)
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        pdfs = []
        for i, (title, src) in enumerate(PARTS):
            if isinstance(src, list):
                out = tmp / f"part{i}.pdf"
                chrome_pdf(html_page(render_images(title, src), title), out, tmp)
                pdfs.append(out)
            elif src.suffix == ".pdf":
                pdfs.append(src)
            else:
                out = tmp / f"part{i}.pdf"
                chrome_pdf(html_page(render_md(src), title), out, tmp)
                pdfs.append(out)

        rows, page = [], 2
        for (title, src), pdf in zip(PARTS, pdfs):
            rows.append(f"<tr><td>{title}</td><td><code>{source_label(src)}</code></td>"
                        f"<td class='n'>{page}</td></tr>")
            page += page_count(pdf)
        cover = f"""<div class="cover"><h1>RBG3-MOTION electrical review pack</h1>
<p>RackBotGen3, Delta Cup 2026. Spec {spec}, repo {rev}, built {datetime.date.today()}.</p>
<p>Start with the project overview, then the review brief: it explains the board, what has been verified and the questions.
The PDF bookmarks jump to each part.</p>
<table><tr><th>Part</th><th>Source</th><th class='n'>Page</th></tr>{''.join(rows)}</table></div>"""
        cover_pdf = tmp / "cover.pdf"
        chrome_pdf(html_page(cover, "Cover"), cover_pdf, tmp)

        args = [str(OUT), "Cover and contents", str(cover_pdf)]
        for (title, _), pdf in zip(PARTS, pdfs):
            args += [title, str(pdf)]
        subprocess.run(["swift", str(Path(__file__).with_name("merge_pdf.swift")), *args], check=True)


if __name__ == "__main__":
    main()
