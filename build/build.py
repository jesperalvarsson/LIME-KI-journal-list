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

out = os.path.join(ROOT, "dist", "ki-journal-list.html")
assert tpl.count("{{FONT}}") == 1 and tpl.count("{{DATA}}") == 1
html = tpl.replace("{{FONT}}", font).replace("{{DATA}}", data)

# A stray </script> inside the JSON would close the block early. None of the
# titles contain one, but assert rather than trust.
assert "</script" not in data.lower(), "data contains a script terminator"

os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "w", encoding="utf-8").write(html)
print(f"{out}  {os.path.getsize(out)/1024:.0f} kB")
