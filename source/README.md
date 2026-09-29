# Source material

`kijl_2026.xlsx` is the Karolinska Institutet Journal List 2026 as published on
staff.ki.se. It is the only input to the build: `build/make_data.py` reads the
`journals` sheet (header on row 6) and writes `data/journals.json`.

`KI-JL staff portal page.html` is a saved copy of the staff.ki.se page that
describes the list. It is kept because the level definitions shown by the tool
are quoted from it verbatim rather than paraphrased, and because it records the
decision reference (Faculty Board, 5 May 2026, Dnr 2-1422/2025).

To rebuild against a later edition, drop the new spreadsheet in here and run:

    python build/make_data.py source/<new file>.xlsx
    python build/build.py

Then re-run the tests: the counts in `tests/search.js` and in the page legend
are asserted against the data, so a new edition will fail loudly until both are
updated.
