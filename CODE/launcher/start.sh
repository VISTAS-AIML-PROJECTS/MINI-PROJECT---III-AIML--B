#!/bin/bash
cd "$HOME/echogenesis" || exit 1
source venv/bin/activate
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"

if ! lsof -i :8002 -sTCP:LISTEN -t >/dev/null 2>&1; then
  nohup python -m uvicorn final_app.app:app --host 0.0.0.0 --port 8002 > /tmp/echogenesis.log 2>&1 &
  for i in $(seq 1 60); do
    if curl -s http://127.0.0.1:8002 >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
fi

open http://127.0.0.1:8002
