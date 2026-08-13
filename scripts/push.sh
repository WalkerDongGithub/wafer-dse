#!/bin/bash
# 自动重试 push —— 网络恢复后自动推送
while true; do
    if git push origin main 2>/dev/null; then
        echo "[$(date '+%H:%M:%S')] push succeeded"
        break
    fi
    echo "[$(date '+%H:%M:%S')] push failed, retry in 60s..."
    sleep 60
done
