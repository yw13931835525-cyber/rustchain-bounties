#!/bin/bash
# RustChain Miner 安装脚本

WALLET="0x6FCBd5d14FB296933A4f5a515933B153bA24370E"

echo "🔧 开始安装 RustChain Miner..."

# 下载并安装
curl -fsSL https://rustchain.org/install.sh | bash -s -- --wallet $WALLET

echo "✅ 安装完成！"
echo "📝 日志文件：~/.rustchain/miner.log"
echo "💰 钱包地址：$WALLET"
echo "⏱️  运行时间：24 小时"
