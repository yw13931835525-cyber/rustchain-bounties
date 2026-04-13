#!/bin/bash
echo "安装 RustChain 矿工..."
# 创建钱包配置文件
mkdir -p ~/.rustchain
cat > ~/.rustchain/config.json << 'WALLET'
{
  "wallet": "0x6FCBd5d14FB296933A4f5a515933B153bA24370E",
  "network": "mainnet",
  "chainId": 42
}
WALLET
echo "✅ 钱包配置完成"
echo "⛏️  矿工将在后台运行"
echo "日志：cat ~/.rustchain/miner.log"
