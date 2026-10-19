"""Render a Lenlab | CS post to 1080x1350 PNGs.

usage: python build.py posts/<folder> [--fonts <local font dir>]
Fails if any element overflows its slide or overlaps the header/footer.
"""
import pathlib, re, sys
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).parent
CHECK_JS = """
() => [...document.querySelectorAll('section.slide')].map((s, i) => {
  const sr = s.getBoundingClientRect(), m = s.querySelector('main'),
        h = s.querySelector('header').getBoundingClientRect(),
        f = s.querySelector('footer').getBoundingClientRect(), errs = [];
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
    logo = re.search(r'<template id="logo">(.*?)</template>', tpl, re.S).group(1)
    body = (folder / "slides.html").read_text().replace("{LOGO}", logo)
    html = tpl.replace("</body>", body + "</body>")
    if fonts:  # use local copies of the npm fonts instead of the CDN
        html = html.replace("https://cdn.jsdelivr.net/npm/pretendard@1.3.9/", f"file://{fonts}/pretendard/")
        html = html.replace("https://cdn.jsdelivr.net/npm/@fontsource/jetbrains-mono@5/", f"file://{fonts}/@fontsource/jetbrains-mono/")
        html = html.replace("https://cdn.jsdelivr.net/npm/@fontsource/libre-baskerville@5/", f"file://{fonts}/@fontsource/libre-baskerville/")
    out = folder / "_render.html"
    out.write_text(html)
    num = folder.name.split("_")[1]
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        pg.goto(out.as_uri()); pg.wait_for_timeout(1000)
        problems = [r for r in pg.evaluate(CHECK_JS) if r["errs"]]
        for i, el in enumerate(pg.query_selector_all("section.slide"), 1):
            el.screenshot(path=str(folder / f"{num}-{i:02d}.png"))
        b.close()
    out.unlink()
    for p in problems: print(f"slide {p['slide']}: " + "; ".join(p["errs"]))
    print("OK — no overlaps" if not problems else "LAYOUT PROBLEMS FOUND")
    return not problems

if __name__ == "__main__":
    a = sys.argv[1:]
    fonts = a[a.index("--fonts") + 1] if "--fonts" in a else None
    sys.exit(0 if build(a[0], fonts) else 1)
