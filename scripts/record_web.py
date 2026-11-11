"""Live web recording (inspired by Argo): Playwright walks a page step by step, with cursor, highlight and zoom.

Run it on a machine that can reach the web (Claude Code on Petr's PC), not in the cloud sandbox.

Usage:   python record_web.py steps.json out_dir/ [--width 1280 --height 800] [--scale 2] [--headed]
Output:  out_dir/web.mp4 (H.264, 30 fps), out_dir/marks.json (time of each step in s)

steps.json:
{
  "url": "https://www.meteoblue.com/...",
  "steps": [
    {"do": "wait", "s": 1.5},
    {"do": "click", "sel": "input[type=search]", "note": "search"},
    {"do": "type", "text": "Raná", "delay": 120},
    {"do": "wait", "s": 1.2},
    {"do": "spot", "sel": "text=Ústecký", "s": 1.5},          # frame + dim the rest
    {"do": "click", "sel": "text=Ústecký"},
    {"do": "zoom", "sel": "#chart", "k": 1.8, "s": 2.0},       # smooth zoom to an element
    {"do": "unzoom", "s": 0.8},
    {"do": "scroll", "y": 600, "s": 1.0},
    {"do": "hover", "sel": "text=MultiModel"},
    {"do": "mark", "name": "end"}
  ]
}
The cursor always glides to the target and shows a ripple on click. Highlight color --accent (default #FFD24A).
In video.html, put web.mp4 in a <video> and move it with vseek() from the template (deterministic for render).
Cookie banners: add a step {"do": "click", "sel": "text=Reject"} (choose the most privacy-friendly option).
"""
import json, argparse, pathlib, subprocess, time, shutil, os
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument('steps'); ap.add_argument('out')
ap.add_argument('--width', type=int, default=1280); ap.add_argument('--height', type=int, default=800)
ap.add_argument('--scale', type=float, default=2.0); ap.add_argument('--headed', action='store_true')
ap.add_argument('--accent', default='#FFD24A')
a = ap.parse_args()
cfg = json.load(open(a.steps, encoding='utf-8')); out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
vdir = out / '_rec'; shutil.rmtree(vdir, ignore_errors=True)

OVERLAY = """(acc)=>{if(window.__mv)return;window.__mv=1;const d=document.createElement('div');d.id='__cur';
d.style.cssText='position:fixed;left:-50px;top:-50px;width:22px;height:22px;z-index:2147483647;pointer-events:none;transition:none';
d.innerHTML='<svg width=22 height=22 viewBox="0 0 22 22"><path d="M2 2 L2 18 L7 13 L10.5 20.5 L13.5 19 L10 12 L17 12 Z" fill="#fff" stroke="#111" stroke-width="1.5"/></svg>';
document.documentElement.appendChild(d);const s=document.createElement('div');s.id='__spot';
s.style.cssText='position:fixed;z-index:2147483646;pointer-events:none;border:4px solid '+acc+';border-radius:10px;box-shadow:0 0 0 9999px rgba(0,0,0,.45),0 0 24px '+acc+';opacity:0;transition:all .35s ease';
document.documentElement.appendChild(s);window.__curXY=[-50,-50];}"""


def ensure(pg):
    pg.evaluate(OVERLAY, a.accent)


def box(pg, sel):
    el = pg.locator(sel).first; el.scroll_into_view_if_needed(); b = el.bounding_box()
    if not b:
        raise SystemExit(f'Element not found: {sel}')
    return b


def move(pg, x, y, dur=0.6):
    ensure(pg); x0, y0 = pg.evaluate('window.__curXY'); n = max(2, int(dur * 60))
    for i in range(1, n + 1):
        p = i / n; e = p * p * (3 - 2 * p)
        cx, cy = x0 + (x - x0) * e, y0 + (y - y0) * e - 40 * (4 * p * (1 - p)) * (abs(x - x0) > 50)
        pg.evaluate("([x,y])=>{const d=document.getElementById('__cur');d.style.left=x+'px';d.style.top=y+'px';window.__curXY=[x,y]}", [cx, cy])
        pg.mouse.move(cx, cy); time.sleep(dur / n)


def ripple(pg, x, y):
    pg.evaluate("""([x,y,acc])=>{const r=document.createElement('div');r.style.cssText='position:fixed;left:'+(x-6)+'px;top:'+(y-6)+'px;width:12px;height:12px;border:3px solid '+acc+';border-radius:50%;z-index:2147483647;pointer-events:none;transition:all .5s ease-out';
document.documentElement.appendChild(r);requestAnimationFrame(()=>{r.style.transform='scale(4)';r.style.opacity='0'});setTimeout(()=>r.remove(),600)}""", [x, y, a.accent])


with sync_playwright() as p:
    CH = os.environ.get('CHROME', '/usr/bin/google-chrome')
    b = p.chromium.launch(headless=not a.headed, executable_path=CH if os.path.exists(CH) else None)
    ctx = b.new_context(viewport={'width': a.width, 'height': a.height}, device_scale_factor=a.scale,
                        record_video_dir=str(vdir), record_video_size={'width': int(a.width * a.scale), 'height': int(a.height * a.scale)})
    pg = ctx.new_page(); t0 = time.time(); marks = []
    pg.goto(cfg['url'], wait_until='domcontentloaded'); pg.wait_for_timeout(1500); ensure(pg)
    for st in cfg['steps']:
        k = st['do']; marks.append({'t': round(time.time() - t0, 2), 'do': k, 'note': st.get('note', st.get('name', st.get('sel', '')))})
        if k == 'wait':
            pg.wait_for_timeout(int(st.get('s', 1) * 1000))
        elif k in ('click', 'hover'):
            bb = box(pg, st['sel']); x, y = bb['x'] + bb['width'] / 2, bb['y'] + bb['height'] / 2
            move(pg, x, y, st.get('move', 0.6))
            if k == 'click':
                ripple(pg, x, y); pg.mouse.click(x, y); pg.wait_for_timeout(int(st.get('after', 0.8) * 1000)); ensure(pg)
            else:
                pg.wait_for_timeout(int(st.get('s', 0.8) * 1000))
        elif k == 'type':
            pg.keyboard.type(st['text'], delay=st.get('delay', 100))
        elif k == 'key':
            pg.keyboard.press(st['key']); pg.wait_for_timeout(500); ensure(pg)
        elif k == 'spot':
            bb = box(pg, st['sel']); m = st.get('pad', 8)
            pg.evaluate("([x,y,w,h])=>{const s=document.getElementById('__spot');Object.assign(s.style,{left:x+'px',top:y+'px',width:w+'px',height:h+'px',opacity:1})}",
                        [bb['x'] - m, bb['y'] - m, bb['width'] + 2 * m, bb['height'] + 2 * m])
            pg.wait_for_timeout(int(st.get('s', 1.5) * 1000)); pg.evaluate("document.getElementById('__spot').style.opacity=0"); pg.wait_for_timeout(350)
        elif k == 'zoom':
            bb = box(pg, st['sel']); cx, cy = bb['x'] + bb['width'] / 2, bb['y'] + bb['height'] / 2; kz = st.get('k', 1.8)
            pg.evaluate("""([cx,cy,k,s])=>{const h=document.documentElement;h.style.transition='transform '+s+'s ease-in-out';h.style.transformOrigin=cx+'px '+cy+'px';h.style.transform='scale('+k+')'}""",
                        [cx + pg.evaluate('scrollX'), cy + pg.evaluate('scrollY'), kz, st.get('s', 1.5) * 0.6])
            pg.wait_for_timeout(int(st.get('s', 1.5) * 1000))
        elif k == 'unzoom':
            pg.evaluate("([s])=>{const h=document.documentElement;h.style.transition='transform '+s+'s ease-in-out';h.style.transform='none'}", [st.get('s', 0.8)])
            pg.wait_for_timeout(int(st.get('s', 0.8) * 1000))
        elif k == 'scroll':
            pg.mouse.wheel(0, st.get('y', 400)); pg.wait_for_timeout(int(st.get('s', 1) * 1000))
        elif k == 'mark':
            pass
        else:
            raise SystemExit(f'Unknown step: {k}')
    pg.wait_for_timeout(600); vid = pg.video.path(); ctx.close(); b.close()

subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', vid, '-r', '30', '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast',
                '-pix_fmt', 'yuv420p', '-an', str(out / 'web.mp4')], check=True)
(out / 'marks.json').write_text(json.dumps(marks, ensure_ascii=False, indent=1), encoding='utf-8')
shutil.rmtree(vdir, ignore_errors=True)
print('->', out / 'web.mp4', out / 'marks.json')
