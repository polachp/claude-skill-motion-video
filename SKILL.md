---
name: motion-video
description: Tvorba videí s motion grafikou podle scénáře – od krátkých reelů po dlouhá videa až ve 4K: konfigurace, scénář, storyboard s hratelným náhledem, kontrola, render, zvuk, texty k publikaci a náhledy. Použij, když Petr chce video, reel, short, explainer, scénář nebo storyboard k videu.
---

# Motion video podle scénáře

Obecný postup pro videa s motion grafikou (animovaný text, grafy, screenshoty, ikony, mapy) renderovaná z HTML.
Značka, tón, barvy, znělka a hudba konkrétního projektu jsou v **profilu projektu `VIDEO.md`**, ne tady.
Skripty a šablony: repo `C:\Mydrive\Claude Projects\motion-video\` (`scripts/`, `templates/`).

## 0. Profil projektu

- Na začátku najít a přečíst profil projektu: `VIDEO.md` nebo `brand/video-profil.md` ve složce projektu,
  případně textovou kopii v claude.ai projektu (`claude/video-profil.md`).
- Profil má přednost před výchozími hodnotami tohoto skillu (barvy, písmo, logo, znělka, hudba, tón, publikum,
  formulace, hashtagy, bezpečné zóny, ukázkové lokality).
- Když profil chybí: zeptat se na značku a publikum a založit ho podle `templates/VIDEO.md`.

## 1. Konfigurace (jediný zdroj pravdy)

Pevný blok na začátku scénáře. Časy scén se odvozují z něj.

| Položka | Příklad |
|---|---|
| Téma | MultiModel v Meteoblue |
| Předvolba | reel / video / čtverec |
| Formát a návrhové rozlišení | 9:16 1080×1920 / 16:9 1920×1080 / 4:5 1080×1350 / 1:1 1080×1080 |
| Finální render | 1080p, nebo 4K (`--scale 2` u 16:9) |
| Délka | 60–75 s / 8 min / … |
| Voiceover | ne / vlastní nahrávka (synchronizace na slova) |
| Titulky | vypálené v obraze / SRT / obojí |
| Znělka, hudba | podle profilu (soubor + licence) |
| Zvukové efekty | ano / ne |
| Živé nahrávky webu | ne / ano (které weby a kroky) |

### Předvolby formátu

| Předvolba | Formát | Délka | Obsah se přizpůsobí |
|---|---|---|---|
| **reel / short** | 9:16, 1080×1920 | do 3 min (Reels, Shorts); FB Reels ověřit (uvádí se 90 s) | jedna myšlenka, velké titulky v obraze, obsah v bezpečné zóně (UI aplikace nahoře a dole), rychlé tempo |
| **video** | 16:9, návrh 1920×1080, render až 4K | libovolná | kapitoly (scénář i storyboard po kapitolách, časové značky do popisu YouTube: první 0:00, min. 3 kapitoly), spíš voiceover, víc prostoru na detail, klidnější tempo |
| **feed 4:5** | 4:5, 1080×1350 | do ~1–2 min | příspěvek do feedu Instagramu (a LinkedIn), zabere víc výšky než čtverec |
| **čtverec** | 1:1, 1080×1080 | do ~1 min | příspěvek do feedu (FB, IG), titulky uprostřed |

Reel je jen předvolba: když Petr řekne „reel“, platí délka, formát i tempo reelu.

## 2. Spolupráce: scénář → storyboard → schválení → render

Výstupem je vždy dvojice **scénář + storyboard**, v souladu po každé změně.
**Finální render až na výslovný pokyn** („vygeneruj video“). Do té doby jen scénář, storyboard a náhled v malém rozlišení.

1. **Hrubé rysy** v chatu: krátký číslovaný seznam sekcí (u videa kapitol). Stručně.
2. **Rozpracovat po sekcích:** čas, nadpis, titulky přesně jak budou na obrazovce, popis obrazu, co se učíme,
   pohyb a přechod, zvuk. Na slova dávat 3–4 krátké varianty a doporučit jednu. Formulace uživatele jen gramaticky
   uhladit a říct, co se změnilo.
3. **Scénář** do `<projekt>/<výstup>/scenar.md` a stejnou kopii do claude.ai projektu. Hlavička = konfigurace +
   poslední render + odkaz na storyboard + stav.
4. **Storyboard** = HTML artefakt (jeden odkaz, republikovat do stejného artefaktu):
   - `projekt/video.html` se scénami a `seek(t)` (viz Technika), i když se ještě nerenderuje,
   - `projekt/storyboard.json`: sekce s `name`, `time`, `learn`, `motion`, `sound`, `items`, `changed` (štítek
     UPRAVENO jen u změn od minulé verze), 1–6 snímků `[čas, popisek]` v okamžicích s nejvíc obsahem,
   - `scripts/storyboard.py projekt/video.html projekt/storyboard.json sb/`,
   - `scripts/player.py projekt/video.html sb/ --chapters projekt/storyboard.json [--audio mix.mp3]`: nahoře
     ve storyboardu **hratelný náhled** s časovou osou rozdělenou na kapitoly (jako YouTube) a s **komentáři**:
     tlačítko Komentář → klik na prvek → připomínka s časem, kapitolou a prvkem se zkopíruje do chatu.
     Zvuk jen MP3 (artefakt neservíruje .m4a),
   - `scripts/check.py projekt/video.html` (viz Kontrola) a nálezy opravit nebo zmínit,
   - publikovat `publish_files` (mode `replace`) i se screenshoty a MP3; odkaz zapsat do scénáře,
   - zakončit větou: „Storyboard je aktualizovaný. Napiš ‚vygeneruj video‘, nebo co změnit.“
5. **Po každé připomínce:** upravit `video.html` → `storyboard.json` → storyboard + přehrávač → republikovat →
   aktualizovat scénář v obou kopiích. V odpovědi stručně, co se změnilo.
6. **Render** až na pokyn, v rozlišení z konfigurace. Úprava jedné scény = přerenderovat jen ji.
   Výstup bez diakritiky s verzí (`reel1_multimodel_v5.mp4`), zapsat do scénáře.
7. **Po schválení videa se zeptat**, jestli vygenerovat texty k publikaci a náhledové obrázky (sekce Publikace).

## 3. Obsah a tempo

- Jeden výstup = jedna hlavní myšlenka; u dlouhého videa jedna myšlenka na kapitolu.
- Hustota: cca 4–6 učebních bodů a 12–18 vizuálních změn za minutu; žádné hluché místo delší než ~3 s,
  ale čas na přečtení titulku (cca 2–3 slova za sekundu).
- Ukazovat, ne vyjmenovávat: graf, srovnání, příčina a následek, skutečný postup na webu.
- Tvrzení o webech, aplikacích a funkcích ověřit na živém webu, ne zpaměti. Nevymýšlet statistiky.
- Ilustrační data jen poznamenat ve scénáři; zda je označit i v obraze, určí profil (v krátkých formátech
  co nejméně vizuálního šumu).
- Přechody: výchozí prolínačka; kde to jde, navazovat (graf se promění v další, karta se rozbalí do scény).
- Skutečné značky a loga jen pravé a nedeformované; na ilustračních datech cizí logo nepoužívat.

## 4. Kontrola

- `scripts/check.py projekt/video.html [--step 0.5] [--safe t,r,b,l]`: text mimo bezpečnou zónu nebo obraz,
  přetékající text, nízký kontrast (WCAG), hluchá místa delší než 3 s. Bezpečné zóny může přepsat profil.
- `scripts/keys.py projekt/video.html out t1 t2 …`: snímky v daných časech + náhledový přehled; prohlédnout.
- Po renderu: pár snímků z MP4 (`ffmpeg -ss t -frames:v 1`), délka, loudness.

## 5. Zvuk

- Znělka a hudba podle profilu; licenci (autor, název, ID, zdroj) zapsat do scénáře.
- `scripts/mix_audio.py out/video_only.mp4 hudba.mp3 znelka.mp3 vystup.mp4 [--music-start s] [--jingle-len s]`
  (bez znělky místo souboru `-`): hudba pod znělkou ztlumená, pak náběh, na konci fade-out, dvouprůchodový
  loudnorm na −14 LUFS a true peak −1,5 dBTP; obraz se nepřekódovává.
- Přeskočit tiché intro skladby (RMS po sekundách), aby po znělce nebyl propad.
- **Zvukové efekty** podle obsahu, jen u důležitých změn a výrazně tišší než hudba:
  `scripts/sfx.py cues.json sfx.wav --dur <délka>` generuje v kódu whoosh (přechod scény), click (rámeček),
  pop (objevení karty), tick (popisek), swell (zvýraznění), riser (náběh), thud (verdikt). Časy (`cues.json`)
  brát z timeline `T` a ze sloupce „zvuk“ ve storyboardu; do mixu `mix_audio.py … --sfx sfx.wav`.
  Volitelně v Claude Code nástroj earshot (MCP; banka 252 zvuků v kódu, poslech a kontrola synchronizace),
  pokud ho Petr nainstaluje (cca 1,1 GB modelů).
- **Voiceover se synchronizací na slova:** `scripts/align_voice.py voiceover.wav projekt/ [--text text.txt]`
  (Whisper, čeština) vytvoří `vo.json`, `vo.js` a `vo.srt`. Ve `video.html` načíst `<script src="vo.js">`
  a časovat grafiku na slova: `voAt('předpověď')` vrátí čas slova; titulky slovo po slově `wordCaption(el, t)`
  (hodí se pro 9:16, 4:5 a 1:1). Nahrávka je hlavní hodiny: délku a časy scén odvodit z ní, nic nenatahovat.
  Časy z Whisperu jsou přesné řádově na desetiny sekundy, ověřit poslechem. `--text` porovná skutečný text
  se slyšeným (překlepy, špatně vyslovená slova).
- Do mixu: `mix_audio.py … --voice voiceover.wav [--voice-start s]`; hudba se pod hlasem sama ztlumí (ducking).
- Hudba ze stock knihoven může vyvolat Content ID; řešit sporem typu Dispute s licencí, ne „Escalate to appeal“.

## 6. Technika

1. **Stránka** `projekt/video.html` (start: `templates/start.html`): `window.FORMAT={w,h}` (návrhové rozlišení),
   scény jako `<div class="scene">`, timeline `T={s1:[0,3.5],…}`, deterministická `seek(t)` (žádné CSS animace,
   časovače ani `Math.random()`; seedovaná náhoda), na konci `window.seek=seek; window.T=T;`.
   Písmo lokálně přes `npm i @fontsource/<písmo>` (přehrávač ho přepne na Google Fonts). Logo vkládat inline SVG.
2. **Živé nahrávky webu** (místo statických screenshotů, když je důležitý průchod webem):
   `scripts/record_web.py kroky.json out/ [--width 1280 --height 800 --scale 2]`: Playwright projde web podle kroků
   (`click`, `type`, `hover`, `spot` = rámeček se ztmavením okolí, `zoom`/`unzoom`, `scroll`, `wait`, `mark`)
   s plynulým kurzorem a vlnkou při kliknutí; výstup `web.mp4` + `marks.json` s časy kroků.
   **Spouštět u Petra (Claude Code)**, cloudový sandbox na běžné weby nedosáhne. Cookie lišty odmítat.
   Ve `video.html` vložit `<video src="web.mp4" muted preload="auto">` a posouvat `vseek(video, čas)` (šablona);
   render, kontrola i storyboard počkají na dokončení posunu.
3. **Screenshoty webů** přes Claude in Chrome: `document.documentElement.style.transform='scale(2)'`
   (origin `0 0`), kurzor odsunout, `save_to_disk`; pak zoom a rámeček ve videu.
4. **Render** `scripts/render.py projekt/video.html out/ [--scale S] [--only s3 s6] [--workers 4]`:
   MP4 na scénu paralelně, CRF 18, concat `-c copy`. Náhled `--scale 0.5`, 4K z 1920×1080 `--scale 2`.
5. **Zvuk** `scripts/mix_audio.py` (viz výše).

Potřeba: Python s `playwright`, `pillow`, `numpy`, Chrome/Chromium, ffmpeg, Node (fonty); pro voiceover `faster-whisper`.

## 7. Publikace (po schválení videa a souhlasu)

- Texty pro sítě z profilu (Instagram, Facebook, YouTube): IG 3–5 krátkých řádků + otázka na konci;
  FB nahrát samostatně (ne sdílet z IG), kratší text; YouTube název do ~60 znaků s klíčovými slovy na začátku,
  popis (co, kde, hlavní pravidlo, odkaz na související video, hudba), u videa časové značky kapitol.
  Hashtagy jen ze sady v profilu. Uložit do scénáře (sekce „Texty k publikaci“).
- Titulky k videu na YouTube: nahrát `vo.srt` (pokud je voiceover).
- Náhledové obrázky: pro reel 1080×1920 + 1280×720, pro video 1280×720 (YouTube); velký text, hlavní motiv,
  styl podle profilu. U Shorts YouTube nemusí vlastní náhled povolit.
