#!/usr/bin/env bash
# ============================================================
# FableDevil — 更新部署脚本
# 用法:  bash deploy/update.sh
# 场景:  上传了新代码后,零停机重载服务
# ============================================================
set -euo pipefail

cd "$(cd "$(dirname "$0")" && pwd)/.."

echo "==> 同步依赖(若有变更)"
npm install --omit=dev || true

echo "==> 零停机重载 FableDevil"
pm2 startOrReload ecosystem.config.js --update-env
pm2 save

echo "✅ 完成。查看日志: pm2 logs fabledevil"
