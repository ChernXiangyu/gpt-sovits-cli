@echo off
chcp 65001 >nul
pushd "%~dp0"
uv run gpt-sovits-infer %*
popd
pause
