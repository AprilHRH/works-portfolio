#!/usr/bin/env bash
# ============================================================
# FableDevil — Ubuntu 一次性部署脚本
# 用法:  bash deploy/setup.sh
# 前提:  Node.js 已安装; 项目文件已上传到服务器
# 作用:  装 PM2 → 装依赖 → 启动/重载服务 → 保存进程列表
# ============================================================
set -euo pipefail

# 切到项目根目录(无论从哪里调用)
cd "$(cd "$(dirname "$0")" && pwd)/.."

PORT="${PORT:-666}"

echo "==> 1/4 检查 Node"
command -v node >/dev/null || { echo "❌ 未检测到 node,请先安装 Node.js (>=18)"; exit 1; }
echo "    node $(node -v)"

echo "==> 2/4 安装 PM2(如未安装)"
if ! command -v pm2 >/dev/null 2>&1; then
  npm install -g pm2
fi
echo "    pm2 $(pm2 -v)"

echo "==> 3/4 安装依赖(可选 — server.js 仅用内置模块)"
npm install --omit=dev || echo "    ⚠️ 依赖安装失败可忽略,服务不依赖 node_modules"

echo "==> 4/4 启动 / 重载 FableDevil (端口 ${PORT})"
PORT="$PORT" pm2 startOrReload ecosystem.config.js --update-env
pm2 save

echo
echo "✅ 已启动:  http://<服务器IP>:${PORT}/"
echo
echo "👉 开机自启(执行后按它输出的 sudo 命令再跑一次):"
echo "   pm2 startup systemd"
echo
echo "常用命令:"
echo "   状态:  pm2 status"
echo "   日志:  pm2 logs fabledevil"
echo "   重启:  pm2 restart fabledevil"
echo "   停止:  pm2 stop fabledevil"
