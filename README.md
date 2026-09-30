# KI Journal List lookup

A single HTML file that answers one question: is this journal level 3, 2, 1, 0,
or not on the Karolinska Institutet Journal List at all? Built from the KI-JL
2026 spreadsheet (6,855 journals, decided by the Faculty Board 5 May 2026,
Dnr 2-1422/2025).

Live at <https://jesperalvarsson.github.io/LIME-KI-journal-list/>

Or open `dist/ki-journal-list.html` in any browser. It needs no server, no
network and no install; the data and the font are inside the file, so it can be
emailed or put on a shared drive and it will still work offline.

## Build

    python build/make_data.py     # kijl_2026.xlsx -> data/journals.json
    python build/build.py         # template + data + font -> dist/ and index.html

The build writes the same bytes twice: `dist/ki-journal-list.html`, whose name
is worth emailing, and `index.html` at the root, which is what GitHub Pages
serves from the short URL. They are written from one string and compared after
writing, so they cannot drift; git stores identical content once, so the second
path costs nothing in the history. Do not edit either by hand — edit
`build/template.html` and rebuild.

`.nojekyll` stops GitHub Pages from running the files through Jekyll, which
would otherwise try to interpret parts of the repository as a site.

## Test

    cd tests && node extract.js ../dist/ki-journal-list.html page.js
    node search.js                # 64 assertions against the shipped file
    node probe.js                 # fuzzy-match separation, for tuning
    python ../tests/contrast.py   # WCAG AA, both themes
    cd .. && python tests/shots.py   # renders every state, both themes

`extract.js` pulls the script out of the built file rather than the template, so
the tests cannot pass against a version that was never shipped.

## Browsing and the level filters

The whole list sits under the search box, sorted by title, so the page is useful
before anyone types and a researcher can scan for a title they cannot quite
spell. Typing filters it; clearing the box brings it back. The rows arrive 150 at
a time as you scroll, because putting 6,855 of them in the document at once makes
scrolling stutter on an ordinary laptop.

The four levels are toggles, all on to begin with. Switching one off takes those
journals out of the list. Two decisions there are deliberate and should survive
future edits:

The filter never touches the verdict. Search for a level 0 journal with level 0
switched off and the card still says level 0, with the list beneath it noting how
many matches the filter is hiding. A filter that could silence the level 0
warning would be worse than no filter at all.

The filter is not remembered between visits. A toggle still set from last week
would quietly drop journals from the list, and "I could not find it" reads as "it
is not on the list" - the one wrong answer this page must never give. Every visit
starts showing everything.

## Three answers, not two

A level is not the only outcome. **Level 0** means KI grades the journal as not
meeting the criteria for scientific publishing - a caution, not a low rank.
**Not listed** means the journal is absent from the list, which is not a
judgement: the list covers journals in KI's bibliometric system and the Nordic
registers, so a journal can be missing simply because nobody at KI has published
there yet. The page says so explicitly rather than leaving a blank result to be
read as disapproval.

## Titles that name more than one journal

Four titles in the 2026 list belong to two different journals at two different
levels: *Omega* (1 and 2), *Surgery* (2 and 0), *Medicina* (1 and 0) and
*Revista de psiquiatria y salud mental* (1 and 0). For these the page shows no
headline level at all and lists the candidates with their ISSNs, because
answering "Surgery" with a single number would be confidently wrong half the
time - and in that particular case the two answers are "high standard" and "does
not fulfil the criteria".

A fifth name does the same thing one level down. Three journals are called
*Alzheimer's & dementia* and differ only after the colon: *the journal of the
Alzheimer's Association* is level 3, *diagnosis, assessment & disease
monitoring* is level 2 and *translational research & clinical interventions* is
level 1. Grouping on the full title misses this, so the page groups on every
name a journal goes by, and the card lists the three subtitles rather than the
three ISSNs, because the subtitle is what the reader has to choose on.

## A journal's own name

The titles follow library cataloguing convention, and two punctuation marks in
them carry meaning. A colon separates the journal's own name from a descriptive
subtitle, as in "Journal of clinical oncology : official journal of the American
Society of Clinical Oncology" (847 titles). An equals sign separates parallel
names for one journal in two languages, as in "Advances in gerontology = Uspekhi
gerontologii" (73 titles). Each name a journal genuinely goes by is matched
separately, and ties are broken on the length of the shortest of them.

This is not cosmetic. Matching the whole string and nothing else meant that
searching *Journal of clinical oncology* - the exact name of a level 3 journal -
answered with a level 0 journal called "Journal of clinical oncology and
research", because the level 0 title is shorter and so won the tiebreak. Calling
a level 3 journal level 0 is the worst mistake this page can make.

One exception: a single-letter tail after the colon is a series designator and
belongs to the name. "International journal of pharmaceutics: X" is a separate
companion journal, a level below its parent, and must not be able to claim the
parent's name. A longer tail is a subtitle or the journal's own acronym.
`tests/search.js` sweeps all 910 subtitled and parallel-named journals to check
each one still wins its own name, and asserts that no name is left claimed by
two different levels without being flagged.

## Approximate matching

Typing is imperfect, so the page falls back to fuzzy matching when little else
lands. Whole-string similarity does not work on journal titles: so much of the
corpus is "International Journal of ..." that an invented title scores higher
against real ones than a genuine misspelling does against its own journal.
Measured on the two sets, the ranges overlapped completely (real typos
0.667-0.958, invented journals 0.625-0.873), so no threshold could separate
them.

What works is scoring word by word, weighting each word by how rare it is in the
corpus, aligning the query to a contiguous run of the title, and capping the
edit distance per word absolutely rather than as a ratio. "Journal" and "of"
then count for almost nothing and the distinctive word decides. The same two
sets now sit at 0.833-0.966 and 0.304-0.512, and the threshold (0.72) sits below
the lowest score an all-words-matched query can produce.

Run `tests/probe.js` after any change to that code and check the two ranges
still separate.

## Caveat

This is a lookup over the published spreadsheet, not an official KI service.
Where the two differ, the spreadsheet on staff.ki.se is what counts.

## Screenshots

`shots/` holds twelve rendered states in both themes: the list as it opens, the
list scrolled, the list with levels 1 and 0 switched off, a level 0 journal found
while level 0 is hidden, the reset, a level 3 verdict, a level 0 caution, a
shared name, a shared title, a not-listed result, a corrected typo and an ISSN
lookup. Regenerate them with

    python tests/shots.py

which also fails if the page logs a console error or if the level filter ever
suppresses a level 0 verdict.
