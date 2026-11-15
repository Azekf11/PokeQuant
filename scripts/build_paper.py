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
    "02_literature.md",
    "03_data.md",
    "04_methodology.md",
    "05_design.md",
    "06_results.md",
    "07_robustness.md",
    "08_discussion.md",
    "09_conclusion.md",
)
APPENDIX = "10_appendix.md"
TITLE = (
    "Opening or Buying? A Probabilistic and Risk-Adjusted Comparison of Pokémon TCG "
    "Booster Acquisition and Secondary-Market Purchases"
)
AUTHOR = "Azekf11"
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
        f"# {TITLE}\n\n**{AUTHOR}** · Working paper · Code, data and configurations: "
        f"<{REPOSITORY}>\n\n"
    )
    return head + "\n".join(body)


CSS = """
body { font: 11pt/1.5 Georgia, "Times New Roman", serif; color: #111; max-width: 46em;
       margin: 2em auto; padding: 0 1em; }
h1 { font-size: 1.45em; margin: 1.6em 0 .5em; } h1:first-child { font-size: 1.7em; }
h2 { font-size: 1.15em; margin: 1.3em 0 .4em; } h3 { font-size: 1em; }
table { border-collapse: collapse; margin: .8em 0; font-size: .86em; }
th, td { border-bottom: 1px solid #ccc; padding: .25em .5em; text-align: left;
         vertical-align: top; }
th { border-bottom: 1.5px solid #333; }
img { max-width: 100%; display: block; margin: .6em auto 0; }
code, pre { font-size: .85em; } pre { background: #f5f5f3; padding: .6em; overflow-x: auto; }
p > em:only-child { display: block; font-size: .9em; color: #333; margin-bottom: 1em; }
@page { size: A4; margin: 2cm 2cm; }
@media print { body { margin: 0; max-width: none; } h1 { break-after: avoid; }
  h2, h3 { break-after: avoid; } table, img { break-inside: avoid; } }
"""


def to_html(md_text: str) -> str:
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "sane_lists"])
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
