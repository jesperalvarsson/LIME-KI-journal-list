"""Inline the font and the journal data into the template, once.

Everything ships in a single file so the page works from a USB stick, from an
email attachment, and behind a firewall. Nothing is fetched at runtime.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
tpl  = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
font = open(os.path.join(HERE, "font.css"), encoding="utf-8").read().strip()
data = open(os.path.join(ROOT, "data/journals.json"), encoding="utf-8").read().strip()

# Two destinations, same bytes. dist/ki-journal-list.html keeps a filename
# worth emailing; index.html at the repository root is what GitHub Pages serves
# from the short URL. Writing both from one string is what stops them drifting,
# and because the contents are identical git stores a single blob for the two
# paths, so the duplicate costs nothing in the history.
out  = os.path.join(ROOT, "dist", "ki-journal-list.html")
page = os.path.join(ROOT, "index.html")
assert tpl.count("{{FONT}}") == 1 and tpl.count("{{DATA}}") == 1
html = tpl.replace("{{FONT}}", font).replace("{{DATA}}", data)

# A stray </script> inside the JSON would close the block early. None of the
# titles contain one, but assert rather than trust.
assert "</script" not in data.lower(), "data contains a script terminator"

os.makedirs(os.path.dirname(out), exist_ok=True)
for path in (out, page):
    open(path, "w", encoding="utf-8").write(html)

a, b = (open(p, "rb").read() for p in (out, page))
assert a == b, "the two copies differ"
print(f"{out}  {len(a)/1024:.0f} kB")
print(f"{page}  identical copy for GitHub Pages")
