"""gpt-sovits-infer: CLI entry point.

Usage:
  gpt-sovits-infer synth "你好"                          # default voice from config.toml
  gpt-sovits-infer synth "Hello" -v myvoice -o hi.wav -l en
  gpt-sovits-infer synth --text-file in.txt -o out.wav
  gpt-sovits-infer list                                  # show available voices
"""
from pathlib import Path
import typer

app = typer.Typer(add_completion=False, help="GPT-SoVITS V3 inference CLI", no_args_is_help=True)


@app.command()
def synth(
    text: str = typer.Argument(None, help="Target text. If omitted, --text-file is required."),
    voice: str = typer.Option(None, "-v", "--voice", help="Voice name (defaults to config)"),
    output: Path = typer.Option(Path("output/out.wav"), "-o", "--output", help="Output wav path (relative to project root)"),
    lang: str = typer.Option(None, "-l", "--lang", help="Target language: zh (Chinese / Chinese+English mixed) or en"),
    text_file: Path = typer.Option(None, "--text-file", help="Read target text from file instead"),
    top_k: int = typer.Option(20, "--top-k"),
    top_p: float = typer.Option(0.6, "--top-p"),
    temperature: float = typer.Option(0.6, "--temperature"),
    speed: float = typer.Option(1.0, "--speed"),
    sample_steps: int = typer.Option(32, "--sample-steps", help="V3 CFM sample steps (4/8/16/32)"),
):
    """Synthesize speech from text using a voice profile."""
    from . import config as _cfg
    from . import bootstrap

    cfg = _cfg.load_config()
    # Resolve paths to absolute BEFORE bootstrap.setup() chdir's to upstream,
    # otherwise relative paths land in upstream's directory.
    output = output.expanduser().resolve()
    if text_file is not None:
        text_file = text_file.expanduser().resolve()

    upstream = bootstrap.setup(cfg.upstream_path)
    typer.echo(f"Upstream: {upstream}")

    from . import inference  # imports vendored inference_webui (loads BERT, etc.)

    if text_file is not None:
        text = text_file.read_text(encoding="utf-8")
    if not text:
        raise typer.BadParameter("Provide TEXT positionally or --text-file <path>")

    voice_name = voice or cfg.default_voice
    v = _cfg.load_voice(voice_name)
    target_lang = lang or cfg.default_target_language

    typer.echo(f"Voice: {voice_name}  (gpt={v.gpt_model.name}, sovits={v.sovits_model.name})")
    inference.load_voice_models(v.gpt_model, v.sovits_model)

    typer.echo(f"Synthesizing {len(text)} chars (lang={target_lang}) -> {output}")
    sr, audio = inference.synthesize(
        text=text,
        ref_audio=v.ref_audio,
        ref_text=v.ref_text,
        ref_language=v.ref_language,
        target_language=target_lang,
        top_k=top_k,
        top_p=top_p,
        temperature=temperature,
        speed=speed,
        sample_steps=sample_steps,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    inference.save_wav(output, sr, audio)
    duration = len(audio) / sr
    typer.echo(f"OK: wrote {output}  {duration:.2f}s @ {sr}Hz")


@app.command("list")
def list_cmd():
    """List available voices."""
    from . import config as _cfg
    voices = _cfg.list_voices()
    if not voices:
        typer.echo("No voices defined under voices/")
        raise typer.Exit(code=1)
    for v in voices:
        typer.echo(f"- {v}")
