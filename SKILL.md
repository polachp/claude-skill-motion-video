---
name: motion-video
description: Make motion-graphics videos from a script, from short reels to long videos up to 4K: config, script, storyboard with playable preview, checks, render, audio, publishing texts and thumbnails. Use when Petr wants a video, reel, short, explainer, script or storyboard.
---

# Motion video from a script

General workflow for motion-graphics videos (animated text, charts, screenshots, live web recordings, icons, maps)
rendered from HTML. Brand, tone, colors, jingle and music of a project live in the **project profile `VIDEO.md`**, not here.
Scripts and templates: repo `C:\Mydrive\Claude Projects\motion-video\` (`scripts/`, `templates/`).

**Language:** talk with Petr in Czech. All files we create (code, comments, docs, profiles, README) are in **English**
(simple English, short sentences). Text that appears in the video (captions, titles) is in the video language from the
config, usually Czech. Storyboard and player UI can be localized with `labels` in `storyboard.json`.

## 0. Project profile

- First find and read the project profile: `VIDEO.md` or `brand/video-profil.md` in the project folder,
  or its text copy in the claude.ai project (`claude/video-profil.md`).
- The profile overrides the defaults of this skill (colors, font, logo, jingle, music, tone, audience,
  phrasing, hashtags, safe zones, example locations).
- No profile: ask about the brand and audience and create one from `templates/VIDEO.md`.

## 1. Config (single source of truth)

A fixed block at the top of the script. Scene times are derived from it.

| Item | Example |
|---|---|
| Topic | MultiModel in Meteoblue |
| Preset | reel / video / feed 4:5 / square |
| Format and design resolution | 9:16 1080×1920 / 16:9 1920×1080 / 4:5 1080×1350 / 1:1 1080×1080 |
| Final render | 1080p, or 4K (`--scale 2` for 16:9) |
| Length | 60–75 s / 8 min / … |
| Video language | cs |
| Voiceover | no / own recording (word sync) |
| Captions | burned in / word by word / SRT |
| Jingle, music | from the profile (file + license) |
| Sound effects | yes / no |
| Live web recordings | no / yes (which sites and steps) |

### Format presets

| Preset | Format | Length | Content adapts |
|---|---|---|---|
| **reel / short** | 9:16, 1080×1920 | up to 3 min (Reels, Shorts); check FB Reels (90 s is often quoted) | one idea, large burned-in captions, content inside the safe zone (app UI at top and bottom), fast pace |
| **video** | 16:9, design 1920×1080, render up to 4K | any | chapters (script and storyboard per chapter, timestamps in the YouTube description: first 0:00, at least 3 chapters), voiceover likely, more room for detail, calmer pace |
| **feed 4:5** | 4:5, 1080×1350 | ~1–2 min | Instagram (and LinkedIn) feed post, taller than square |
| **square** | 1:1, 1080×1080 | ~1 min | feed post (FB, IG), captions in the middle |

"Reel" is only a preset: when Petr says "reel", reel length, format and pace apply.

## 2. Workflow: script → storyboard → approval → render

The output is always a pair **script + storyboard**, kept in sync after every change.
**Final render only on an explicit request** ("vygeneruj video"). Until then only script, storyboard and a low-res preview.

1. **Outline** in chat: a short numbered list of sections (chapters for a video). Keep it short.
2. **Develop section by section:** time, heading, captions exactly as on screen, picture, what we learn,
   motion and transition, sound. For wording questions give 3–4 short options and recommend one.
   Only polish the user's wording for grammar and say what changed.
3. **Script** in `<project>/<output>/scenar.md` and the same copy in the claude.ai project.
   Header = config + last render + storyboard link + status.
4. **Storyboard** = HTML artifact (one link, always republish to the same artifact):
   - `project/video.html` with scenes and `seek(t)` (see Technique), even before any render,
   - `project/storyboard.json`: sections with `name`, `time`, `learn`, `motion`, `sound`, `items`, `changed`
     (CHANGED badge only for changes since the last version), 1–6 frames `[time, caption]` at the busiest moments,
     optional `labels` and `lang` for the UI language,
   - `scripts/storyboard.py project/video.html project/storyboard.json sb/`,
   - `scripts/player.py project/video.html sb/ --chapters project/storyboard.json [--audio mix.mp3]`: a **playable preview**
     at the top of the storyboard, with a chapter timeline (like YouTube) and **comments**: Comment button → click an
     element → a note with time, chapter and element is copied for the chat. Audio must be MP3 (the artifact does not serve .m4a),
   - `scripts/check.py project/video.html` (see Checks); fix or report findings,
   - publish with `publish_files` (mode `replace`) including screenshots, clips and MP3; put the link in the script,
   - end with: "Storyboard je aktualizovaný. Napiš ‚vygeneruj video', nebo co změnit."
5. **After every comment:** update `video.html` → `storyboard.json` → storyboard + player → republish →
   update the script in both copies. Reply briefly with what changed.
6. **Render** only on request, at the config resolution. Changing one scene = re-render only that scene.
   Output name without diacritics, with version (`reel1_multimodel_v5.mp4`); note it in the script.
7. **After the video is approved, ask** whether to generate publishing texts and thumbnails (see Publishing).

## 3. Content and pace

- One output = one main idea; in a long video one idea per chapter.
- Density: about 4–6 learning points and 12–18 visual changes per minute; no dead air longer than ~3 s,
  but enough time to read a caption (about 2–3 words per second).
- Show, don't list: chart, comparison, cause and effect, the real steps on a website.
- Verify claims about websites, apps and features on the live site, not from memory. Do not invent statistics.
- Illustrative data: note it in the script; whether to label it on screen is decided by the profile
  (short formats: as little visual noise as possible).
- Transitions: crossfade by default; where possible, connect scenes (a chart morphs into the next, a card expands into a scene).
- Real brands and logos only genuine and undistorted; never put a third-party logo on illustrative data.

## 4. Checks

- `scripts/check.py project/video.html [--step 0.5] [--safe t,r,b,l]`: text outside the safe zone or frame,
  overflowing text, low contrast (WCAG), dead air longer than 3 s. Default zones per format (9:16, 4:5, 1:1, 16:9);
  the profile can override them.
- `scripts/keys.py project/video.html out t1 t2 …`: frames at given times + contact sheet; look at them.
- After render: a few frames from the MP4 (`ffmpeg -ss t -frames:v 1`), duration, loudness.

## 5. Audio

- Jingle and music from the profile; write the license (author, title, ID, source) into the script.
- `scripts/mix_audio.py out/video_only.mp4 music.mp3 jingle.mp3 output.mp4 [--music-start s] [--jingle-len s]
  [--voice f] [--voice-start s] [--sfx f] [--target -14]` (no jingle or no music: `-` instead of the file):
  music ducked under the jingle, then ramps up, ducks automatically under the voiceover, fades out at the end;
  two-pass loudnorm to −14 LUFS and true peak −1.5 dBTP; video is not re-encoded.
- Skip a quiet intro of the track (RMS per second) so there is no dip after the jingle.
- **Sound effects** that fit the content, only at important changes and much quieter than the music:
  `scripts/sfx.py cues.json sfx.wav --dur <length>` generates in code: whoosh (scene transition), click (frame),
  pop (card appears), tick (label), swell (highlight), riser (build-up), thud (verdict). Take the times (`cues.json`)
  from timeline `T` and the "sound" field in the storyboard. No audio files are stored; effects are code.
  Optional in Claude Code: earshot (MCP; 252 sounds as code, listening and sync checks), if Petr installs it (~1.1 GB of models).
- **Voiceover with word sync:** `scripts/align_voice.py voiceover.wav project/ [--text script.txt]` (Whisper, Czech)
  creates `vo.json`, `vo.js` and `vo.srt`. In `video.html` load `<script src="vo.js">` and time graphics to words:
  `voAt('word')` returns the time of a word; word-by-word captions with `wordCaption(el, t)` (good for 9:16, 4:5, 1:1).
  The recording is the master clock: take length and scene times from it, never stretch anything.
  Whisper timing is accurate to about a tenth of a second; check by listening. `--text` compares the real text with what was heard.
- Stock music may trigger Content ID; file a Dispute with the license, not "Escalate to appeal".

## 6. Technique

1. **Page** `project/video.html` (start from `templates/start.html`): `window.FORMAT={w,h}` (design resolution),
   scenes as `<div class="scene">`, timeline `T={s1:[0,3.5],…}`, deterministic `seek(t)` (no CSS animations,
   timers or `Math.random()`; seeded random), at the end `window.seek=seek; window.T=T;`.
   Local font via `npm i @fontsource/<font>` (the player switches to Google Fonts). Put logos inline as SVG.
2. **Live web recordings** (instead of static screenshots, when the walk through a site matters):
   `scripts/record_web.py steps.json out/ [--width 1280 --height 800 --scale 2]`: Playwright walks the site by steps
   (`click`, `type`, `hover`, `spot` = frame with dimmed surroundings, `zoom`/`unzoom`, `scroll`, `wait`, `mark`)
   with a gliding cursor and a ripple on click; output `web.mp4` + `marks.json` with step times.
   **Run on Petr's PC (Claude Code)**; the cloud sandbox cannot reach normal websites. Reject cookie banners.
   In `video.html` add `<video src="web.mp4" muted preload="auto">` and move it with `vseek(video, time)` (template);
   render, checks and storyboard wait until the seek is done.
3. **Website screenshots** with Claude in Chrome: `document.documentElement.style.transform='scale(2)'`
   (origin `0 0`), move the cursor away, `save_to_disk`; then zoom and frame in the video.
4. **Render** `scripts/render.py project/video.html out/ [--scale S] [--only s3 s6] [--workers 4]`:
   one MP4 per scene in parallel, CRF 18, concat `-c copy`. Preview `--scale 0.5`, 4K from 1920×1080 `--scale 2`.
5. **Audio** `scripts/mix_audio.py` (see above).

Requires: Python with `playwright`, `pillow`, `numpy`, Chrome/Chromium, ffmpeg, Node (fonts); for voiceover `faster-whisper`.

## 7. Publishing (after approval and consent)

- Social texts from the profile (Instagram, Facebook, YouTube): IG 3–5 short lines + a question at the end;
  FB upload separately (do not share from IG), shorter text; YouTube title up to ~60 characters with keywords first,
  description (what, where, main rule, related video, music), chapter timestamps for long videos.
  Hashtags only from the profile set. Save into the script (section "Texty k publikaci").
- YouTube subtitles: upload `vo.srt` (when there is a voiceover).
- Thumbnails: reel 1080×1920 + 1280×720, video 1280×720 (YouTube); large text, main motif, profile style.
  YouTube may not allow a custom thumbnail for Shorts.
