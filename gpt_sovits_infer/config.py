"""Config and voice profile loading from TOML files at the project root."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Config:
    upstream_path: str
    default_voice: str
    output_dir: str
    default_target_language: str


@dataclass
class Voice:
    name: str
    voice_dir: Path
    gpt_model: Path
    sovits_model: Path
    ref_audio: Path
    ref_text: str
    ref_language: str


def load_config() -> Config:
    cfg_path = PROJECT_ROOT / "config.toml"
    if not cfg_path.exists():
        raise FileNotFoundError(f"config.toml not found at {cfg_path}")
    with open(cfg_path, "rb") as f:
        data = tomllib.load(f)
    return Config(
        upstream_path=data["upstream_path"],
        default_voice=data.get("default_voice", "example"),
        output_dir=data.get("output_dir", "output"),
        default_target_language=data.get("default_target_language", "zh"),
    )


def load_voice(name: str) -> Voice:
    voice_dir = PROJECT_ROOT / "voices" / name
    voice_toml = voice_dir / "voice.toml"
    if not voice_toml.exists():
        raise FileNotFoundError(
            f"No voice '{name}' at {voice_dir} (voice.toml missing). "
            f"Available: {list_voices()}"
        )
    with open(voice_toml, "rb") as f:
        v = tomllib.load(f)
    return Voice(
        name=name,
        voice_dir=voice_dir,
        gpt_model=voice_dir / v["gpt_model"],
        sovits_model=voice_dir / v["sovits_model"],
        ref_audio=voice_dir / v["ref_audio"],
        ref_text=v["ref_text"],
        ref_language=v["ref_language"],
    )


def list_voices() -> list[str]:
    vd = PROJECT_ROOT / "voices"
    if not vd.exists():
        return []
    return sorted(
        d.name for d in vd.iterdir()
        if d.is_dir() and (d / "voice.toml").exists()
    )
