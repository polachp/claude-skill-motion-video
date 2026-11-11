"""Zvuk videa: hudba + znělka na začátku (volitelně), normalizace na -14 LUFS, připojení k videu.

Použití:
  python mix_audio.py video_only.mp4 hudba.mp3 znelka.mp3 vystup.mp4 [--music-start 4] [--jingle-len 4.6] [--target -14]
  (bez znělky: místo souboru znělky napiš -)

- hudba začíná od --music-start s skladby (přeskočí tiché intro), pod variem je ztlumená na 35 %,
  pak během 1,5 s náběh na plnou hlasitost, na konci 2,5 s fade-out
- vario hraje 0 až --vario-len s, posledních 1,2 s doznívá
- dvouprůchodový loudnorm: I=-14 LUFS, TP=-1.5 dBTP (Instagram, YouTube)
- obraz se nepřekódovává (-c:v copy)
"""
import sys, json, subprocess, argparse

ap = argparse.ArgumentParser()
ap.add_argument('video'); ap.add_argument('music'); ap.add_argument('jingle', help='znělka, nebo - pro žádnou'); ap.add_argument('out')
ap.add_argument('--music-start', type=float, default=4.0)
ap.add_argument('--jingle-len', type=float, default=4.6)
ap.add_argument('--target', type=float, default=-14.0, help='LUFS (sociální sítě -14)')
a = ap.parse_args()

dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                     '-of', 'csv=p=0', a.video]).decode())
vl = a.jingle_len
noj = a.jingle == '-'
F = (f"[0:a]atrim={a.music_start}:{a.music_start + dur},asetpts=PTS-STARTPTS,volume=-6dB,"
     f"volume='if(lt(t,{vl - .6}),0.35,if(lt(t,{vl + .9}),0.35+0.65*(t-{vl - .6})/1.5,1))':eval=frame,"
     f"afade=t=out:st={dur - 2.5}:d=2.5[m];"
     f"[1:a]atrim=0:{vl},asetpts=PTS-STARTPTS,volume=-3dB,afade=t=in:st=0:d=0.15,afade=t=out:st={vl - 1.2}:d=1.2[v];"
     f"[m][v]amix=inputs=2:duration=first:normalize=0[mix]")
if noj:
    F = (f"[0:a]atrim={a.music_start}:{a.music_start + dur},asetpts=PTS-STARTPTS,volume=-6dB,"
         f"afade=t=in:st=0:d=1,afade=t=out:st={dur - 2.5}:d=2.5[mix]")
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', a.music] + ([] if noj else ['-i', a.jingle]) + ['-filter_complex', F,
                '-map', '[mix]', '-ar', '48000', 'mix_raw.wav'], check=True)
r = subprocess.run(['ffmpeg', '-hide_banner', '-i', 'mix_raw.wav', '-af',
                    f'loudnorm=I={a.target}:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'],
                   capture_output=True, text=True).stderr
j = json.loads(r[r.rindex('{'):r.rindex('}') + 1])
af = (f"loudnorm=I={a.target}:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
      f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'mix_raw.wav', '-af', af, '-ar', '48000',
                '-c:a', 'aac', '-b:a', '192k', 'mix.m4a'], check=True)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', a.video, '-i', 'mix.m4a', '-map', '0:v', '-map', '1:a',
                '-c:v', 'copy', '-c:a', 'copy', '-shortest', a.out], check=True)
print('->', a.out)
