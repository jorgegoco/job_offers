#!/bin/bash
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH"
cd ~/job_offers
exec uvicorn webapp.main:app --host 0.0.0.0 --port 8000
