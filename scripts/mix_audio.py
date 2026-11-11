"""Zvuk videa: hudba + znělka + voiceover + zvukové efekty, normalizace, připojení k videu.

Použití:
  python mix_audio.py video_only.mp4 hudba.mp3 znelka.mp3 vystup.mp4 [volby]
  (bez znělky místo souboru znělky napiš -; bez hudby místo hudby napiš -)
Volby:
  --music-start S    od kolikáté sekundy skladby začít (přeskočit tiché intro), výchozí 4
  --jingle-len S     délka znělky (dozní poslední 1,2 s), výchozí 4.6
  --voice F          voiceover (WAV/MP3); hudba se pod hlasem automaticky ztlumí (sidechain ducking)
  --voice-start S    kdy voiceover začíná ve videu, výchozí = konec znělky
  --sfx F            stopa zvukových efektů ze sfx.py (WAV, od času 0)
  --target L         cílová hlasitost v LUFS, výchozí -14 (sociální sítě; YouTube normalizuje kolem -14)
Postup: hudba pod znělkou na 35 %, pak náběh; na konci 2,5 s fade-out; dvouprůchodový loudnorm, true peak -1,5 dBTP.
Obraz se nepřekódovává (-c:v copy).
"""
import json, subprocess, argparse

ap = argparse.ArgumentParser()
ap.add_argument('video'); ap.add_argument('music'); ap.add_argument('jingle'); ap.add_argument('out')
ap.add_argument('--music-start', type=float, default=4.0); ap.add_argument('--jingle-len', type=float, default=4.6)
ap.add_argument('--voice'); ap.add_argument('--voice-start', type=float)
ap.add_argument('--sfx'); ap.add_argument('--target', type=float, default=-14.0)
a = ap.parse_args()

dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', a.video]).decode())
inputs, fl, mix = [], [], []
nojing = a.jingle == '-'; vl = 0 if nojing else a.jingle_len
FMT = 'aformat=sample_rates=48000:channel_layouts=stereo'


def add(path):
    inputs.extend(['-i', path]); return len(inputs) // 2 - 1


if a.music != '-':
    i = add(a.music)
    ramp = '' if nojing else f",volume='if(lt(t,{vl - .6}),0.35,if(lt(t,{vl + .9}),0.35+0.65*(t-{vl - .6})/1.5,1))':eval=frame"
    fin = 1 if nojing else 0.05
    fl.append(f"[{i}:a]atrim={a.music_start}:{a.music_start + dur},asetpts=PTS-STARTPTS,{FMT},volume=-6dB{ramp},"
              f"afade=t=in:st=0:d={fin},afade=t=out:st={max(0, dur - 2.5)}:d=2.5[mus0]")
if not nojing:
    i = add(a.jingle)
    fl.append(f"[{i}:a]atrim=0:{vl},asetpts=PTS-STARTPTS,{FMT},volume=-3dB,afade=t=in:st=0:d=0.15,afade=t=out:st={vl - 1.2}:d=1.2[jin]")
    mix.append('[jin]')
if a.voice:
    i = add(a.voice); vs = a.voice_start if a.voice_start is not None else vl; ms = int(vs * 1000)
    fl.append(f"[{i}:a]{FMT},adelay={ms}|{ms},apad,atrim=0:{dur},asplit=2[voc][key]")
    mix.append('[voc]')
if a.music != '-':
    if a.voice:
        fl.append("[mus0][key]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[mus]")
    else:
        fl.append("[mus0]anull[mus]")
    mix.insert(0, '[mus]')
elif a.voice:
    fl.append("[key]anullsink")
if a.sfx:
    i = add(a.sfx); fl.append(f"[{i}:a]{FMT},apad,atrim=0:{dur}[fx]"); mix.append('[fx]')
fl.append(''.join(mix) + f"amix=inputs={len(mix)}:duration=longest:normalize=0,atrim=0:{dur}[mix]")

subprocess.run(['ffmpeg', '-y', '-loglevel', 'error'] + inputs + ['-filter_complex', ';'.join(fl), '-map', '[mix]', '-ar', '48000', 'mix_raw.wav'], check=True)
r = subprocess.run(['ffmpeg', '-hide_banner', '-i', 'mix_raw.wav', '-af', f'loudnorm=I={a.target}:TP=-1.5:LRA=11:print_format=json',
                    '-f', 'null', '-'], capture_output=True, text=True).stderr
j = json.loads(r[r.rindex('{'):r.rindex('}') + 1])
af = (f"loudnorm=I={a.target}:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
      f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'mix_raw.wav', '-af', af, '-ar', '48000', '-c:a', 'aac', '-b:a', '192k', 'mix.m4a'], check=True)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', a.video, '-i', 'mix.m4a', '-map', '0:v', '-map', '1:a',
                '-c:v', 'copy', '-c:a', 'copy', '-shortest', a.out], check=True)
print('->', a.out)
