"""Bootstrap the environment so vendored `inference_webui.py` can be imported safely.

The vendored upstream code assumes:
  - cwd is the upstream GPT-SoVITS project root (so relative paths like
    `GPT_SoVITS/pretrained_models/...` resolve correctly).
  - The directory containing AR/, module/, text/, etc. is on `sys.path`.
  - `gradio` is importable (the module builds a UI block at top-level).

`setup()` makes all three true without bringing gradio in as a real dep.
Call it BEFORE any `import inference_webui`.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VENDORED = PROJECT_ROOT / "gpt_sovits"


class _NoOp:
    """Stand-in for gradio. Every attribute/call/context-manager use returns self."""
    def __init__(self, *a, **kw): pass
    def __call__(self, *a, **kw): return self
    def __getattr__(self, k): return self
    def __getitem__(self, k): return self
    def __setitem__(self, k, v): pass
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def __iter__(self): return iter([])
    def __bool__(self): return False


_STUB_MODULES = (
    # gradio: the vendored inference_webui builds a UI block at module-load time
    "gradio", "gradio.analytics",
)


def _stub_modules():
    """Replace heavy training/UI-only modules with no-op stubs."""
    for name in _STUB_MODULES:
        if name in sys.modules and not isinstance(sys.modules[name], _NoOp):
            continue  # real module is installed; let it run
        sys.modules[name] = _NoOp()


def setup(upstream_path: str | os.PathLike) -> Path:
    """Prepare process state for inference. Returns the resolved upstream path."""
    upstream = Path(upstream_path).expanduser().resolve()
    pretrained = upstream / "GPT_SoVITS" / "pretrained_models"
    if not pretrained.exists():
        raise FileNotFoundError(
            f"upstream_path={upstream} does not contain GPT_SoVITS/pretrained_models/. "
            "Set the correct path in config.toml."
        )
    os.chdir(upstream)
    if str(VENDORED) not in sys.path:
        sys.path.insert(0, str(VENDORED))
    _stub_modules()
    # Force UTF-8 stdout/stderr so upstream print() can output non-GBK chars
    # (e.g. Polish/Czech diacritics in author names like Maćkowiak, Matějka).
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass
    return upstream
