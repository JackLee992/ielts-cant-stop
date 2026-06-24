#!/usr/bin/env python3
"""OpenAI-compatible local Kokoro TTS server for Immerse Learning."""

from __future__ import annotations

import argparse
import io
import json
import logging
import os
import shutil
import subprocess
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


DEFAULT_MODEL_PATH = Path("~/.cache/immerse-learning/kokoro/kokoro-v1.0.int8.onnx").expanduser()
DEFAULT_VOICES_PATH = Path("~/.cache/immerse-learning/kokoro/voices-v1.0.bin").expanduser()
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8880
DEFAULT_VOICE = "reader_warm"
DEFAULT_LANG = "en-us"
VOICE_PRESETS = {
    "reader_warm": {"kokoro": "af_heart", "system": "Samantha"},
    "reader_clear": {"kokoro": "af_sky", "system": "Daniel"},
    "reader_british": {"kokoro": "bf_emma", "system": "Daniel"},
    "reader_relaxed": {"kokoro": "bm_lewis", "system": "Moira"},
}
KOKORO_TO_SYSTEM_VOICE = {
    "af_sky": "Samantha",
    "af_heart": "Samantha",
    "af_bella": "Karen",
    "bf_emma": "Daniel",
    "bf_isabella": "Tessa",
    "bm_lewis": "Daniel",
    "am_adam": "Rishi",
    "am_echo": "Daniel",
}
SYSTEM_TO_KOKORO_VOICE = {
    "Samantha": "af_sky",
    "Daniel": "bm_lewis",
    "Karen": "af_bella",
    "Moira": "bf_emma",
    "Tessa": "bf_isabella",
    "Rishi": "am_adam",
}
SYSTEM_VOICE_FALLBACKS = ["Samantha", "Daniel", "Karen", "Moira", "Tessa", "Rishi"]


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def _parse_speed(value: Any) -> float:
    try:
        speed = float(value)
    except (TypeError, ValueError):
        speed = 1.0
    return max(0.5, min(2.0, speed))


def patch_kokoro_speed_input_dtype(kokoro_class: Any) -> None:
    if getattr(kokoro_class, "_immerse_speed_input_dtype_patched", False):
        return
    original_create_audio = getattr(kokoro_class, "_create_audio", None)
    if not callable(original_create_audio):
        return

    def _create_audio(self: Any, phonemes: str, voice: Any, speed: float) -> tuple[Any, int]:
        input_names = [model_input.name for model_input in self.sess.get_inputs()]
        if "input_ids" not in input_names:
            return original_create_audio(self, phonemes, voice, speed)

        import numpy as np
        from kokoro_onnx.config import MAX_PHONEME_LENGTH, SAMPLE_RATE

        if len(phonemes) > MAX_PHONEME_LENGTH:
            logging.warning("Phonemes are too long, truncating to %s phonemes", MAX_PHONEME_LENGTH)
        phonemes = phonemes[:MAX_PHONEME_LENGTH]
        tokens = np.array(self.tokenizer.tokenize(phonemes), dtype=np.int64)
        assert len(tokens) <= MAX_PHONEME_LENGTH, (
            f"Context length is {MAX_PHONEME_LENGTH}, but leave room for the pad token 0 at the start & end"
        )
        voice = voice[len(tokens)]
        inputs = {
            "input_ids": np.array([[0, *tokens.tolist(), 0]], dtype=np.int64),
            "style": np.array(voice, dtype=np.float32),
            "speed": np.array([speed], dtype=np.float32),
        }
        audio = self.sess.run(None, inputs)[0]
        audio = normalize_kokoro_audio_for_wav(audio)
        return audio, SAMPLE_RATE

    kokoro_class._create_audio = _create_audio
    kokoro_class._immerse_speed_input_dtype_patched = True


def normalize_kokoro_audio_for_wav(audio: Any) -> Any:
    import numpy as np

    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim == 2 and audio.shape[0] == 1:
        return audio.reshape(-1)
    return audio


class KokoroSpeechHandler(BaseHTTPRequestHandler):
    server: "KokoroSpeechServer"

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.end_headers()

    def do_GET(self) -> None:
        if self.path != "/health":
            self._send_json(404, {"error": "not_found"})
            return
        self._send_json(
            200,
            {
                "status": "ok",
                "model": "kokoro",
                "mode": self.server.mode,
                "endpoint": "/v1/audio/speech",
                "defaultVoice": self.server.default_voice,
                "defaultLanguage": self.server.default_lang,
                "modelPath": str(self.server.model_path),
                "voicesPath": str(self.server.voices_path),
            },
        )

    def do_POST(self) -> None:
        if self.path != "/v1/audio/speech":
            self._send_json(404, {"error": "not_found"})
            return
        try:
            payload = self._read_json_body()
            wav = self.server.create_speech(payload)
            self._send_wav(wav)
        except ValueError as error:
            self._send_json(400, {"error": str(error)})
        except AssertionError as error:
            self._send_json(400, {"error": str(error)})
        except Exception as error:  # pragma: no cover - surfaced to Obsidian.
            logging.exception("Failed to create Kokoro speech")
            self._send_json(500, {"error": str(error)})

    def log_message(self, message: str, *args: Any) -> None:
        logging.info("%s - %s", self.address_string(), message % args)

    def _read_json_body(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            raise ValueError("Request body is required.")
        raw = self.rfile.read(content_length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError("Request body must be valid JSON.") from error
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object.")
        return payload

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = _json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_wav(self, body: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class KokoroSpeechServer(ThreadingHTTPServer):
    def __init__(
        self,
        address: tuple[str, int],
        model_path: Path,
        voices_path: Path,
        default_voice: str,
        default_lang: str,
        allow_system_fallback: bool,
    ) -> None:
        self.model_path = model_path
        self.voices_path = voices_path
        self.default_voice = default_voice
        self.default_lang = default_lang
        self.mode = "kokoro"
        self.kokoro = None
        self.soundfile = None
        self.system_voice_names = self._available_system_voice_names()
        system_fallback_ready = self._system_fallback_available()
        if model_path.exists() and voices_path.exists():
            try:
                import soundfile as sf
                from kokoro_onnx import Kokoro

                patch_kokoro_speed_input_dtype(Kokoro)
                logging.info("Loading Kokoro model from %s", model_path)
                self.kokoro = Kokoro(str(model_path), str(voices_path))
                self.soundfile = sf
            except Exception as error:
                if not allow_system_fallback or not system_fallback_ready:
                    raise
                logging.warning("Kokoro is unavailable; using system TTS fallback: %s", error)
                self.mode = "system"
        elif allow_system_fallback and system_fallback_ready:
            logging.info("Kokoro model files are not ready; using system TTS fallback")
            self.mode = "system"
        else:
            validate_model_files(model_path, voices_path)
        super().__init__(address, KokoroSpeechHandler)

    @staticmethod
    def _system_fallback_available() -> bool:
        return bool(shutil.which("say") and shutil.which("afconvert"))

    @staticmethod
    def _available_system_voice_names() -> set[str]:
        say_bin = shutil.which("say")
        if not say_bin:
            return set()
        try:
            result = subprocess.run(
                [say_bin, "-v", "?"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
        except Exception:
            return set()
        voices: set[str] = set()
        for line in result.stdout.splitlines():
            parts = line.split()
            if not parts:
                continue
            locale_index = next((idx for idx, part in enumerate(parts) if "_" in part and len(part) >= 5), None)
            if locale_index is None:
                continue
            voices.add(" ".join(parts[:locale_index]))
        return voices

    def _available_kokoro_voices(self) -> set[str]:
        return set(getattr(self.kokoro.voices, "files", []) or []) if self.kokoro is not None else set()

    def _resolve_kokoro_voice(self, voice: str) -> str:
        requested = str(voice or self.default_voice).strip() or self.default_voice
        preset = VOICE_PRESETS.get(requested)
        candidate = preset["kokoro"] if preset else SYSTEM_TO_KOKORO_VOICE.get(requested, requested)
        available = self._available_kokoro_voices()
        if not available or candidate in available:
            return candidate
        default_candidate = VOICE_PRESETS.get(self.default_voice, {}).get("kokoro", "af_sky")
        if default_candidate in available:
            return default_candidate
        return sorted(available)[0]

    def _resolve_system_voice(self, voice: str) -> str:
        requested = str(voice or self.default_voice).strip() or self.default_voice
        preset = VOICE_PRESETS.get(requested)
        candidate = preset["system"] if preset else KOKORO_TO_SYSTEM_VOICE.get(requested, requested)
        if not self.system_voice_names or candidate in self.system_voice_names:
            return candidate
        for fallback in SYSTEM_VOICE_FALLBACKS:
            if fallback in self.system_voice_names:
                return fallback
        return candidate

    def create_speech(self, payload: dict[str, Any]) -> bytes:
        text = str(payload.get("input") or "").strip()
        if not text:
            raise ValueError("Field `input` is required.")

        voice = str(payload.get("voice") or self.default_voice).strip() or self.default_voice
        lang = str(payload.get("lang") or payload.get("language") or self.default_lang).strip() or self.default_lang
        speed = _parse_speed(payload.get("speed", 1.0))

        if self.mode == "system":
            return self._create_system_speech(text, speed, self._resolve_system_voice(voice))

        if self.kokoro is None or self.soundfile is None:
            raise RuntimeError("Kokoro TTS is not initialized.")
        voice = self._resolve_kokoro_voice(voice)
        audio, sample_rate = self.kokoro.create(text, voice=voice, speed=speed, lang=lang)
        audio = normalize_kokoro_audio_for_wav(audio)
        output = io.BytesIO()
        self.soundfile.write(output, audio, sample_rate, format="WAV")
        return output.getvalue()

    def _create_system_speech(self, text: str, speed: float, system_voice: str) -> bytes:
        say_bin = shutil.which("say")
        afconvert_bin = shutil.which("afconvert")
        if not say_bin or not afconvert_bin:
            raise RuntimeError("System TTS fallback requires macOS `say` and `afconvert`.")
        words_per_minute = str(int(max(90, min(360, 175 * speed))))
        with tempfile.TemporaryDirectory(prefix="immerse-local-tts-") as tmp:
            tmp_dir = Path(tmp)
            text_path = tmp_dir / "input.txt"
            aiff_path = tmp_dir / "speech.aiff"
            wav_path = tmp_dir / "speech.wav"
            text_path.write_text(text, encoding="utf-8")
            say_args = [say_bin, "-r", words_per_minute, "-v", system_voice, "-f", str(text_path), "-o", str(aiff_path)]
            subprocess.run(
                say_args,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            subprocess.run(
                [afconvert_bin, "-f", "WAVE", "-d", "LEI16", str(aiff_path), str(wav_path)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            return wav_path.read_bytes()


def _path_arg(value: str | os.PathLike[str]) -> Path:
    return Path(value).expanduser().resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a local Kokoro TTS server for Immerse Learning.")
    parser.add_argument("--host", default=os.environ.get("KOKORO_TTS_HOST", DEFAULT_HOST))
    parser.add_argument("--port", type=int, default=int(os.environ.get("KOKORO_TTS_PORT", DEFAULT_PORT)))
    parser.add_argument(
        "--model-path",
        type=_path_arg,
        default=_path_arg(os.environ.get("KOKORO_MODEL_PATH", str(DEFAULT_MODEL_PATH))),
    )
    parser.add_argument(
        "--voices-path",
        type=_path_arg,
        default=_path_arg(os.environ.get("KOKORO_VOICES_PATH", str(DEFAULT_VOICES_PATH))),
    )
    parser.add_argument("--default-voice", default=os.environ.get("KOKORO_TTS_VOICE", DEFAULT_VOICE))
    parser.add_argument("--default-lang", default=os.environ.get("KOKORO_TTS_LANG", DEFAULT_LANG))
    parser.add_argument("--allow-system-fallback", action="store_true")
    parser.add_argument("--log-level", default=os.environ.get("KOKORO_TTS_LOG_LEVEL", "INFO"))
    return parser.parse_args()


def validate_model_files(model_path: Path, voices_path: Path) -> None:
    missing = [str(path) for path in (model_path, voices_path) if not path.exists()]
    if missing:
        raise SystemExit(
            "Missing Kokoro model file(s): "
            + ", ".join(missing)
            + ". Download kokoro-v1.0.int8.onnx and voices-v1.0.bin first."
        )


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, str(args.log_level).upper(), logging.INFO), format="%(levelname)s %(message)s")
    server = KokoroSpeechServer(
        (args.host, args.port),
        model_path=args.model_path,
        voices_path=args.voices_path,
        default_voice=args.default_voice,
        default_lang=args.default_lang,
        allow_system_fallback=args.allow_system_fallback,
    )
    logging.info("Local TTS ready at http://%s:%s/v1/audio/speech (%s mode)", args.host, args.port, server.mode)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Stopping Kokoro TTS server")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
