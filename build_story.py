"""Render the quiz-answer Instagram story for a Lenlab | CS post to a 1080x1920 PNG.

usage: python build_story.py posts/<folder> [--fonts <local font dir>]
Reads posts/<folder>/story.html (one <section class="slide story">), writes <NNN>-story.png.
Uses templates/card-template.html + templates/story.css. Fails on overflow/overlap.
"""
import pathlib, re, sys
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).parent
CHECK_JS = """
() => [...document.querySelectorAll('section.slide')].map((s, i) => {
  const sr = s.getBoundingClientRect(), m = s.querySelector('main'),
        h = s.querySelector('header').getBoundingClientRect(),
        f = s.querySelector('footer').getBoundingClientRect(), errs = [];
  if (Math.round(sr.height) !== 1920) errs.push(`story height is ${sr.height}px, not 1920`);
  if (m.scrollHeight > m.clientHeight + 1) errs.push(`main overflows by ${m.scrollHeight - m.clientHeight}px`);
  for (const el of m.querySelectorAll('*')) {
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    if (r.top < h.bottom - 1 || r.bottom > f.top + 1) { errs.push(`<${el.tagName.toLowerCase()}> "${el.textContent.trim().slice(0,30)}" hits header/footer`); break; }
    if (r.right > sr.right - 79 || r.left < sr.left + 79) { errs.push(`<${el.tagName.toLowerCase()}> "${el.textContent.trim().slice(0,30)}" crosses side margin`); break; }
  }
  return {slide: i + 1, errs};
})
"""

def build(folder, fonts=None):
    folder = (ROOT / folder).resolve()
    tpl = (ROOT / "templates/card-template.html").read_text()
    css = (ROOT / "templates/story.css").read_text()
    logo = re.search(r'<template id="logo">(.*?)</template>', tpl, re.S).group(1)
    body = (folder / "story.html").read_text().replace("{LOGO}", logo)
    html = tpl.replace("</style>", css + "</style>", 1).replace("</body>", body + "</body>")
    if fonts:
        html = html.replace("https://cdn.jsdelivr.net/npm/pretendard@1.3.9/", f"file://{fonts}/pretendard/")
        html = html.replace("https://cdn.jsdelivr.net/npm/@fontsource/jetbrains-mono@5/", f"file://{fonts}/@fontsource/jetbrains-mono/")
        html = html.replace("https://cdn.jsdelivr.net/npm/@fontsource/libre-baskerville@5/", f"file://{fonts}/@fontsource/libre-baskerville/")
    out = folder / "_render_story.html"
    out.write_text(html)
    num = folder.name.split("_")[1]
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto(out.as_uri()); pg.wait_for_timeout(1000)
        problems = [r for r in pg.evaluate(CHECK_JS) if r["errs"]]
        el = pg.query_selector("section.slide")
        el.screenshot(path=str(folder / f"{num}-story.png"))
        b.close()
    out.unlink()
    for p in problems: print("story: " + "; ".join(p["errs"]))
    print("OK — no overlaps" if not problems else "LAYOUT PROBLEMS FOUND")
    return not problems

if __name__ == "__main__":
    a = sys.argv[1:]
    fonts = a[a.index("--fonts") + 1] if "--fonts" in a else None
    sys.exit(0 if build(a[0], fonts) else 1)
