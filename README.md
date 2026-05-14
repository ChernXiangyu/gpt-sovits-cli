# gpt-sovits-infer

A standalone command-line wrapper around **GPT-SoVITS V3** inference. Each voice
is a folder under `voices/` containing a GPT checkpoint, a SoVITS checkpoint, a
short reference clip, and its transcript.

This repo ships **only** the CLI / glue code. It does not redistribute the
GPT-SoVITS code itself, the ~10 GB of pretrained base models, or any voice
weights. All of those are **bring-your-own** — see [Setup](#setup) below.

> **Tested on:** NVIDIA RTX 5090 (Blackwell, compute capability 12.0) with
> CUDA 12.8, on Windows 11. The torch stack is pinned to the `cu128` wheels
> in `pyproject.toml`. Other Blackwell cards should work; older architectures
> will likely need a different torch wheel (edit the `[tool.uv.sources]` /
> `[[tool.uv.index]]` section in `pyproject.toml`).

## Setup

### 1. Get an upstream GPT-SoVITS install

You need a normal GPT-SoVITS V3 install — clone and run upstream's installer:

> https://github.com/RVC-Boss/GPT-SoVITS

Make sure `GPT_SoVITS/pretrained_models/` is populated (it should be after the
official installer runs). You can put the install anywhere on disk.

### 2. Restore `gpt_sovits/`

This repo's `gpt_sovits/` directory is **gitignored** because it's a verbatim
snapshot of upstream subdirs and is too large to redistribute (~850 MB, with
two single files over GitHub's 100 MB cap).

Copy these subdirectories from your upstream install's `GPT_SoVITS/` folder
into a new local `gpt_sovits/` here:

```
<upstream>/GPT_SoVITS/AR/                    ->  gpt_sovits/AR/
<upstream>/GPT_SoVITS/BigVGAN/               ->  gpt_sovits/BigVGAN/
<upstream>/GPT_SoVITS/TTS_infer_pack/        ->  gpt_sovits/TTS_infer_pack/
<upstream>/GPT_SoVITS/configs/               ->  gpt_sovits/configs/
<upstream>/GPT_SoVITS/f5_tts/                ->  gpt_sovits/f5_tts/
<upstream>/GPT_SoVITS/feature_extractor/     ->  gpt_sovits/feature_extractor/
<upstream>/GPT_SoVITS/module/                ->  gpt_sovits/module/
<upstream>/GPT_SoVITS/pretrained_models/fast_langdetect/  ->  gpt_sovits/pretrained_models/fast_langdetect/
<upstream>/GPT_SoVITS/text/                  ->  gpt_sovits/text/
<upstream>/GPT_SoVITS/tools/                 ->  gpt_sovits/tools/
<upstream>/GPT_SoVITS/inference_webui.py     ->  gpt_sovits/inference_webui.py
<upstream>/GPT_SoVITS/process_ckpt.py        ->  gpt_sovits/process_ckpt.py
<upstream>/GPT_SoVITS/utils.py               ->  gpt_sovits/utils.py
```

Symlinking is fine if your OS supports it. The CLI puts `gpt_sovits/` ahead of
the upstream path on `sys.path` at import time, so any local edits in
`gpt_sovits/` take precedence over upstream.

### 3. Configure

```powershell
copy config.example.toml config.toml
# edit config.toml -> set upstream_path to your GPT-SoVITS install
```

### 4. Install dependencies

```powershell
uv sync
```

(One-off, ~5 min including the torch + cu128 download.)

> **Note on `jieba_fast`:** this dep is a C extension and PyPI does not ship a
> Windows wheel for it. `uv sync` will try to build it from sdist, which
> needs Microsoft C++ Build Tools (the "Desktop development with C++"
> workload from the Visual Studio Installer). If you don't want to install
> MSVC, drop a pre-built wheel into `wheels/` — the `[tool.uv]` block in
> `pyproject.toml` already points `find-links` at that directory, so uv will
> pick it up automatically. A wheel built for Python 3.9 / Windows x64 is
> roughly 8 MB; you can either build it yourself in a one-off MSVC env or
> find a community-built one (search "jieba_fast 0.53 cp39 win_amd64
> whl").

### 5. Add a voice

```powershell
xcopy /e /i voices\example voices\myvoice
copy yourmodel.ckpt voices\myvoice\gpt.ckpt
copy yourmodel.pth  voices\myvoice\sovits.pth
copy yourref.wav    voices\myvoice\ref.wav
# edit voices\myvoice\voice.toml: set ref_text and ref_language
uv run gpt-sovits-infer list
```

`voice.toml` minimum:

```toml
gpt_model    = "gpt.ckpt"
sovits_model = "sovits.pth"
ref_audio    = "ref.wav"
ref_text     = "exact transcript of ref_audio"
ref_language = "zh"            # zh | en | ja | ko | yue | auto
```

> ⚠️  You are responsible for the licensing and copyright status of any voice
> models or reference audio you load. Cloning a voice without consent of the
> speaker may be illegal in your jurisdiction.

## Usage

```powershell
uv run gpt-sovits-infer synth "Hello, this is a test" -v myvoice -o output/hello.wav -l en
uv run gpt-sovits-infer list
```

Or double-click **`run.bat`** with arguments via a Windows shortcut.

## Why is upstream_path needed?

The pretrained base models V3 inference depends on are too large to duplicate
inside `gpt_sovits/pretrained_models/`:

| File                                              | Size    | Role                                         |
| ------------------------------------------------- | ------- | -------------------------------------------- |
| `chinese-roberta-wwm-ext-large/`                  | ~1.3 GB | BERT for text features                       |
| `chinese-hubert-base/`                            | ~1 GB   | cnhubert encoder                             |
| `s2Gv3.pth`                                       | ~1 GB   | V3 SoVITS base (your fine-tune is a LoRA on top) |
| `models--nvidia--bigvgan_v2_24khz_100band_256x/`  | ~150 MB | BigVGAN vocoder                              |
| (plus V1/V2 fallbacks)                            |         |                                              |

`config.toml`'s `upstream_path` points to a GPT-SoVITS install that has these
in its `GPT_SoVITS/pretrained_models/` subtree. At startup the CLI `chdir`'s
into that path so all of upstream's hard-coded relative paths resolve
correctly, and adds `gpt_sovits/` to `sys.path` ahead of upstream's so any
local patches take precedence.

## Layout

```
.
├── pyproject.toml          # uv project + dep pins (torch cu128, etc.)
├── config.example.toml     # copy to config.toml and edit
├── gpt_sovits_infer/       # this project's CLI + bootstrap + thin inference wrapper
├── gpt_sovits/             # vendored upstream snapshot (gitignored; restore per Setup)
├── wheels/                 # local drop-zone for wheels without PyPI Windows builds (jieba_fast); gitignored
├── voices/example/         # voice profile template (real profiles gitignored)
└── output/                 # generated wavs (gitignored)
```

## Troubleshooting

- **`FileNotFoundError ... pretrained_models`**: edit `upstream_path` in `config.toml`.
- **`ModuleNotFoundError: inference_webui` or similar**: `gpt_sovits/` isn't populated — redo Setup step 2.
- **NLTK `cmudict not found`**: run `uv run python -c "import nltk; nltk.download('cmudict'); nltk.download('averaged_perceptron_tagger_eng')"` once. The English G2P (`g2p_en`) needs these for English text.
- **Stuck at `0% [00:00<?]` in T2S sampling**: PyTorch can't address the GPU. Confirm with `uv run python -c "import torch; print(torch.cuda.get_device_capability())"` — must be your card's capability (e.g. `(12, 0)` for RTX 5090). If wrong, the cu128 wheel didn't install cleanly.

## License

MIT. See [LICENSE](LICENSE). The vendored `gpt_sovits/` subtree (not shipped
in this repo, restored locally per Setup) is also MIT, from
[RVC-Boss/GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS); third-party
components under `gpt_sovits/BigVGAN/incl_licenses/` retain their original
licenses.
