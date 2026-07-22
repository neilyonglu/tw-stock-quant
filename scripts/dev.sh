#!/usr/bin/env bash
# 一次啟動中台（data_service，port 8001）+ 前端（Next.js，port 3000）。
# Ctrl+C 會把兩個都一起關掉。
set -e
cd "$(dirname "$0")/.."

trap 'kill 0' EXIT

uv run uvicorn data_service.main:app --reload --port 8001 &
(cd frontend && npm run dev) &

wait
