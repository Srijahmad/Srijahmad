#!/bin/bash
RESTART_COUNT=0

while true; do
    RESTART_COUNT=$((RESTART_COUNT + 1))
    echo ">>> [#$RESTART_COUNT] بدء تشغيل البوت - $(date)"
    python main.py
    EXIT_CODE=$?
    echo ">>> البوت توقف (كود: $EXIT_CODE) - إعادة التشغيل فوراً..."
    sleep 1
done
