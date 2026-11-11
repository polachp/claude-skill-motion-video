# motion-video

A skill for Claude (Claude Code and claude.ai) to make motion-graphics videos from a script: from reels to long videos up to 4K.
Workflow: config → script → storyboard with playable preview and comments → checks → render → audio → publishing texts and thumbnails.

The brand of a project lives in its profile `VIDEO.md` (template in `templates/VIDEO.md`).

## Structure

```
SKILL.md              skill instructions
scripts/
  render.py           render HTML timeline -> MP4 (parallel per scene, --scale for preview and 4K)
  check.py            pre-render check: safe zone, overflow, contrast, dead air
  keys.py             key frames at given times
  storyboard.py       storyboard (frames + texts) as an HTML page to publish
  player.py           playable preview with chapters and comments for the storyboard
  mix_audio.py        music + jingle + voiceover (ducking) + effects, loudness -14 LUFS
  sfx.py              sound effects generated in code, placed at given times
  align_voice.py      voiceover: word timings (Whisper) -> vo.json / vo.js / vo.srt
  record_web.py       live web recording with cursor, highlight and zoom (run locally)
templates/
  start.html          video page skeleton (FORMAT, T, seek, vseek, wordCaption)
  VIDEO.md            project profile template
```

## Install

Requires: Python 3.10+ with `pip install playwright pillow numpy` (voiceover also `faster-whisper`), Chrome or Chromium,
ffmpeg, Node (fonts via `npm i @fontsource/<font>`).

- **claude.ai:** save the content of `SKILL.md` as a skill (scripts stay in this repo; the skill points to them).
- **Claude Code:** link the folder to `~/.claude/skills/motion-video`
  (Windows: `mklink /D "%USERPROFILE%\.claude\skills\motion-video" "C:\Mydrive\Claude Projects\motion-video"`).

## Projects

- Na přeletu: profile `Na-preletu/brand/video-profil.md`, example `Na-preletu/reels/2026-11-reel01-multimodel/`.

## License

Private.
