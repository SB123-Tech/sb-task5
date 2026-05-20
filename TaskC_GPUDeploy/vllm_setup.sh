#!/bin/bash
# vLLM 服务器环境配置脚本
# 在云端 GPU 服务器（如 RTX 3090）上运行

set -e

echo "========================================"
echo "  vLLM 部署环境配置"
echo "========================================"

# 检查 GPU
echo -e "\n[1/5] 检查 GPU..."
nvidia-smi

# 检查 Python
echo -e "\n[2/5] 检查 Python..."
python3 --version

# 创建虚拟环境
echo -e "\n[3/5] 创建虚拟环境..."
python3 -m venv ~/vllm-env
source ~/vllm-env/bin/activate

# 安装 vLLM
echo -e "\n[4/5] 安装 vLLM..."
pip install --upgrade pip
pip install vllm

# 下载模型（Qwen3-8B）
echo -e "\n[5/5] 下载模型 Qwen3-8B..."
echo "    （约 14GB，首次下载需要几分钟）"
python3 -c "from vllm import LLM; llm = LLM(model='Qwen/Qwen3-8B', load_format='dummy')" 2>/dev/null || \
  python3 -c "from transformers import AutoTokenizer, AutoModelForCausalLM; \
    AutoTokenizer.from_pretrained('Qwen/Qwen3-8B'); \
    AutoModelForCausalLM.from_pretrained('Qwen/Qwen3-8B', device_map='auto')"

echo -e "\n========================================"
echo "  环境配置完成！"
echo "========================================"
echo ""
echo "启动 vLLM 服务："
echo "  source ~/vllm-env/bin/activate"
echo "  python3 -m vllm.entrypoints.openai.api_server \\"
echo "      --model Qwen/Qwen3-8B \\"
echo "      --dtype half \\"
echo "      --max-model-len 4096 \\"
echo "      --host 0.0.0.0 \\"
echo "      --port 8000"
echo ""
echo "服务启动后访问: http://<服务器IP>:8000/v1"
