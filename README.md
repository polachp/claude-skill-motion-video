# motion-video

Skill pro Claude (Claude Code i claude.ai) na tvorbu videí s motion grafikou podle scénáře: od reelů po dlouhá videa až ve 4K.
Postup: konfigurace → scénář → storyboard s hratelným náhledem a komentáři → kontrola → render → zvuk → texty a náhledy k publikaci.

Značka konkrétního projektu je v jeho profilu `VIDEO.md` (šablona v `templates/VIDEO.md`).

## Struktura

```
SKILL.md              instrukce skillu
scripts/
  render.py           render HTML timeline -> MP4 (paralelně po scénách, --scale pro náhled i 4K)
  check.py            kontrola před renderem: bezpečná zóna, přetékání, kontrast, hluchá místa
  keys.py             klíčové snímky v daných časech
  storyboard.py       storyboard (snímky + texty) jako HTML stránka k publikování
  player.py           hratelný náhled s kapitolami a komentáři do storyboardu
  mix_audio.py        hudba + znělka + voiceover (ducking) + efekty, normalizace -14 LUFS
  sfx.py              zvukové efekty generované v kódu, rozmístěné podle časů
  align_voice.py      voiceover: časy slov (Whisper) -> vo.json/vo.js/vo.srt
  record_web.py       živé nahrávání webu s kurzorem, zvýrazněním a zoomem (spouštět lokálně)
templates/
  start.html          kostra video stránky (FORMAT, T, seek)
  VIDEO.md            šablona profilu projektu
```

## Instalace

Potřeba: Python 3.10+ s `pip install playwright pillow numpy` (voiceover navíc `faster-whisper`), Chrome nebo Chromium, ffmpeg, Node (fonty přes `npm i @fontsource/<písmo>`).

- **claude.ai:** obsah `SKILL.md` uložit jako skill (skripty zůstávají v tomto repu, skill na ně odkazuje).
- **Claude Code:** nalinkovat složku do `~/.claude/skills/motion-video` (Windows: `mklink /D "%USERPROFILE%\.claude\skills\motion-video" "C:\Mydrive\Claude Projects\motion-video"`).

## Projekty

- Na přeletu: profil `Na-preletu/brand/video-profil.md`, vzor `Na-preletu/reels/2026-11-reel01-multimodel/`.

## Licence

Soukromé.
