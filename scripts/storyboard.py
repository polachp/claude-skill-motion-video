"""Storyboard: frames per section + an HTML page to publish as an artifact.

Usage:   python storyboard.py video.html storyboard.json out_dir/
Output:  out_dir/index.html and out_dir/img/f_<t>.jpg -> publish with publish_files (mode replace,
         same artifact slug, so the link stays the same).

storyboard.json:
{
  "title": "Reel 1: MultiModel – storyboard",
  "subtitle": "9:16, 74 s, burned-in captions",
  "status": "Storyboard for approval, do not render the video yet.",
  "labels": {"learn": "Co se učíme", "motion": "Pohyb a přechod", "sound": "Zvuk", ...},   # optional UI language
  "sections": [
    {"name": "1. Intro", "time": "0–3.5 s",
     "learn": "...", "motion": "...", "sound": "...",
     "items": ["Logo assembles", "Title: ..."],
     "changed": [1],                      # indexes of items marked CHANGED (optional)
     "frames": [[0.7, "logo"], [2.8, "title"]]}
  ]
}
"""
import sys, os, json, html, pathlib
from playwright.sync_api import sync_playwright
from PIL import Image

page, cfg, out = pathlib.Path(sys.argv[1]).resolve(), json.load(open(sys.argv[2], encoding='utf-8')), pathlib.Path(sys.argv[3])
img = out / 'img'; img.mkdir(parents=True, exist_ok=True)
for f in img.glob('*.jpg'):
    f.unlink()
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome')
times = sorted({float(t) for s in cfg['sections'] for t, _ in s['frames']})
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME if os.path.exists(CHROME) else None,
                          args=['--allow-file-access-from-files'])
    pg = b.new_page(); pg.goto(page.as_uri()); pg.wait_for_timeout(800)
    F = pg.evaluate('window.FORMAT || {w:1080,h:1920}'); pg.set_viewport_size({'width': F['w'], 'height': F['h']})
    pg.on('pageerror', lambda e: print('PAGE ERROR', e)); pg.goto(page.as_uri()); pg.wait_for_timeout(800)
    TW = 540 if F['w'] <= F['h'] else 640; TH = round(TW * F['h'] / F['w'])
    for t in times:
        pg.evaluate(f'seek({t})'); pg.evaluate("Promise.all(window.__pending||[]).then(()=>{window.__pending=[]})"); tmp = out / '_tmp.jpg'
        pg.screenshot(path=str(tmp), type='jpeg', quality=92)
        Image.open(tmp).resize((TW, TH)).save(img / f'f_{t}.jpg', quality=86)
    b.close()
(out / '_tmp.jpg').unlink(missing_ok=True)

e = html.escape
L = {'learn': 'What we learn', 'motion': 'Motion and transition', 'sound': 'Sound', 'changed': 'CHANGED',
     'player': 'Preview player', 'player_hint': 'Animation right in the browser, no render. Use the timeline to jump in time.',
     'open_player': 'Open the player on its own', 'zoom_hint': 'Click a frame to enlarge it.'}
L.update(cfg.get('labels', {}))
secs = []
for s in cfg['sections']:
    ch = set(s.get('changed', []))
    items = ''.join(f"<li>{e(it)}{' <span class=new>' + e(L['changed']) + '</span>' if i in ch else ''}</li>" for i, it in enumerate(s['items']))
    extra = ''.join(f"<div class=x><b>{lab}:</b> {e(s[k])}</div>" for k, lab in ((k, e(L[k])) for k in ('learn', 'motion', 'sound')) if s.get(k))
    figs = ''.join(f"<figure><img src='img/f_{float(t)}.jpg'><figcaption>{e(c)}</figcaption></figure>" for t, c in s['frames'])
    secs.append(f"<section><h2>{e(s['name'])}</h2><div class=t>{e(s['time'])}</div>{extra}<ul>{items}</ul><div class=frames>{figs}</div></section>")
player = (f"<div class=player><h2>{e(L['player'])}</h2><div class=t>{e(L['player_hint'])}</div>"
          f"<iframe src='player.html' title='{e(L['player'])}'></iframe><div class=t><a href='player.html' style='color:#FFD24A'>{e(L['open_player'])}</a></div></div>") if (out / 'player.html').exists() else ''
doc = f"""<!DOCTYPE html><html lang="{e(cfg.get('lang', 'en'))}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(cfg['title'])}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&display=swap">
<style>
body{{margin:0;font-family:Outfit,sans-serif;background:#0B2545;color:#fff}}
header{{padding:28px 24px 4px;max-width:1280px;margin:auto}} h1{{font-weight:700;margin:0 0 6px;font-size:30px}}
header p{{margin:0;opacity:.75}} .meta{{margin-top:8px;font-size:14px;opacity:.6}}
section{{max-width:1280px;margin:20px auto;padding:20px 24px;background:#10305a;border-radius:16px}}
h2{{margin:0 0 4px;font-weight:600;font-size:22px}} .t{{font-size:14px;opacity:.65;margin-bottom:10px}}
ul{{margin:6px 0 14px 18px;padding:0;line-height:1.45}}
.new{{display:inline-block;background:#FFD24A;color:#0B2545;font-size:12px;font-weight:700;padding:2px 8px;border-radius:10px;margin-left:8px}}
.x{{font-size:14px;opacity:.85;margin:2px 0}} .x b{{color:#FFD24A;font-weight:600}}
.player{{max-width:1280px;margin:20px auto;padding:16px 24px;background:#10305a;border-radius:16px}}
.player iframe{{width:100%;height:78vh;max-height:900px;border:0;border-radius:12px;background:#0B2545}}
.frames{{display:flex;gap:14px;overflow-x:auto;padding-bottom:6px}} figure{{margin:0;flex:0 0 auto;cursor:zoom-in}}
figure img{{max-height:430px;max-width:420px;border-radius:12px;display:block;box-shadow:0 6px 18px rgba(0,0,0,.35)}}
figcaption{{font-size:13px;opacity:.75;margin-top:6px;max-width:240px}}
#lb{{position:fixed;inset:0;background:rgba(0,0,0,.85);display:none;align-items:center;justify-content:center;cursor:zoom-out}}
#lb img{{max-height:94vh;max-width:94vw;border-radius:14px}}
</style></head><body>
<header><h1>{e(cfg['title'])}</h1><p>{e(cfg.get('subtitle', ''))} {e(L['zoom_hint'])}</p><div class=meta>{e(cfg.get('status', ''))}</div></header>
{player}{''.join(secs)}
<div id=lb><img></div>
<script>const lb=document.getElementById('lb'),li=lb.querySelector('img');
document.querySelectorAll('figure img').forEach(i=>i.addEventListener('click',()=>{{li.src=i.src;lb.style.display='flex'}}));
lb.addEventListener('click',()=>lb.style.display='none');</script></body></html>"""
(out / 'index.html').write_text(doc, encoding='utf-8')
print('->', out / 'index.html', len(times), 'frames')
