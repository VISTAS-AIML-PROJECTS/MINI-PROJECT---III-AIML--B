#!/bin/bash
PIDS=$(lsof -ti :8002)
if [ -n "$PIDS" ]; then
  kill -9 $PIDS
  osascript -e 'display notification "EchoGenesis stopped" with title "EchoGenesis"'
else
  osascript -e 'display notification "Nothing was running" with title "EchoGenesis"'
fi
