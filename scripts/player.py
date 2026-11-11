"""Hratelný náhled videa do storyboardu (bez renderu MP4), s kapitolami a komentáři.

Použití:  python player.py projekt/reel.html sb/ [--audio mix.mp3] [--chapters projekt/storyboard.json]
Vytvoří sb/player.html (animace + přehrávač s posuvníkem, skoky na scény) a zkopíruje do sb/ obrázky,
na které reel.html odkazuje. Písmo Outfit načítá z Google Fonts (v artefaktu nejde node_modules).
storyboard.py pak přehrávač vloží nahoru do sb/index.html, pokud sb/player.html existuje.
Stránka reel.html musí mít funkci seek(t) a timeline T (window.T).
"""
import sys, re, shutil, argparse, pathlib

ap = argparse.ArgumentParser()
ap.add_argument('reel'); ap.add_argument('out'); ap.add_argument('--audio')
ap.add_argument('--chapters', help='storyboard.json: názvy sekcí jako kapitoly (ve stejném pořadí jako T)')
a = ap.parse_args()
src = pathlib.Path(a.reel); out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
h = src.read_text(encoding='utf-8')

# písmo: node_modules -> Google Fonts
h = re.sub(r'<link rel="stylesheet" href="node_modules/@fontsource/outfit/\d+\.css">', '', h)
h = h.replace('<head>', '<head><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap">', 1)
# obrázky z reel.html zkopírovat vedle
for f in set(re.findall(r'(?:src="|\'img\':\'|img:\')([\w\-.]+\.(?:jpg|jpeg|png|svg))', h)):
    p = src.parent / f
    if p.exists():
        shutil.copy(p, out / f)
# body (1080x1920) -> #stage, který se škáluje do okna
h = re.sub(r'\bbody\{width:(\d+)px;height:(\d+)px;', r'#stage{position:relative;width:\1px;height:\2px;', h, count=1)
h = h.replace('<body>', '<body style="margin:0;background:#0B2545;overflow:hidden"><div id="stage">', 1)
audio_tag = ''
if a.audio:
    shutil.copy(a.audio, out / pathlib.Path(a.audio).name)
    audio_tag = f'<audio id="au" src="{pathlib.Path(a.audio).name}" preload="auto"></audio>'
import json
names = [x['name'] for x in json.load(open(a.chapters, encoding='utf-8'))['sections']] if a.chapters else []
ctl = '''</div>%s
<div id="ctl" style="position:fixed;left:0;right:0;bottom:0;height:78px;background:#08182e;box-sizing:border-box;padding:6px 12px 0;font:600 14px Outfit,sans-serif;color:#fff">
 <div id="bar" style="position:relative;height:18px;display:flex;gap:3px;align-items:center;cursor:pointer"></div>
 <div id="cp" style="display:none;position:fixed;left:12px;right:12px;bottom:88px;background:#08182e;border:2px solid #FFD24A;border-radius:12px;padding:10px;font:500 14px Outfit,sans-serif;color:#fff">
  <div id="cpl" style="opacity:.8;margin-bottom:6px"></div><textarea id="cpt" rows="3" style="width:100%%;box-sizing:border-box;border-radius:8px;font:14px Outfit,sans-serif" placeholder="Co změnit?"></textarea>
  <div style="display:flex;gap:8px;margin-top:6px"><button id="cpc" style="border:0;border-radius:8px;padding:6px 12px;background:#FFD24A;font-weight:700;cursor:pointer">Kopírovat</button><button id="cpx" style="border:0;border-radius:8px;padding:6px 12px;cursor:pointer">Zavřít</button><span id="cps" style="align-self:center;opacity:.8"></span></div>
 </div>
 <div id="tip" style="position:absolute;bottom:72px;display:none;background:#000c;padding:4px 8px;border-radius:6px;font-size:13px;white-space:nowrap;pointer-events:none"></div>
 <div style="display:flex;align-items:center;gap:12px;margin-top:6px">
  <button id="pp" style="width:40px;height:34px;border-radius:9px;border:0;background:#FFD24A;font-size:16px;cursor:pointer">&#9654;</button>
  <span id="tm">0:00 / 0:00</span><span id="ch" style="flex:1;opacity:.85;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"></span>
  <button id="cm" title="Komentář: klikni pak na prvek v obraze" style="height:34px;border-radius:9px;border:0;padding:0 12px;background:#2c4a73;color:#fff;font:600 14px Outfit,sans-serif;cursor:pointer">Komentář</button>
 </div>
</div>
<script>
(function(){const T=window.T,NAMES=%s,keys=Object.keys(T),END=Math.max(...Object.values(T).map(v=>v[1]));const st=document.getElementById('stage');
const bar=document.getElementById('bar'),tip=document.getElementById('tip'),pp=document.getElementById('pp'),tm=document.getElementById('tm'),ch=document.getElementById('ch'),au=document.getElementById('au');
const segs=keys.map((k,i)=>{const [a,b]=T[k];const d=document.createElement('div');d.style.cssText='position:relative;height:5px;flex:'+(b-a)+' 0 0;background:rgba(255,255,255,.28);border-radius:2px;transition:height .1s';
 const f=document.createElement('div');f.style.cssText='position:absolute;left:0;top:0;bottom:0;width:0;background:#FFD24A;border-radius:2px';d.appendChild(f);bar.appendChild(d);
 return {a,b,el:d,fill:f,name:NAMES[i]||k}});
const dot=document.createElement('div');dot.style.cssText='position:absolute;width:13px;height:13px;border-radius:50%%;background:#FFD24A;top:2.5px;margin-left:-6px;pointer-events:none';bar.appendChild(dot);
const SW=st.offsetWidth||1080,SH=st.offsetHeight||1920;
function fit(){const s=Math.min(innerWidth/SW,(innerHeight-78)/SH);st.style.transform='scale('+s+')';st.style.transformOrigin='0 0';
 st.style.position='absolute';st.style.left=((innerWidth-SW*s)/2)+'px';st.style.top='0px'}
addEventListener('resize',fit);fit();
const f=t=>Math.floor(t/60)+':'+String(Math.floor(t%%60)).padStart(2,'0');
const segAt=t=>segs.find(s=>t>=s.a&&t<s.b)||segs[segs.length-1];
function tAtX(x){const r=bar.getBoundingClientRect();for(const s of segs){const q=s.el.getBoundingClientRect();if(x<=q.right+1.5){return s.a+(s.b-s.a)*Math.max(0,Math.min(1,(x-q.left)/q.width))}}return END}
let t=Math.min(1.2,END),playing=false,last=0,drag=false;
function show(){seek(t);segs.forEach(s=>{s.fill.style.width=(t>=s.b?100:t<=s.a?0:(t-s.a)/(s.b-s.a)*100)+'%%'});
 const s=segAt(t),q=s.el.getBoundingClientRect(),r=bar.getBoundingClientRect();dot.style.left=(q.left-r.left+q.width*Math.min(1,(t-s.a)/(s.b-s.a)))+'px';
 tm.textContent=f(t)+' / '+f(END);ch.textContent='• '+s.name}
function loop(now){if(!playing)return;if(au&&!au.paused){t=au.currentTime}else{t+=(now-last)/1000}last=now;
 if(t>=END){t=END;playing=false;pp.innerHTML='&#9654;';if(au)au.pause()}show();if(playing)requestAnimationFrame(loop)}
function setT(v){t=Math.max(0,Math.min(END,+v));if(au){try{au.currentTime=t}catch(e){}}show()}
pp.onclick=()=>{playing=!playing;pp.innerHTML=playing?'&#10074;&#10074;':'&#9654;';if(playing){if(t>=END)setT(0);last=performance.now();
 if(au){au.currentTime=t;au.play().catch(()=>{})}requestAnimationFrame(loop)}else if(au)au.pause()};
bar.addEventListener('pointerdown',e=>{drag=true;bar.setPointerCapture(e.pointerId);setT(tAtX(e.clientX))});
bar.addEventListener('pointermove',e=>{const tt=tAtX(e.clientX),s=segAt(tt);segs.forEach(x=>x.el.style.height=x===s?'8px':'5px');
 tip.style.display='block';tip.textContent=s.name+' · '+f(tt);tip.style.left=Math.max(4,Math.min(innerWidth-tip.offsetWidth-4,e.clientX-tip.offsetWidth/2))+'px';if(drag)setT(tt)});
bar.addEventListener('pointerup',()=>drag=false);bar.addEventListener('pointerleave',()=>{tip.style.display='none';segs.forEach(x=>x.el.style.height='5px')});
addEventListener('resize',show);show();
const cm=document.getElementById('cm'),cp=document.getElementById('cp'),cpl=document.getElementById('cpl'),cpt=document.getElementById('cpt');let cmode=false,ref='';
cm.onclick=()=>{cmode=!cmode;cm.style.background=cmode?'#FFD24A':'#2c4a73';cm.style.color=cmode?'#08182e':'#fff';st.style.cursor=cmode?'crosshair':''};
st.addEventListener('click',e=>{if(!cmode)return;e.preventDefault();e.stopPropagation();if(playing)pp.onclick();
 const vis=n=>{let o=1;for(let q=n;q&&q.nodeType===1&&q!==st;q=q.parentElement)o*=+getComputedStyle(q).opacity;return o};const els=document.elementsFromPoint(e.clientX,e.clientY).filter(n=>st.contains(n)&&n!==st&&vis(n)>0.3);const el=els.find(n=>(n.innerText||n.textContent||'').trim())||els[0]||e.target;const txt=(el.innerText||el.textContent||'').trim().replace(/\\s+/g,' ').slice(0,60);
 const r=st.getBoundingClientRect(),sc=r.width/SW;const x=Math.round((e.clientX-r.left)/sc),y=Math.round((e.clientY-r.top)/sc);
 ref='['+f(t)+' · '+segAt(t).name+' · '+(txt?'prvek „'+txt+'“':(el.tagName.toLowerCase()+(el.id?'#'+el.id:'')))+' · bod '+x+','+y+']';
 cpl.textContent=ref;cpt.value='';cp.style.display='block';cpt.focus();cmode=false;cm.style.background='#2c4a73';cm.style.color='#fff';st.style.cursor=''},true);
document.getElementById('cpx').onclick=()=>cp.style.display='none';
document.getElementById('cpc').onclick=()=>{const v=ref+' '+cpt.value;navigator.clipboard.writeText(v).then(()=>{document.getElementById('cps').textContent='Zkopírováno, vlož do chatu.'},()=>{cpt.value=v;cpt.select();document.getElementById('cps').textContent='Označeno, zkopíruj Ctrl+C.'})};
})();
</script></body>''' % (audio_tag, json.dumps(names, ensure_ascii=False))
h = h.replace('</body>', ctl, 1)
(out / 'player.html').write_text(h, encoding='utf-8')
print('->', out / 'player.html')
