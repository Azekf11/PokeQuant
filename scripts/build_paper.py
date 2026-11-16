"""Assemble the working paper from its section drafts.

Writes research/paper/paper.md (citations resolved to author-year, reference
list built from references.bib) and research/paper/paper.html. With --pdf, it
also prints the HTML to research/paper/paper.pdf with a local Chrome or
Chromium in headless mode.

Citations use the pandoc forms [@key], [@a; @b] and [-@key] (year only).
Every cited key must exist in references.bib, and only cited entries are
listed.

Usage: uv run python scripts/build_paper.py [--pdf]
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "research/paper"
DRAFTS = PAPER / "drafts"
ORDER = (
    "00_abstract.md",
    "01_introduction.md",
    "02_data.md",
    "03_model.md",
    "04_results.md",
    "05_robustness.md",
    "06_conclusion.md",
)
APPENDIX = "10_appendix.md"
TITLE = (
    "Opening or Buying? A Probabilistic and Risk-Adjusted Comparison of Pokémon TCG "
    "Booster Acquisition and Secondary-Market Purchases"
)
AUTHOR = "Anh-Vu TA"
VERSION = "3"
DATE = "November 2026"
DOI = "10.5281/zenodo.24251050"
REPOSITORY = "https://github.com/Azekf11/PokeQuant"
CHROME = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome",
    "chromium",
    "chromium-browser",
)
CITE = re.compile(r"\[(-?@[\w-]+(?:\s*;\s*-?@[\w-]+)*)\]")


@dataclass(frozen=True)
class Entry:
    key: str
    kind: str
    fields: dict[str, str]

    @property
    def surnames(self) -> list[str]:
        out = []
        for name in re.split(r"\s+and\s+", self.fields.get("author", "")):
            name = name.strip()
            out.append(name.split(",")[0].strip() if "," in name else name.split()[-1])
        return [latex(s) for s in out if s]

    @property
    def year(self) -> str:
        return self.fields.get("year", "n.d.")

    def short(self) -> str:
        names = self.surnames
        if len(names) == 1:
            return names[0]
        if len(names) == 2:
            return f"{names[0]} and {names[1]}"
        return f"{names[0]} et al."


def latex(text: str) -> str:
    """Undo the few LaTeX escapes used in references.bib."""
    text = re.sub(r"\{\\'(\w)\}|\\'\{?(\w)\}?", lambda m: _acute(m.group(1) or m.group(2)), text)
    text = re.sub(r'\{\\"(\w)\}|\\"\{?(\w)\}?', lambda m: _umlaut(m.group(1) or m.group(2)), text)
    return text.replace("\\&", "&").replace("{", "").replace("}", "").replace("--", "\u2013")


def _acute(c: str) -> str:
    return {"e": "é", "E": "É", "a": "á", "o": "ó", "i": "í", "u": "ú"}.get(c, c)


def _umlaut(c: str) -> str:
    return {"o": "ö", "a": "ä", "u": "ü", "O": "Ö", "A": "Ä", "U": "Ü"}.get(c, c)


def parse_bib(text: str) -> dict[str, Entry]:
    entries: dict[str, Entry] = {}
    for m in re.finditer(r"@(\w+)\{([\w-]+),(.*?)\n\}", text, re.S):
        fields: dict[str, str] = {}
        for f in re.finditer(r"(\w+)\s*=\s*\{(.*?)\}\s*,?\s*\n", m.group(3) + "\n", re.S):
            fields[f.group(1).lower()] = " ".join(f.group(2).split())
        entries[m.group(2)] = Entry(m.group(2), m.group(1).lower(), fields)
    return entries


def resolve(text: str, bib: dict[str, Entry], cited: list[str]) -> str:
    def one(m: re.Match[str]) -> str:
        parts = []
        year_only = True
        for raw in m.group(1).split(";"):
            raw = raw.strip()
            suppress = raw.startswith("-")
            key = raw.lstrip("-@")
            if key not in bib:
                raise KeyError(f"unknown citation key: {key}")
            if key not in cited:
                cited.append(key)
            e = bib[key]
            parts.append(e.year if suppress else f"{e.short()} {e.year}")
            year_only = year_only and suppress
        joined = ", ".join(parts) if year_only else "; ".join(parts)
        return f"({joined})"

    return CITE.sub(one, text)


def reference(e: Entry) -> str:
    f = {k: latex(v) for k, v in e.fields.items()}
    authors = re.split(r"\s+and\s+", f.get("author", ""))
    names = ", ".join(a.strip() for a in authors[:-1])
    names = f"{names} and {authors[-1].strip()}" if len(authors) > 1 else authors[0]
    where = f.get("journal") or f.get("booktitle") or f.get("howpublished") or f.get("school", "")
    if e.kind == "thesis" and "type" in f:
        where = f"{f['type']}, {where}"
    details = ", ".join(
        x
        for x in (
            where,
            f"{f['volume']}({f['number']})" if "volume" in f and "number" in f else f.get("volume"),
            f.get("pages"),
        )
        if x
    )
    link = f"https://doi.org/{f['doi']}" if "doi" in f else f.get("url", "")
    out = f"{names} ({e.year}). {f.get('title', '')}. *{details}*."
    return f"{out} <{link}>" if link else out


def assemble() -> str:
    bib = parse_bib((PAPER / "references.bib").read_text(encoding="utf-8"))
    cited: list[str] = []
    body = []
    for name in (*ORDER, APPENDIX):
        path = DRAFTS / name
        if not path.exists():
            raise FileNotFoundError(f"missing section draft: {path}")
        text = re.sub(r"<!--.*?-->\s*", "", path.read_text(encoding="utf-8"), flags=re.S)
        text = text.replace("](../figures/", "](figures/")
        text = text.replace("](../../reports/figures/", "](../reports/figures/")
        if name == APPENDIX:
            refs = sorted((bib[k] for k in cited), key=lambda e: (e.surnames[0], e.year))
            body.append("# References\n\n" + "\n\n".join(reference(e) for e in refs) + "\n")
        body.append(resolve(text, bib, cited).strip() + "\n")
    head = (
        f"# {TITLE}\n\n"
        f'<p class="author">{AUTHOR}</p>\n\n'
        f'<p class="meta">Working paper, version {VERSION}, {DATE}<br>'
        f'Code, data and configurations: <a href="{REPOSITORY}">{REPOSITORY}</a> · '
        f'DOI <a href="https://doi.org/{DOI}">{DOI}</a></p>\n\n'
    )
    return head + "\n".join(body)


CSS = """
body { font: 10pt/1.34 "Latin Modern Roman", "CMU Serif", "Times New Roman", Times, serif;
       color: #111; max-width: 46em; margin: 1em auto; padding: 0 1em; text-align: justify;
       hyphens: auto; }
h1 { font-size: 1.15em; margin: 1.1em 0 .35em; text-align: left; }
h1:first-child { font-size: 1.45em; text-align: center; line-height: 1.25;
                 margin: 0 0 .5em; }
h2 { font-size: 1em; margin: .9em 0 .25em; text-align: left; } h3 { font-size: 1em; }
p { margin: .45em 0; }
p.author { text-align: center; font-size: 1.05em; margin: 0; }
p.meta { text-align: center; font-size: .82em; color: #333; margin: .3em 0 1em; }
div.abstract { margin: 0 2em 1.2em; font-size: .9em; }
div.abstract h1 { font-size: 1em; text-align: center; margin: 0 0 .3em; }
table { border-collapse: collapse; margin: .4em auto .7em; font-size: .8em;
        border-top: 1.2px solid #111; border-bottom: 1.2px solid #111; text-align: left; }
th, td { padding: .12em .45em; vertical-align: top; }
th { border-bottom: .8px solid #111; font-weight: 600; }
figure { margin: .5em 0 .8em; break-inside: avoid; }
figure img { max-width: 86%; display: block; margin: 0 auto; }
figure img[src$="tornado.png"] { max-width: 60%; }
figure img[src$="figA1_pipeline.png"] { max-width: 66%; }
figcaption { font-size: .82em; margin-top: .25em; text-align: left; }
code, pre { font-size: .78em; } pre { background: #f6f6f4; padding: .45em .6em; overflow-x: auto;
  border-top: 1px solid #111; border-bottom: 1px solid #111; text-align: left; line-height: 1.25; }
@page { size: letter; margin: 1.8cm 2cm; }
@media print { body { margin: 0; max-width: none; } h1, h2, h3 { break-after: avoid; }
  table, figure, pre { break-inside: avoid; } }
"""


FIGURE = re.compile(r'<p><img alt="([^"]*)" src="([^"]*)" ?/?></p>')
ABSTRACT = re.compile(r"(<h1>Abstract</h1>.*?)(?=<h1>)", re.S)


def to_html(md_text: str) -> str:
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "sane_lists"])
    body = FIGURE.sub(
        lambda m: (
            f'<figure><img src="{m[2]}" alt=""><figcaption>'
            + re.sub(r"^(Figure [A-Z]?\d+\.)", r"<strong>\1</strong>", m[1])
            + "</figcaption></figure>"
        ),
        body,
    )
    body = ABSTRACT.sub(r'<div class="abstract">\1</div>\n', body, count=1)
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        f"<title>{html.escape(TITLE)}</title><style>{CSS}</style></head>"
        f"<body>\n{body}\n</body></html>\n"
    )


def to_pdf(html_path: Path, pdf_path: Path) -> None:
    exe = next((c for c in CHROME if Path(c).exists() or shutil.which(c)), None)
    if exe is None:
        raise SystemExit("no Chrome or Chromium found for --pdf")
    subprocess.run(
        [
            exe,
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path}",
            html_path.resolve().as_uri(),
        ],
        check=True,
        capture_output=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pdf", action="store_true", help="also print paper.pdf with Chrome")
    args = parser.parse_args()
    text = assemble()
    (PAPER / "paper.md").write_text(text, encoding="utf-8")
    (PAPER / "paper.html").write_text(to_html(text), encoding="utf-8")
    print(f"wrote {PAPER / 'paper.md'} and paper.html")
    if args.pdf:
        to_pdf(PAPER / "paper.html", PAPER / "paper.pdf")
        print(f"wrote {PAPER / 'paper.pdf'}")


if __name__ == "__main__":
    main()
