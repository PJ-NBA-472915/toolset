#!/bin/bash
nohup venv/bin/python src/cli/app.py start > /dev/null 2>&1 &
echo $! > .api.pid
