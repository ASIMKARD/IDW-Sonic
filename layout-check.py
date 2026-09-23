"""Layout regression check in real Chromium (jsdom has no layout engine).
Run from the repo root:  python3 layout-check.py
Asserts the sticky stack and band spacing that jsdom cannot see."""
import asyncio, subprocess, sys, time
from playwright.async_api import async_playwright
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8765'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.2)
fails = []
def ok(name, cond):
    print(('ok   ' if cond else 'FAIL ') + name)
    if not cond: fails.append(name)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': 390, 'height': 844})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_timeout(900)
        await pg.evaluate("document.getElementById('bannerChip').click()")
        await pg.evaluate("window.scrollTo(0, 700)"); await pg.wait_for_timeout(400)
        m = await pg.evaluate("""() => { const g = s => { const e = document.querySelector(s);
            const r = e.getBoundingClientRect(); return {top:r.top, bottom:r.bottom, pos:getComputedStyle(e).position}; };
            return {tabs:g('#tabs'), banner:g('#banner'), phead:g('.period-head'), pintro:g('.period-intro')}; }""")
        ok('tabs are sticky', m['tabs']['pos'] == 'sticky')
        ok('tabs pinned to the top after scrolling', abs(m['tabs']['top']) < 1)
        ok('banner is sticky', m['banner']['pos'] == 'sticky')
        ok('banner sits directly under the tabs', abs(m['banner']['top'] - m['tabs']['bottom']) < 2)
        ok('band is not shifted onto its own intro', m['pintro']['top'] >= m['phead']['bottom'] - 1)
        await pg.evaluate("""()=>{const b=[...document.querySelectorAll('button')].find(x=>/Collapse all/i.test(x.textContent)); b&&b.click();
            document.querySelectorAll('.period-head').forEach(h=>{const n=h.nextElementSibling; if(n&&n.hidden) h.click();});}""")
        await pg.wait_for_timeout(300)
        gaps = await pg.evaluate("""()=>{const ps=[...document.querySelectorAll('.period')];
            return ps.slice(0,-1).map((p,i)=>Math.round(ps[i+1].getBoundingClientRect().top - p.getBoundingClientRect().bottom));}""")
        ok('no large gap between bands (max %dpx)' % max(gaps), max(gaps) <= 16)
        # table view must actually compact the list, not just trim padding
        await pg.evaluate("""()=>{document.querySelectorAll('.period-head').forEach(h=>{const n=h.nextElementSibling;if(n&&n.hidden)h.click()});
            document.querySelectorAll('.era-head').forEach(h=>{const n=h.nextElementSibling;if(n&&n.hidden)h.click()});}""")
        await pg.wait_for_timeout(200)
        normal = await pg.evaluate("()=>Math.round(document.querySelector('.row:not(.gap)').getBoundingClientRect().height)")
        await pg.evaluate("document.getElementById('tableChip').click()"); await pg.wait_for_timeout(300)
        table = await pg.evaluate("()=>Math.round(document.querySelector('.row:not(.gap)').getBoundingClientRect().height)")
        wide = await pg.evaluate("()=>[...document.querySelectorAll('.row:not(.gap)')].slice(0,40).filter(r=>r.scrollWidth>r.clientWidth+1).length")
        ok('table view at least halves row height (%dpx -> %dpx)' % (normal, table), table <= normal / 2)
        ok('no table row overflows the screen width', wide == 0)
        await pg.evaluate("document.getElementById('tableChip').click()")
        ok('no runtime errors', not errs)
        await b.close()
try: asyncio.run(main())
finally: srv.terminate()
print('\n%d failure(s)' % len(fails)); sys.exit(1 if fails else 0)
