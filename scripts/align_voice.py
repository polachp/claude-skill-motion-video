"""Voiceover: word timings from a recording (Whisper) to sync graphics and captions.

Usage:
  python align_voice.py voiceover.wav project/ [--lang cs] [--model small] [--text voiceover_script.txt]
Output in project/:
  vo.json   {"duration": s, "words": [{"w","start","end"}], "segments": [{"text","start","end"}]}
  vo.js     window.VO = {...}  (load in video.html: <script src="vo.js"></script>)
  vo.srt    subtitles per sentence (YouTube, accessibility)
In video.html:
  voAt('word')             time of the first occurrence of a word (s); voAt('word', 2) = second occurrence
  voWordsAt(t, 4)          words around time t, for word-by-word captions
The recording is the master clock: take video length and scene times from vo.json, never stretch anything.
--text: optional real voiceover text; only used as a check (prints words Whisper heard differently).

Requires: pip install faster-whisper  (or openai-whisper). The model downloads on first run.
Whisper supports Czech; timing accuracy is about a tenth of a second, check by listening.
"""
import sys, json, argparse, pathlib, subprocess, re, difflib

ap = argparse.ArgumentParser()
ap.add_argument('audio'); ap.add_argument('out')
ap.add_argument('--lang', default='cs'); ap.add_argument('--model', default='small')
ap.add_argument('--text')
a = ap.parse_args()
out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)

dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', a.audio]).decode())
words, segs = [], []
try:
    from faster_whisper import WhisperModel
    import numpy as np
    pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', a.audio, '-f', 's16le', '-ac', '1', '-ar', '16000', '-'], capture_output=True, check=True).stdout
    audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0   # decode with ffmpeg (no PyAV)
    m = WhisperModel(a.model, device='cpu', compute_type='int8')
    it, _ = m.transcribe(audio, language=a.lang, word_timestamps=True, vad_filter=True)
    for s in it:
        segs.append({'text': s.text.strip(), 'start': round(s.start, 3), 'end': round(s.end, 3)})
        for w in s.words or []:
            words.append({'w': w.word.strip(), 'start': round(w.start, 3), 'end': round(w.end, 3)})
except ImportError:
    import whisper
    m = whisper.load_model(a.model)
    r = m.transcribe(a.audio, language=a.lang, word_timestamps=True)
    for s in r['segments']:
        segs.append({'text': s['text'].strip(), 'start': round(s['start'], 3), 'end': round(s['end'], 3)})
        for w in s.get('words', []):
            words.append({'w': w['word'].strip(), 'start': round(w['start'], 3), 'end': round(w['end'], 3)})

data = {'duration': round(dur, 3), 'words': words, 'segments': segs}
(out / 'vo.json').write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
js = ('window.VO=' + json.dumps(data, ensure_ascii=False) + ';\n'
      "const _n=s=>s.toLowerCase().normalize('NFC').replace(/[^\\p{L}\\p{N}]+/gu,'');\n"
      "window.voAt=(w,k=1)=>{const q=_n(w);let c=0;for(const x of VO.words){if(_n(x.w)===q&&++c===k)return x.start}console.warn('voAt: not found',w);return null};\n"
      "window.voWordsAt=(t,n=4)=>{const i=VO.words.findIndex(x=>x.end>t);if(i<0)return[];const s=Math.max(0,i-Math.floor(n/2));return VO.words.slice(s,s+n).map(x=>({...x,active:t>=x.start&&t<x.end}))};\n")
(out / 'vo.js').write_text(js, encoding='utf-8')


def ts(x):
    h, r = divmod(x, 3600); m, s = divmod(r, 60)
    return f'{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s % 1) * 1000)):03d}'


(out / 'vo.srt').write_text(''.join(f'{i+1}\n{ts(s["start"])} --> {ts(s["end"])}\n{s["text"]}\n\n' for i, s in enumerate(segs)), encoding='utf-8')
print(f'-> {out}/vo.json, vo.js, vo.srt  ({len(words)} words, {len(segs)} sentences, {dur:.1f} s)')

if a.text:
    norm = lambda s: re.findall(r'\w+', s.lower())
    ref, hyp = norm(open(a.text, encoding='utf-8').read()), [x for w in words for x in norm(w['w'])]
    diff = [d for d in difflib.ndiff(ref, hyp) if d[0] in '+-']
    print('Differences text vs. heard (- in text, + heard):' if diff else 'Text and speech match.')
    for d in diff[:60]:
        print('  ', d)
