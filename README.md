# 雅思不能停

雅思不能停 is the public beta release package for Immerse Learning. It turns YouTube clippings and English Markdown notes into an
immersive language-learning workspace inside Obsidian. It creates clean
transcript Markdown — original text plus an optional Chinese translation — and
plays the video with synced, clickable subtitles.

This repository is the public beta install channel. The development source is
maintained at <https://github.com/JackLee992/obsidian-youtube-plugin>.

It identifies the YouTube URL in a clipping note, fetches the video's existing
captions, and writes a tidy, timestamped transcript into your vault for ClipLex,
review, sentence mining, or any other knowledge workflow to digest.

## What It Does

- **Find the video automatically** — reads the YouTube URL from a note's
  frontmatter (`source` / `url` / `link`) or body. Supports `watch`, `youtu.be`,
  `shorts`, `live`, and `embed` links, including ones inside Markdown syntax.
- **Fetch existing captions reliably** — first calls a local ClipLex yt-dlp
  extractor service, then falls back to the original built-in YouTube caption
  fetcher when the local service is unavailable or returns no usable track.
  Manual captions are preferred over auto-generated ones.
- **Write a clean transcript** to your output folder as `{title} - {videoId}.md`,
  with clickable per-line timestamps under a stable `## Transcript` heading.
- **Optional Chinese translation** into a sibling `… CN.md` file via any
  OpenAI-compatible provider (**Local model / OpenAI / OpenRouter / DeepSeek /
  Kimi / Custom**). Local model translation defaults to an OpenAI-compatible
  endpoint such as Ollama or LM Studio; remote providers still require an API
  key. Every timestamp line is preserved.
- **Link back to the clipping** — writes status frontmatter
  (`transcript_status`, `transcript_file`, `transcript_cn_file`, …) and a
  `## Immerse Learning` section into the source note. Re-running is idempotent.
- **Process and open watch mode** (desktop) — the recommended flow fetches
  captions, writes the transcript, then opens a focused two-pane workspace with
  video on the left and synced transcript on the right.
- **Play inside Obsidian** — the current line highlights and autoscrolls in sync.
  Click any line to seek; toggle original / Chinese / bilingual display.
- **Immersive Learning drills** — replay the current sentence, move sentence by
  sentence, loop one subtitle line, hide the active line for dictation, reveal it
  after listening, and filter the transcript by all / i+1 / unknown / saved.
- **Click-word dictionary lookup** — Click any English word in the synced
  transcript to open a ClipLex dictionary card. The card uses a local
  ECDICT/DictionaryByGPT4-style seed dictionary first, then Free Dictionary API
  online lookup when available.
- **Article Deep Study Mode** — switch article learning from clean Immerse
  reading into a close-reading desk that shows words, collocations, grammar
  structures, and complex sentences with different color wavy underlines.
- **Auto-start bundled local TTS** — on Obsidian desktop, article read-aloud
  can prepare and launch the bundled Kokoro service automatically the first time
  the default local voice is used.
- **One-click study records** — add the selected word, definition, subtitle
  sentence, and timestamped source into `ClipLex/Study/Word Learning.md`.
- **Sentence mining records** — save the full subtitle sentence, translation
  when available, focus words, phrase chunks, and timestamped source into
  `ClipLex/Study/Sentence Mining.md`.
- **Review queue** — queue mined sentences into an FSRS-compatible review state
  and review due cards from Obsidian.
- **Shadowing recording** — record your own follow-along audio and save it under
  `ClipLex/Media/Shadowing`.
- **Timestamped frame context** — save YouTube timestamp links plus thumbnail
  context for review cards. Real iframe screenshots are not captured because
  YouTube embeds are cross-origin.
- **Timestamped notes with context** — freeze the current playback time and
  append a clickable note with the nearest original subtitle and Chinese line
  when available.
- **Localized UI** — English or Chinese, following Obsidian's configured language.

## What It Is Not

Immerse Learning does **not** summarize, download video or audio, or transcribe
with Whisper. It produces text assets from captions that already exist on
YouTube; the player is a read/review surface streamed live from YouTube.

```text
Web Clipper note → Immerse Learning → Transcript Markdown (+ optional CN) → review / mining notes
                                 ↘ Player + synced transcript
```

## Installation

Immerse Learning is not yet in the Obsidian community plugin store.

### Via BRAT (recommended)

[BRAT](https://github.com/TfTHacker/obsidian42-brat) installs the plugin and
keeps it auto-updated from this repository.

1. Install **BRAT** from Community Plugins and enable it.
2. Run the command **BRAT: Add a beta plugin for testing**.
3. Paste this repository URL:

   ```text
   https://github.com/JackLee992/ielts-cant-stop
   ```

4. BRAT downloads the latest release into your vault.
5. Enable **Immerse Learning** in Community Plugins, then open its settings.

### Manual install

1. Download `main.js`, `manifest.json`, `styles.css`, and `tools/local-tts/`
   from the
   [latest release](https://github.com/JackLee992/ielts-cant-stop/releases/latest).
2. Put the files in `<your-vault>/.obsidian/plugins/immerse-learning/`, keeping
   `tools/local-tts/kokoro_onnx_server.py` under that plugin folder.
3. Reload Obsidian and enable **Immerse Learning** in Community Plugins.

## Usage

1. Open a clipping note that contains a YouTube URL.
2. Click the play ribbon icon or run **Immerse Learning: Process and open watch
   mode**. This is the P0 watch workflow: fetch captions, write the Markdown
   transcript, then replace the current pane with a focused player + synced
   transcript layout.
3. Other commands remain available:
   - **Immerse Learning: Process current note** — fetch (and translate, if enabled).
   - **Immerse Learning: Fetch transcript only** — never translates.
   - **Immerse Learning: Translate current transcript** — translate an already-open
     transcript file into a CN file.
   - **Immerse Learning: Open player with synced transcript** — desktop only.
   - **Immerse Learning: Add note at current time** — desktop only.
   - **Immerse Learning: Check local model health** — local model health check for
     OpenAI-compatible servers such as Ollama or LM Studio.

Optional translation is configured in settings: pick a provider, set a model
name, and paste an API key when using a remote provider. Base URLs are prefilled
but editable.

## Article Learning

Open any English Markdown note and run **Immerse Learning: Open article learning
mode**. The article view has two modes:

- **Immerse** keeps the page quiet for reading and local-model read-aloud. You
  can still click words, merge badly split terms, and generate cached audio.
- **Deep Study Mode** turns on the analysis layer. Blue wavy underlines mark
  study words, green marks collocations, purple marks grammar structures, and
  orange marks complex sentences. Use the filter bar to focus on Words,
  Collocations, Grammar, Sentences, or Saved insights.

Click any underline to open a focused explanation card. Save useful items into:

```text
ClipLex/Study/Article Deep Study.md
```

Deep Study uses local rules first, so it works without API tokens. Local LLM or
NLP-backed explanations can be layered on later without changing the reading UI.

## ClipLex Caption Extractor

This build adds a stable local-first caption path:

```text
Obsidian plugin -> ClipLex yt-dlp extractor -> normalized VTT -> transcript Markdown
                ↘ built-in YouTube caption fetcher fallback
```

The plugin calls:

```http
POST http://127.0.0.1:8000/v1/extract/subtitles
```

with a ClipLex-compatible payload:

```json
{
  "url": "https://www.youtube.com/watch?v=VIDEOID",
  "preferredLanguages": ["en", "en-US", "zh", "zh-CN"],
  "includeAutoCaptions": true,
  "includeTrackBody": true,
  "includeAllTracks": true,
  "returnFormat": "vtt"
}
```

Settings expose both the local extractor toggle and base URL. Keep the default
`http://127.0.0.1:8000` for a same-machine extractor, or switch it to a LAN /
server URL when Obsidian is not running on the extractor host.

## Local Model Translation

The default LLM provider is now **Local model (OpenAI-compatible)** with the
default base URL:

```text
http://127.0.0.1:11434/v1
```

This works with OpenAI-compatible local servers such as Ollama or LM Studio.
For local providers, the API key field can stay empty; the model field still
needs a model name, for example `qwen2.5:7b`. Remote providers continue to
require both API key and model.

Run **Immerse Learning: Check local model health** to call the local
OpenAI-compatible `/models` endpoint and confirm Obsidian can reach the server
before generating bilingual transcripts.

## Watch Mode

Watch mode now opens as a focused two-pane workspace:

- Existing Immerse Learning player/transcript panes are closed first, avoiding the
  previous three-column Markdown + player + transcript layout.
- The player is placed in the current pane, and the synced transcript is split
  beside it.
- Processing a note auto-opens watch mode by default. If no Chinese transcript
  exists yet, the view falls back to original-only mode and shows a setup hint.
- Notes saved from the capture bar include the timestamp, your note, the nearest
  original subtitle, and the nearest translated subtitle when a CN file exists.

## Switch Videos

Video switching is available inside the learning workflow:

- Run **Immerse Learning: Switch video by URL** and paste a YouTube link.
- Or click **Video** in the synced transcript header and paste the next link.
- ClipLex creates or reuses a lightweight source note under `ClipLex/Videos`,
  reuses an existing transcript for that video when one is already in your
  output folder, and only calls the extractor when no local transcript exists.
- Recently opened videos are shown by video title in the switcher so you can
  jump back without finding the original note first.

## Immersive Learning

The synced transcript view now includes an immersive learning toolbar:

- **Prev / Next** jumps one subtitle sentence at a time.
- **Replay** seeks to the start of the active sentence and plays it again.
- **Loop** keeps the active sentence repeating for close listening.
- **Dictation** hides the active subtitle line so you can listen before reading.
- **Reveal** shows the hidden line after the listening attempt.
- **Mine** saves the active subtitle into:

```text
ClipLex/Study/Sentence Mining.md
```

- **Merge edit mode** lets you click **Merge**, choose the first and last
  adjacent words in the transcript, then confirm them as one reusable token for
  future dictionary lookup and study capture.

The filter bar supports **All**, **i+1**, **Unknown**, and **Saved** views. The
i+1 view shows subtitle lines with exactly one unknown content word based on the
ClipLex word-status store plus a small common-word baseline. Click any word and
mark it as **Unknown**, **Learning**, **Known**, or **Ignore**; those statuses
change future highlights and filters.

Common phrase chunks such as `call to action`, `come across`, and
`public speaking` are surfaced inline so learners save useful expressions, not
only isolated words.

## Article Learning

Immerse Learning can also turn an existing English Markdown article in Obsidian into a
study surface:

- Open any English article note and click the **Open article learning mode**
  ribbon icon, or right-click the note / editor and choose **Open in Immerse
  Article Learning**.
- You can still run **Immerse Learning: Open current article in Immerse Article mode**
  or **Immerse Learning: Open article learning mode** from the command palette.
- The article opens in a dedicated learning pane, with Markdown syntax cleaned
  into readable paragraphs.
- Click any English word to use the same ClipLex dictionary, word-status, and
  one-click study-log workflow used by video subtitles.
- **Read aloud** starts English article reading from the active paragraph,
  highlights the paragraph being spoken, and keeps it centered while the text
  scrolls. Local TTS shows a generating/loading status and prepares the next
  paragraph while the current one is playing to reduce gaps between paragraphs.
- **Generate article audio** builds the local-model audio for the whole article
  ahead of time. The generated WAV segments are cached under
  `ClipLex/Media/ArticleAudioCache` and reused as long as the source article
  text and voice settings do not change.
- **Voice** defaults to a no-token local TTS model endpoint compatible with
  Kokoro/OpenAI speech APIs: `http://127.0.0.1:8880/v1/audio/speech`, model
  `kokoro`, voice `af_heart`. Auto-start bundled local TTS is on by
  default: the plugin prepares the Kokoro venv/assets under
  `~/.cache/immerse-learning/kokoro` and starts the local Kokoro service when
  needed. Pick
  **Warm article reader**, **Clear neutral reader**, **British article reader**,
  or another voice in the Voice panel. If the local service fails, reading stops
  and shows the failure reason instead of switching voices silently. Use
  **Test local TTS** in the Voice panel to prepare/check the bundled service.
  Choose **System voice** explicitly if you want the browser speech engine
  instead of the local endpoint.
- Use **Merge edit mode** when the tokenizer splits a word or phrase
  incorrectly: click **Merge**, click adjacent article tokens to define the
  range, then click **Confirm**.
- Lightweight reading progress is saved per source note so returning to the
  article keeps the active paragraph context.

## Local Kokoro TTS Service

Article read-aloud uses an OpenAI-compatible local speech endpoint by default:

```text
http://127.0.0.1:8880/v1/audio/speech
```

Auto-start bundled local TTS is enabled by default on Obsidian desktop. The
first read-aloud or **Voice -> Test local TTS** action will:

1. prepare `~/.cache/immerse-learning/kokoro/.venv` and install
   `kokoro-onnx`/`soundfile` in the background;
2. download the smaller `kokoro-v1.0.int8.onnx` model and `voices-v1.0.bin`;
3. start the bundled `tools/local-tts/kokoro_onnx_server.py` service in Kokoro
   mode.

The first run may take longer while dependencies and model assets are prepared.
It should not silently fall back to macOS `say`; if Kokoro cannot start, the
plugin shows the failure reason. The managed service is stopped when Obsidian
unloads the plugin.

Advanced users can still verify or run a compatible service manually:

```bash
curl http://127.0.0.1:8880/health
curl -H "Content-Type: application/json" \
  -d '{"model":"kokoro","input":"This is a local Kokoro test.","voice":"reader_warm","response_format":"wav"}' \
  http://127.0.0.1:8880/v1/audio/speech \
  -o /tmp/immerse-kokoro-test.wav
```

### Choosing Local Voices

Immerse Learning preserves the configured local voice in Obsidian plugin data,
so plugin updates should not overwrite the voice you picked in
`.obsidian/plugins/immerse-learning/data.json`.

To try a different article-reading voice:

1. Open an article learning pane.
2. Click **Voice**.
3. Keep **Reading provider** set to **Local model**.
4. Choose another voice from the **Local voice** dropdown.
5. Click **Test local TTS** and listen before using **Read** or
   **Generate audio**.

The top of the dropdown contains reading presets such as `reader_warm`,
`reader_clear`, `reader_british`, and `reader_relaxed`. These presets map to a
matching Kokoro voice. `reader_warm` defaults to `af_heart`, which is a better
fit for article reading than the very plain default voices.

The dropdown also contains the available voice ids from the bundled
`voices-v1.0.bin`. Useful English Kokoro voices include:

```text
af_heart, af_bella, af_nicole, af_sarah, af_sky, af_nova
am_adam, am_echo, am_eric, am_liam, am_michael, am_onyx
bf_alice, bf_emma, bf_isabella, bf_lily
bm_daniel, bm_fable, bm_george, bm_lewis
```

Voice id prefixes are a quick guide: `af`/`am` are American English female/male
voices, and `bf`/`bm` are British English female/male voices. The full local
voice list can be printed with:

```bash
~/.cache/immerse-learning/kokoro/.venv/bin/python - <<'PY'
from pathlib import Path
from kokoro_onnx import Kokoro

base = Path("~/.cache/immerse-learning/kokoro").expanduser()
kokoro = Kokoro(str(base / "kokoro-v1.0.int8.onnx"), str(base / "voices-v1.0.bin"))
print("\n".join(kokoro.get_voices()))
PY
```

Changing **Local voice** also changes the article-audio cache key, so previously
generated audio is not reused with the wrong voice. If the selected voice has
no cache for the current article, **Read** generates that paragraph's audio
before playback and then stores it under that voice-specific cache. Use
**Generate audio** again after choosing a new voice if you want the whole article
cached in that voice.

Then use **Voice → Test local TTS** in the article learning toolbar. If the
service is not running, Immerse Learning shows the local endpoint failure reason
and does not automatically switch to the system voice.

## Review, Shadowing, And Media Context

The immersive toolbar adds a second layer of learning capture:

- **Queue** adds the active subtitle sentence to an FSRS-compatible review item
  store and appends an Obsidian note entry to:

```text
ClipLex/Study/Review Queue.md
```

- **Record / Stop** records shadowing audio with the browser `MediaRecorder`
  API. Audio files are saved under:

```text
ClipLex/Media/Shadowing
```

- **Frame** saves timestamped media context into `ClipLex/Study/Media Context.md`.
  Because YouTube iframes are cross-origin, the plugin cannot reliably capture
  the exact video frame pixels from the embedded player. It stores the timestamp
  URL and YouTube thumbnail fallback instead, which still gives review cards a
  stable visual/source cue.

Run **ClipLex: Open review queue** to review due items. Each review card supports
**Again**, **Hard**, **Good**, and **Easy** ratings. The current implementation
uses an FSRS-compatible data shape (`due`, `stability`, `difficulty`, `reps`,
`lapses`, `state`) so a full upstream FSRS library can replace the lightweight
scheduler without migrating stored cards.

## Dictionary Lookup And Study Records

Click any English word in the synced transcript to open a dictionary card. The
first result comes from the bundled ClipLex local dictionary seed, which follows
the same shape as the app-side ECDICT / DictionaryByGPT4 entries. When network
access is available, the plugin also queries Free Dictionary API:

```text
https://api.dictionaryapi.dev/api/v2/entries/en/{word}
```

Use **Add word** to append an Obsidian-native learning item to:

```text
ClipLex/Study/Word Learning.md
```

Each record includes the word, phonetic text when available, definition,
translation when available, the current subtitle sentence, and a timestamped
YouTube source link. Duplicate clicks on the same word at the same timestamp are
deduplicated by an internal HTML marker.

Use **Mine sentence** from the dictionary card when the full sentence matters
more than the isolated word.

## Output Format

A transcript file with clickable, per-line timestamps:

```md
---
source: "https://www.youtube.com/watch?v=VIDEOID"
video_id: VIDEOID
caption_kind: manual
generator: Immerse Learning
---

# Video title

## Transcript

- [00:00](https://www.youtube.com/watch?v=VIDEOID&t=0s) First line of dialogue
- [00:04](https://www.youtube.com/watch?v=VIDEOID&t=4s) Second line of dialogue
```

With translation enabled, a sibling `… CN.md` file mirrors the timestamps under
a `## 中文翻译` heading so the player can switch languages line-for-line.

## Known Limitation

YouTube has been tightening unauthenticated caption access. This build reduces
that risk by preferring the ClipLex yt-dlp extractor and keeping the original
caption fetcher as a fallback. Some auth-gated, age-restricted, private, or
region-restricted videos can still expose **no usable caption tracks** without
server-side credentials or cookies.

The in-Obsidian player is **desktop only** (the YouTube embed and custom views
are impractical on mobile); transcript fetching and translation stay
cross-platform. Videos that disallow embedding open in your browser instead.

## Source Code

This repository currently carries the distributable plugin files. The compiled
`main.js` has been patched for ClipLex caption extraction and local-model
translation.

## Credits

The InnerTube caption-fetching strategy is adapted from
[ljantzen/obsidian-youtube-transcript](https://github.com/ljantzen/obsidian-youtube-transcript)
(MIT).

## License

Immerse Learning is available for **non-commercial use only**. See
[LICENSE.md](LICENSE.md).

Commercial use, resale, SaaS hosting, paid-client use, marketplace
redistribution, and commercial bundling require prior written permission.
