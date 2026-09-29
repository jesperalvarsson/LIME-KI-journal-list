"""WCAG 2.1 contrast audit of the shipped page, both themes.

Reads the design tokens straight out of dist/ki-journal-list.html so the audit
cannot drift from what is actually served. 4.5:1 is the AA floor for body text,
3:1 for large text and for the edges of controls that must be locatable.
"""
import re, sys, itertools, pathlib

SRC = pathlib.Path(__file__).resolve().parents[1] / "dist" / "ki-journal-list.html"
html = SRC.read_text(encoding="utf-8")

def lum(hexs):
    r, g, b = (int(hexs[i:i+2], 16) / 255 for i in (1, 3, 5))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)

def tokens(block):
    return dict(re.findall(r"--([a-z0-9-]+)\s*:\s*(#[0-9A-Fa-f]{6})", block))

# :root is the light theme; the first dark block follows it.
blocks = re.findall(r"\{([^{}]*--bg\s*:[^{}]*)\}", html)
assert len(blocks) >= 2, f"expected a light and a dark token block, found {len(blocks)}"
themes = {"light": tokens(blocks[0]), "dark": tokens(blocks[1])}

# (ink, background, minimum) - every pairing the page actually paints.
PAIRS = [
    ("text", "bg", 4.5), ("text", "surface", 4.5), ("text", "surface-2", 4.5),
    ("head", "bg", 4.5), ("head", "surface", 4.5),
    ("dim", "bg", 4.5), ("dim", "surface", 4.5), ("dim", "surface-2", 4.5),
    ("faint", "bg", 4.5), ("faint", "surface", 4.5),
    ("accent", "bg", 4.5), ("accent", "surface", 4.5),
    ("accent-2", "surface", 4.5),
    ("on-accent", "accent", 4.5),
    ("l3-ink", "l3", 4.5), ("l2-ink", "l2", 4.5),
    ("l1-ink", "l1", 4.5), ("l0-ink", "l0", 4.5),
    ("good", "surface", 4.5), ("warn", "surface", 4.5), ("bad", "surface", 4.5),
    ("border-strong", "bg", 3.0), ("border-strong", "surface", 3.0),
    ("accent", "surface-2", 3.0),
]

bad = []
print(f"{'theme':6} {'pair':34} {'ratio':>6}  min")
for name, t in themes.items():
    for ink, bgk, need in PAIRS:
        if ink not in t or bgk not in t:
            bad.append((name, f"{ink} on {bgk}", None, need)); continue
        r = ratio(t[ink], t[bgk])
        ok = r >= need
        if not ok:
            bad.append((name, f"{ink} on {bgk}", r, need))
        print(f"{name:6} {ink + ' on ' + bgk:34} {r:6.2f}  {need}  {'' if ok else '<-- FAIL'}")

# Luminance contrast is the wrong instrument for telling the four level
# colours apart - l1 and l0 differ by hue (purple against a red tint), not by
# lightness, and a ratio between two backgrounds says nothing useful about
# that. The property worth asserting is that colour is never load-bearing: a
# reader who cannot separate those hues must still get the answer. So check
# that every chip carries its digit and that the legend spells all four out.
print()
chip = re.search(r"'<span class=\"chip lv' \+ (\w+)\.l \+ '\">' \+ \1\.l", html)
if not chip:
    bad.append(("both", "level chip does not render its own digit", None, None))
    print("chip renders colour without the digit  <-- FAIL")
else:
    print("chip renders the level digit inside the swatch          ok")

for lv, word in [(3, "Highest quality"), (2, "High standard"),
                 (1, "Fulfils the criteria"), (0, "Does not fulfil the criteria")]:
    if f'class="chip lv{lv}">{lv}<' in html and word in html:
        print(f"level {lv} stated in words as well as colour            ok")
    else:
        bad.append(("both", f"level {lv} not stated in words", None, None))
        print(f"level {lv} not stated in words  <-- FAIL")

# The counts in the legend must match the data actually shipped, or the page
# is quietly describing a different list than the one it searches.
counts = {int(a): int(b.replace(",", "")) for a, b in
          re.findall(r'class="chip lv(\d)">\d</span><span>.*?([\d,]+) journals', html)}
total = sum(counts.values())
if len(counts) == 4 and total == 6855:
    print(f"legend counts sum to the shipped corpus ({total})        ok")
else:
    bad.append(("both", f"legend counts {counts} sum to {total}", None, 6855))
    print(f"legend counts sum to {total}, expected 6855  <-- FAIL")

print(f"\n{len(bad)} failing pair(s)" if bad else "\nall pairs pass WCAG AA")
sys.exit(1 if bad else 0)
