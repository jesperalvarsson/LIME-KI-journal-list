"""Render every state of the page in both themes into shots/.

    cd .. && python tests/shots.py

Kept in the repository because the states are easy to break silently: the level
filter must never change the verdict, and a shared name must never be answered
with one number.  The script also fails loudly on any console error.
"""
import asyncio, pathlib, sys
from playwright.async_api import async_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / "dist" / "ki-journal-list.html").as_uri()
OUT = ROOT / "shots"


async def main():
    OUT.mkdir(exist_ok=True)
    errs = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for theme in ("light", "dark"):
            pg = await b.new_page(viewport={"width": 1100, "height": 950},
                                  color_scheme=theme)
            pg.on("console", lambda m: m.type == "error" and errs.append(m.text))
            pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(URL)
            await pg.wait_for_timeout(900)

            async def shot(name, note=""):
                await pg.screenshot(path=str(OUT / f"{theme}-{name}.png"))
                count = await pg.inner_text("#count")
                rows = await pg.eval_on_selector_all("#list .row", "e => e.length")
                print(f"{theme:5} {name:24} rows={rows:4}  {count[:60]:60} {note}")

            async def find(q, name, note=""):
                await pg.fill("#q", q)
                await pg.wait_for_timeout(450)
                await pg.evaluate("window.scrollTo(0,0)")
                await shot(name, note)

            # A chip in the legend must use the same ink as a bare chip. A CSS
            # rule for the legend's text once outranked the level colours - one
            # class plus an element beats one class - and left a dark digit on a
            # dark square in light mode, which is invisible rather than merely
            # ugly, so it is worth a check rather than an eye.
            for lv in (3, 2, 1, 0):
                same = await pg.evaluate(
                    """lv => {
                         const p = document.createElement("span");
                         p.className = "chip lv" + lv;
                         document.body.appendChild(p);
                         const want = getComputedStyle(p).color;
                         p.remove();
                         const c = document.querySelector(".lg .chip.lv" + lv);
                         return [want, getComputedStyle(c).color];
                       }""", lv)
                if same[0] != same[1]:
                    errs.append(f"legend chip {lv} ink {same[1]} != {same[0]} ({theme})")

            # the whole list, before anyone types
            await shot("01-browse")
            for _ in range(4):
                await pg.mouse.wheel(0, 4000)
                await pg.wait_for_timeout(250)
            await shot("02-browse-scrolled")
            await pg.evaluate("window.scrollTo(0,0)")

            # levels 1 and 0 switched off
            await pg.click('button.lg[data-lv="1"]')
            await pg.click('button.lg[data-lv="0"]')
            await pg.wait_for_timeout(350)
            await shot("03-filtered-32")

            # a level 0 journal searched WHILE level 0 is hidden: the filter
            # narrows the list, so the verdict has to answer anyway
            await pg.fill("#q", "Psychology")
            await pg.wait_for_timeout(450)
            v = (await pg.inner_text("#vcard")).split("\n")
            await shot("04-level0-while-hidden", "| verdict: " + " / ".join(x for x in v[:3] if x))
            if "Level 0" not in " ".join(v):
                errs.append("level 0 verdict suppressed by the level filter")

            await pg.click("#reset")
            await pg.wait_for_timeout(350)
            await shot("05-reset")

            await find("Lancet", "06-level3")
            await find("Psychology", "07-level0")
            await find("Alzheimer's & dementia", "08-shared-name")
            await find("Surgery", "09-shared-title")
            await find("Journal of Imaginary Studies", "10-not-listed")
            await find("New Englnad journal of medicine", "11-typo")
            await find("0140-6736", "12-issn")

            # level order, browsing and within a search
            await pg.fill("#q", "")
            await pg.wait_for_timeout(300)
            await pg.click('button.sb[data-sort="level"]')
            await pg.wait_for_timeout(350)
            await pg.evaluate("window.scrollTo(0,0)")
            await shot("13-by-level")
            tops = await pg.eval_on_selector_all("#list .chip", "e => e.map(x => x.textContent)")
            if tops[:8] != ["3"] * 8:
                errs.append(f"level sort does not lead with 3s: {tops[:8]}")
            await find("oncology", "14-by-level-search")
            await pg.click('button.sb[data-sort="title"]')
            await pg.wait_for_timeout(300)
            await pg.close()
        await b.close()
    print("\nconsole errors:", errs or "none")
    return 1 if errs else 0


sys.exit(asyncio.run(main()))
