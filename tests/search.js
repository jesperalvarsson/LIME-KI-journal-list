/* Behaviour tests for the shipped lookup page.
   Run from this directory:  node search.js                                  */
require("./domshim.js");
const fs = require("fs");
(0, eval)(fs.readFileSync("page.js", "utf8") +
  "\nglobal.__X = {search, norm, J, AMBIG, digits};");
const { search, J, AMBIG } = global.__X;

let pass = 0, fail = 0;
function t(name, fn){
  let ok = false, why = "";
  try { const r = fn(); ok = r === true; if(!ok) why = String(r); }
  catch(e){ why = e.message; }
  if(ok){ pass++; } else { fail++; console.log("  FAIL  " + name + "\n         " + why); }
}
const top  = q => (search(q).hits[0] || {}).t;
const lvl  = q => (search(q).hits[0] || {}).l;
const n    = q => search(q).hits.length;

console.log("corpus:", J.length, "journals;", AMBIG.size, "ambiguous titles\n");

/* --- the list loaded at all ------------------------------------------- */
t("6,855 entries", () => J.length === 6855 || J.length);
t("142 at level 3", () => J.filter(j=>j.l===3).length === 142 || J.filter(j=>j.l===3).length);
t("955 at level 0", () => J.filter(j=>j.l===0).length === 955 || J.filter(j=>j.l===0).length);

/* --- exact and partial titles ------------------------------------------ */
t("exact: 'ACS nano' -> 3",            () => lvl("ACS nano") === 3 || `${top("ACS nano")}=${lvl("ACS nano")}`);
t("case-insensitive: 'acs NANO'",      () => lvl("acs NANO") === 3 || lvl("acs NANO"));
t("exact beats substring: 'Lancet'",   () => top("Lancet") === "Lancet" || top("Lancet"));
t("partial: 'bmj open' finds it",      () => /^BMJ open/i.test(top("bmj open")||"") || top("bmj open"));
t("empty query -> no hits",            () => n("") === 0 || n(""));
t("whitespace only -> no hits",        () => n("   ") === 0 || n("   "));

/* --- ISSN -------------------------------------------------------------- */
const lancet = J.find(j => j.t === "Lancet");
t("ISSN with hyphen",    () => top(lancet.p) === "Lancet" || `${lancet.p} -> ${top(lancet.p)}`);
t("ISSN without hyphen", () => top(lancet.p.replace("-","")) === "Lancet" || top(lancet.p.replace("-","")));
t("online ISSN too",     () => top(lancet.d) === "Lancet" || `${lancet.d} -> ${top(lancet.d)}`);
t("ISSN mode is exact",  () => search(lancet.p).mode === "issn" || search(lancet.p).mode);
t("unknown ISSN -> none",() => n("9999-9999") === 0 || n("9999-9999"));

/* --- diacritics and punctuation ---------------------------------------- */
const acc = J.find(j => /[À-ɏ]/.test(j.t));
t("diacritics fold: " + (acc ? acc.t.slice(0,34) : "-"),
  () => !acc || search(acc.t.normalize("NFKD").replace(/[̀-ͯ]/g,"")).hits.some(h=>h.t===acc.t) || "not found");
const punc = J.find(j => j.t.includes(":"));
t("punctuation ignored: " + (punc ? punc.t.slice(0,30) : "-"),
  () => !punc || search(punc.t.replace(/[:.]/g," ")).hits.some(h=>h.t===punc.t) || "not found");

/* --- typos ------------------------------------------------------------- */
t("typo 'Lancett'",        () => (search("Lancett").hits[0]||{}).t === "Lancet" || top("Lancett"));
t("typo 'Naure'",          () => (search("Naure").hits.slice(0,5)).some(h=>h.t==="Nature") || search("Naure").hits.slice(0,3).map(h=>h.t).join("|"));
t("typo flagged as fuzzy", () => search("Lancett").fuzzyOnly === true || String(search("Lancett").fuzzyOnly));
t("exact NOT flagged fuzzy",() => search("Lancet").fuzzyOnly === false || String(search("Lancet").fuzzyOnly));
t("gibberish -> nothing",  () => n("qxzptwvb") === 0 || `${n("qxzptwvb")}: ${top("qxzptwvb")}`);

/* --- the four ambiguous titles ----------------------------------------- */
for(const [title, levels] of [["Omega",[1,2]], ["Surgery",[0,2]],
                              ["Medicina",[0,1]], ["Revista de psiquiatria y salud mental",[0,1]]]){
  t(`ambiguous '${title}' -> levels ${levels.join("/")}`, () => {
    const hits = search(title).hits.filter(h => h.n === require("./domshim.js") || true);
    const exact = search(title).hits.filter(h => h.t.toLowerCase() === title.toLowerCase());
    const got = [...new Set(exact.map(h => h.l))].sort();
    return JSON.stringify(got) === JSON.stringify(levels) || `got ${JSON.stringify(got)}`;
  });
  t(`'${title}' marked ambiguous`, () => {
    const j = search(title).hits[0];
    return AMBIG.has(j.n) === true || `${j.t} n=${j.n}`;
  });
}
/* A journal whose title is unique must NOT be flagged */
t("'Lancet' not flagged ambiguous", () => AMBIG.has(search("Lancet").hits[0].n) === false || "flagged");

/* --- genuinely absent journals ------------------------------------------
   The whole point of the tool is that "not on the list" is a real answer, so
   an invented title must return nothing rather than the nearest thing sharing
   boilerplate. These titles are built out of ordinary journal words on purpose
   - they are the cases a loose fuzzy match gets wrong. */
for(const q of ["Journal of Imaginary Studies", "Journal of Invented Medicine",
                "Nordic Journal of Nothing", "International Journal of Fabrication",
                "Annals of Nowhere", "Review of Unreal Biology",
                "Scandinavian Journal of Make Believe", "Acta Fictiva"])
  t(`absent: ${q} -> no hits`, () => n(q) === 0 || top(q));

/* --- typo tolerance must survive the tightening above -------------------- */
for(const [q, want] of [["Lancett","Lancet"], ["Naure","Nature"], ["Lanct","Lancet"],
                        ["BMJ Opne","BMJ open"], ["Plos medicin","PLoS medicine"],
                        ["Jorunal of affective disorders","Journal of affective disorders"],
                        ["Sucide and life threatening behavior","Suicide & life-threatening behavior"],
                        ["Acta psychiatrica scandinavia","Acta psychiatrica Scandinavica"]])
  t(`typo: ${q} -> ${want}`, () => top(q) === want || `got ${top(q)}`);

/* A near-miss on a short name must not be forgiven: one edit is the entire
   difference between two real publishers. */
t("BMC is not a typo for BMJ", () => {
  const h = search("BMJ").hits.map(x => x.t);
  return !h.some(x => /^BMC/i.test(x)) || "BMC in BMJ hits";
});

/* --- the approximate path must stay usable while typing ------------------ */
t("worst-case fuzzy query under 60 ms", () => {
  const t0 = Date.now();
  for(const q of ["Journal of Imaginary Studies","International Journal of Fabrication","Naure"]) search(q);
  const ms = (Date.now() - t0) / 3;
  return ms < 60 || `${ms.toFixed(0)} ms`;
});

/* --- ordering ----------------------------------------------------------- */
t("prefix ranks above mid-string", () => {
  const h = search("nature").hits.slice(0, 12).map(x => x.t);
  const first = h.findIndex(x => /^Nature/i.test(x));
  const mid   = h.findIndex(x => !/^Nature/i.test(x));
  return (mid === -1 || first < mid) || h.join(" | ");
});

/* --- every level renders a defined meaning ------------------------------ */
t("every level in 0..3", () => J.every(j => [0,1,2,3].includes(j.l)) || "stray level");
t("every entry has a title", () => J.every(j => j.t && j.t.length) || "blank title");
t("every entry has >=1 ISSN", () => J.every(j => j.k.size >= 1) || J.filter(j=>!j.k.size).length + " without");

/* --- a journal must not lose its own name to a lookalike ----------------
   The list is catalogued library-style, so a journal's own name is followed by
   a colon and a descriptive subtitle. Matching the whole string and nothing
   else meant the level 3 Journal of clinical oncology, which carries a long
   subtitle, lost the tiebreak on title length to a level 0 journal called
   "Journal of clinical oncology and research". Reporting a level 3 journal as
   level 0 is the worst answer this page can give, so these are pinned. */
t("exact name beats a longer-named lookalike", () =>
  /^Journal of clinical oncology :/.test(top("Journal of clinical oncology")) ||
  top("Journal of clinical oncology"));
t("...and still does through a typo", () =>
  /^Journal of clinical oncology :/.test(top("Jorunal of Clinical Oncology")) ||
  top("Jorunal of Clinical Oncology"));
t("a subtitled journal answers to its own name", () =>
  /^Academic medicine :/.test(top("Academic medicine")) || top("Academic medicine"));
t("a parallel-language name is searchable", () =>
  /Angiology and vascular surgery/.test(top("Angiology and vascular surgery") || "") ||
  top("Angiology and vascular surgery"));

/* A one-letter tail is a series designator, not a subtitle: the ": X" journals
   are separate companion titles, sometimes a level below their parent, and must
   not be able to claim the parent's name. */
for(const [q, want] of [["Journal of biomedical informatics", 2],
                        ["International journal of pharmaceutics", 2],
                        ["Veterinary parasitology", 2]])
  t(`"${q}" is not answered by its ": X" companion`, () =>
    (top(q) === q && lvl(q) === want) || `${top(q)} (level ${lvl(q)})`);
t("a series designator stays part of the name", () =>
  top("Acta physica Polonica: B") === "Acta physica Polonica: B" ||
  top("Acta physica Polonica: B"));

t("every subtitled journal wins its own name", () => {
  const bad = [];
  for(const j of J.filter(x => x.a.length > 1)){
    const nm = j.a[1], h = search(nm).hits;
    if(!h.length || (h[0].t !== j.t && !h[0].a.includes(nm))) bad.push(j.t);
  }
  return bad.length === 0 || `${bad.length} lost: ${bad.slice(0, 3).join(" | ")}`;
});

/* Sampled rather than exhaustive: all 6,855 take about a hundred seconds, and
   the full sweep is worth running by hand after a change to the scoring. */
t("a journal searched by its full title ranks first (every 23rd)", () => {
  const bad = [];
  for(let i = 0; i < J.length; i += 23){
    const h = search(J[i].t).hits;
    if(!h.length || (h[0].t !== J[i].t && h[0].n !== J[i].n)) bad.push(J[i].t);
  }
  return bad.length === 0 || `${bad.length} lost: ${bad.slice(0, 3).join(" | ")}`;
});

/* --- names shared across levels are never answered with one number ------ */
t("Alzheimer's & dementia is flagged, not answered", () => {
  const g = AMBIG.get("alzheimer s and dementia");
  return (g && g.length === 3 && new Set(g.map(x => x.l)).size === 3) ||
    "the three sibling journals are not grouped";
});
t("no name is left claimed by two levels", () => {
  const by = new Map();
  for(const j of J) for(const nm of j.a) (by.get(nm) || by.set(nm, []).get(nm)).push(j);
  const loose = [...by].filter(([nm, g]) =>
    new Set(g.map(x => x.t)).size > 1 && new Set(g.map(x => x.l)).size > 1 && !AMBIG.has(nm));
  return loose.length === 0 || loose.map(x => x[0]).join(" | ");
});

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
