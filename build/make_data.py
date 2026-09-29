"""Turn the KI-JL spreadsheet into the compact payload the lookup page embeds.

The sheet has four preamble rows (title, the two decision statements, and the
two "more information" links) before the header, so the header is row 5.
"""
import json, re, sys, unicodedata
import pandas as pd

SRC = sys.argv[1] if len(sys.argv) > 1 else "source/kijl_2026.xlsx"
OUT = sys.argv[2] if len(sys.argv) > 2 else "data/journals.json"


def norm(s):
    """Fold to the form the search compares against: no diacritics, no
    punctuation, single spaces. 'Zeitschrift fur ...' must match 'für'."""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def issn(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    s = re.sub(r"[^0-9xX]", "", str(v)).upper()
    return f"{s[:4]}-{s[4:]}" if len(s) == 8 else ""


df = pd.read_excel(SRC, sheet_name="journals", header=5)
df.columns = ["title", "issn_p", "issn_d", "level"]

rows = []
for r in df.itertuples(index=False):
    rows.append({
        "t": str(r.title).strip(),
        "p": issn(r.issn_p),
        "d": issn(r.issn_d),
        "l": int(r.level),
    })

# Eight titles appear twice. Four are the same journal listed under two ISSN
# pairs and agree on level - those merge. Four are genuinely different journals
# that share a name and DISAGREE on level (Omega, Surgery, Medicina, Revista de
# psiquiatria y salud mental). Those must stay separate, because collapsing them
# would make the page answer confidently and wrongly.
by_title = {}
for r in rows:
    by_title.setdefault(norm(r["t"]), []).append(r)

out, merged, kept_apart = [], 0, []
for key, group in by_title.items():
    if len(group) == 1:
        out.append(group[0])
        continue
    if len({g["l"] for g in group}) == 1:
        issns = []
        for g in group:
            for v in (g["p"], g["d"]):
                if v and v not in issns:
                    issns.append(v)
        out.append({"t": group[0]["t"], "p": issns[0] if issns else "",
                    "d": issns[1] if len(issns) > 1 else "",
                    "x": issns[2:], "l": group[0]["l"]})
        merged += 1
    else:
        out.extend(group)
        kept_apart.append((group[0]["t"], sorted(g["l"] for g in group)))

out.sort(key=lambda r: norm(r["t"]))
for r in out:
    r["n"] = norm(r["t"])

payload = {
    "source": "Karolinska Institutet Journal List (KI-JL) 2026",
    "decided": "Faculty Board, 5 May 2026 (Dnr 2-1422/2025)",
    # The normalised form is NOT shipped: recomputing it in the browser costs a
    # few milliseconds once at load and saves about 250 kB on the wire, which
    # matters more for a file people will email to each other.
    "rows": [[r["t"], r["p"], r["d"], r["l"]] + ([r["x"]] if r.get("x") else [])
             for r in out],
}

import os
os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))

from collections import Counter
print(f"rows in sheet   : {len(rows)}")
print(f"entries emitted : {len(out)}  (merged {merged} duplicate pairs)")
print(f"levels          : {dict(sorted(Counter(r['l'] for r in out).items(), reverse=True))}")
print("same title, different level - kept separate:")
for t, ls in kept_apart:
    print(f"   {t!r} -> levels {ls}")
print(f"written         : {OUT}  ({os.path.getsize(OUT)/1024:.0f} kB)")
