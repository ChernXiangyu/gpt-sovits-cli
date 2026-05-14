"""Thin wrapper around the vendored `inference_webui.py` functions.

`bootstrap.setup()` MUST be called before importing this module —
importing `inference_webui` triggers BERT/cnhubert path setup and gradio
UI construction.
"""
import numpy as np
import soundfile as sf

import inference_webui as _iw  # noqa: E402  (imported only after bootstrap)

# Our short codes -> upstream's internal language values (the values in
# dict_language). These match what `get_phones_and_bert(text, language, ...)`
# expects internally.
_SHORT_TO_RAW = {
    "zh": "all_zh",      # all-Chinese
    "en": "en",
    "ja": "all_ja",
    "ko": "all_ko",
    "yue": "all_yue",
    "zh_en": "zh",       # Chinese + English mixed
    "ja_en": "ja",
    "ko_en": "ko",
    "yue_en": "yue",
    "auto": "auto",
    "auto_yue": "auto_yue",
}


def _to_dict_language_key(short: str) -> str:
    """Translate our short code to whatever locale-specific key the upstream
    `dict_language` is using (depends on detected i18n locale).
    """
    raw = _SHORT_TO_RAW.get(short)
    if raw is None:
        raise ValueError(
            f"Unknown language {short!r}. Valid: {sorted(_SHORT_TO_RAW)}"
        )
    for key, val in _iw.dict_language.items():
        if val == raw:
            return key
    raise RuntimeError(
        f"raw code {raw!r} for {short!r} not found in dict_language values "
        f"({list(_iw.dict_language.values())})"
    )

_loaded = {"gpt": None, "sovits": None}


def load_voice_models(gpt_path, sovits_path):
    """Load (or swap) the GPT + SoVITS model pair. SoVITS first so version is set."""
    sovits_path, gpt_path = str(sovits_path), str(gpt_path)
    if _loaded["sovits"] != sovits_path:
        _iw.change_sovits_weights(sovits_path)
        _loaded["sovits"] = sovits_path
    if _loaded["gpt"] != gpt_path:
        _iw.change_gpt_weights(gpt_path)
        _loaded["gpt"] = gpt_path


def synthesize(
    text: str,
    ref_audio,
    ref_text: str,
    ref_language: str,
    target_language: str,
    *,
    how_to_cut: str = "凑四句一切",
    top_k: int = 20,
    top_p: float = 0.6,
    temperature: float = 0.6,
    speed: float = 1.0,
    sample_steps: int = 32,
    pause_second: float = 0.3,
):
    """Run TTS. Returns (sample_rate, int16 audio ndarray)."""
    ref_lang = _to_dict_language_key(ref_language)
    tgt_lang = _to_dict_language_key(target_language)
    gen = _iw.get_tts_wav(
        ref_wav_path=str(ref_audio),
        prompt_text=ref_text,
        prompt_language=ref_lang,
        text=text,
        text_language=tgt_lang,
        how_to_cut=how_to_cut,
        top_k=top_k,
        top_p=top_p,
        temperature=temperature,
        speed=speed,
        sample_steps=sample_steps,
        pause_second=pause_second,
    )
    chunks = list(gen)
    if not chunks:
        raise RuntimeError("get_tts_wav produced no output")
    sr, audio = chunks[-1]
    return sr, audio


def save_wav(path, sr: int, audio: np.ndarray):
    sf.write(str(path), audio, sr)
