"""Automatická kontrola videa před renderem.

Použití:  python check.py video.html [--step 0.5] [--dead 3] [--safe 180,60,420,60]
Hlídá:
  - text mimo bezpečnou zónu (okraje top,right,bottom,left v px návrhového rozlišení; výchozí podle formátu:
    9:16 = 200,60,380,60 kvůli UI Reels/Shorts (orientační, upravit dle platformy), 16:9 = 54,96,54,96, 1:1 = 54,54,54,54)
  - text přetékající přes kontejner nebo mimo obraz
  - nízký kontrast textu proti pozadí (WCAG poměr < 3 pro velký text, < 4.5 pro malý)
  - hluchá místa: úseky delší než --dead s, kde se obraz skoro nemění
Výstup: seznam nálezů s časem a scénou. Návratový kód 1, pokud něco našel.
"""
import sys, os, json, argparse, pathlib, io
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops, ImageStat

ap = argparse.ArgumentParser()
ap.add_argument('html'); ap.add_argument('--step', type=float, default=0.5)
ap.add_argument('--dead', type=float, default=3.0); ap.add_argument('--safe')
a = ap.parse_args()
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome')

JS = r"""(safe)=>{const W=innerWidth,H=innerHeight,res=[];
function vis(el){let o=1;for(let e=el;e&&e.nodeType===1;e=e.parentElement){const cs=getComputedStyle(e);if(cs.display==='none'||cs.visibility==='hidden')return 0;o*=+cs.opacity}return o}
const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;
while(n=walker.nextNode()){const t=n.textContent.trim();if(!t)continue;const el=n.parentElement;if(vis(el)<0.6)continue;
 const rg=document.createRange();rg.selectNodeContents(n);const r=rg.getBoundingClientRect();if(r.width<2||r.height<2)continue;
 const cs=getComputedStyle(el);const fs=parseFloat(cs.fontSize),fw=+cs.fontWeight||400;
 const issues=[];
 if(r.left<0||r.top<0||r.right>W||r.bottom>H)issues.push('mimo obraz');
 else if(r.top<safe[0]||r.right>W-safe[1]||r.bottom>H-safe[2]||r.left<safe[3])issues.push('mimo bezpečnou zónu');
 if(el.scrollWidth>el.clientWidth+2&&cs.overflow!=='visible')issues.push('přetéká');
 const col=(el instanceof SVGElement&&cs.fill&&cs.fill.startsWith('rgb'))?cs.fill:cs.color;
 res.push({t:t.slice(0,60),x:r.left,y:r.top,w:r.width,h:r.height,color:col,large:fs>=24||(fs>=18.6&&fw>=700),issues})}
return res}"""


def lum(c):
    c = [v / 255 for v in c[:3]]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def parse_rgb(s):
    s = s[s.index('(') + 1:s.index(')')].split(',')
    return [float(v) for v in s[:3]]


with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None, args=['--allow-file-access-from-files'])
    pg0 = b.new_page(); pg0.goto(pathlib.Path(a.html).resolve().as_uri()); pg0.wait_for_timeout(800)
    T = pg0.evaluate('window.T'); F = pg0.evaluate('window.FORMAT || {w:1080,h:1920}'); pg0.close()
    W, H = F['w'], F['h']
    if a.safe:
        safe = [int(v) for v in a.safe.split(',')]
    else:
        r = W / H
        safe = [200, 60, 380, 60] if r < 0.8 else ([54, 96, 54, 96] if r > 1.2 else [54, 54, 54, 54])
    pg = b.new_page(viewport={'width': W, 'height': H})
    pg.goto(pathlib.Path(a.html).resolve().as_uri()); pg.wait_for_timeout(800)
    END = max(v[1] for v in T.values())
    scene = lambda t: next((k for k, v in T.items() if v[0] <= t < v[1]), list(T)[-1])
    found, seen, prev, still = [], set(), None, 0.0
    t = 0.0
    while t <= END:
        pg.evaluate(f'seek({t})')
        img = Image.open(io.BytesIO(pg.screenshot(type='png'))).convert('RGB')
        for it in pg.evaluate(JS, safe):
            box = (max(0, int(it['x'])), max(0, int(it['y'])), min(W, int(it['x'] + it['w'])), min(H, int(it['y'] + it['h'])))
            iss = list(it['issues'])
            if box[2] > box[0] and box[3] > box[1]:
                bg = ImageStat.Stat(img.crop((max(0, box[0] - 6), max(0, box[1] - 6), min(W, box[2] + 6), min(H, box[3] + 6)))).median
                l1, l2 = lum(parse_rgb(it['color'])), lum(bg)
                cr = (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)
                if cr < (3 if it['large'] else 4.5):
                    iss.append(f'nízký kontrast {cr:.1f}:1')
            for i in iss:
                key = (it['t'], i.split(' ')[0], scene(t))
                if key not in seen:
                    seen.add(key); found.append(f"{t:6.1f} s  [{scene(t)}]  {i}: „{it['t']}“")
        small = img.resize((W // 8, H // 8))
        if prev is not None:
            diff = ImageStat.Stat(ImageChops.difference(small, prev)).mean
            if sum(diff) / 3 < 0.6:
                still += a.step
            else:
                if still >= a.dead:
                    found.append(f"{t - still:6.1f} s  [{scene(t - still)}]  hluché místo {still:.1f} s bez změny")
                still = 0.0
        prev = small
        t = round(t + a.step, 3)
    if still >= a.dead:
        found.append(f"{END - still:6.1f} s  [{scene(END - still)}]  hluché místo {still:.1f} s bez změny (konec)")
    b.close()

print(f'Formát {W}x{H}, bezpečná zóna (top,right,bottom,left) = {safe}, krok {a.step} s')
print('\n'.join(found) if found else 'Bez nálezů.')
sys.exit(1 if found else 0)
