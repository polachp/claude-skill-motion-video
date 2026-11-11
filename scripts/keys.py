"""Klíčové snímky z HTML timeline (kontrola stylu, storyboard).

Použití:  python keys.py reel.html out_dir 0.7 8.5 31.5 ...
Uloží out_dir/k_<t>.jpg (1080x1920) a out_dir/contact.jpg (náhledy vedle sebe).
"""
import sys, os, pathlib
from playwright.sync_api import sync_playwright
from PIL import Image

html = pathlib.Path(sys.argv[1]).resolve()
out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
ts = [float(x) for x in sys.argv[3:]]
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome')
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None,
                          args=['--allow-file-access-from-files'])
    pg = b.new_page(); pg.goto(html.as_uri()); pg.wait_for_timeout(800)
    F = pg.evaluate('window.FORMAT || {w:1080,h:1920}'); pg.set_viewport_size({'width': F['w'], 'height': F['h']})
    pg.on('pageerror', lambda e: print('PAGE ERROR', e)); pg.goto(html.as_uri()); pg.wait_for_timeout(800)
    files = []
    for t in ts:
        pg.evaluate(f'seek({t})'); f = out / f'k_{t}.jpg'
        pg.screenshot(path=str(f), type='jpeg', quality=90); files.append(f)
    b.close()
tw, th = (540, round(540 * F['h'] / F['w'])) if F['h'] <= F['w'] else (round(960 * F['w'] / F['h']), 960)
S = Image.new('RGB', ((tw + 10) * len(files), th), 'white')
for i, f in enumerate(files):
    S.paste(Image.open(f).resize((tw, th)), (i * (tw + 10), 0))
S.save(out / 'contact.jpg'); print('->', out / 'contact.jpg')
