#!/usr/bin/env bash
# Day 11 Vast.ai instance bootstrap.
# Run as root on Ubuntu 22.04 RTX 4090 instance immediately after provisioning.
# Usage: bash day11_vastai_setup.sh
set -euo pipefail

echo "[$(date -u +%H:%M:%S)] Starting Day 11 Vast.ai setup..."

# System packages
apt-get update -qq
apt-get install -y -qq rsync git

# Upgrade pip
python3 -m pip install --upgrade pip --quiet

# Core ML stack (CUDA 12.1, torch 2.4)
pip install --quiet \
    "torch==2.4.0" \
    "torchvision==0.19.0" \
    --index-url https://download.pytorch.org/whl/cu121

# PDF processing (pymupdf ships as fitz)
pip install --quiet "pymupdf==1.24.10"

# ColPali
pip install --quiet "colpali-engine>=0.3.0" "Pillow>=10.0.0"

# Nougat OCR
pip install --quiet "nougat-ocr>=0.1.17"

# DPO training stack
pip install --quiet \
    "trl>=0.9.0" \
    "peft>=0.12.0" \
    "accelerate>=0.34.0" \
    "datasets>=2.20.0" \
    "bitsandbytes>=0.43.0" \
    "huggingface_hub>=0.24.0" \
    "pyyaml"

# Unsloth (CUDA 12.1, torch 2.4 -- install last to avoid dependency clobber)
pip install --quiet "unsloth[cu121-torch240] @ git+https://github.com/unslothai/unsloth.git"

# Utilities
pip install --quiet numpy

echo "[$(date -u +%H:%M:%S)] All packages installed."

# Workspace layout
mkdir -p /data/tcpd /outputs

echo ""
echo "=== SETUP COMPLETE ==="
echo ""
echo "Next steps:"
echo "  1. Upload SSH key if not already done (Vast.ai console > Account > SSH keys)"
echo ""
echo "  2. Upload TCPD PDFs (run locally):"
echo "     rsync -avz --progress cache/tcpd_primegov/ root@<INSTANCE_IP>:/data/tcpd/"
echo ""
echo "  3. Upload day11 script (run locally):"
echo "     scp scripts/day11_colpali_nougat.py root@<INSTANCE_IP>:/root/"
echo ""
echo "  4. Run DPO smoke test (10 steps -- verify numerical stability before full run):"
echo "     HF_TOKEN=hf_... python3 scripts/smoke_test_dpo.py --mode forward"
echo ""
echo "  5. Run full DPO training (produces odia-v3):"
echo "     HF_TOKEN=hf_... python3 scripts/train_dpo.py"
echo "     # Pushes GGUF to HuggingFace SynTechRev/odia-v3-dpo when complete"
echo "     # Beta sweep (Watch 1): re-run with --beta 0.05 / 0.2 / 0.3 if loss does not decrease"
echo ""
echo "  6. Run ColPali phase:"
echo "     python3 scripts/day11_colpali_nougat.py --pdf-dir /data/tcpd --output-dir /outputs --phase colpali"
echo ""
echo "  7. Run Nougat phase:"
echo "     python3 scripts/day11_colpali_nougat.py --pdf-dir /data/tcpd --output-dir /outputs --phase nougat"
echo ""
echo "  8. Verify outputs:"
echo "     python3 scripts/day11_colpali_nougat.py --pdf-dir /data/tcpd --output-dir /outputs --phase verify"
echo ""
echo "  9. Download ColPali outputs (run locally):"
echo "     rsync -avz --progress root@<INSTANCE_IP>:/outputs/ data/vectors/tcpd_colpali/"
echo ""
echo " 10. DESTROY INSTANCE immediately after all downloads confirmed."
echo ""
echo " 11. Run locally (severity_critical RAIA gate -- requires odia-v3 in Ollama):"
echo "     ollama create odia-v3 -f models/Modelfile.v3"
echo "     python -I scripts/raia_severity_critical_gate.py --model odia-v3"
echo ""
echo "OPTIONAL -- pull model weights to local before destroying instance:"
echo "  ColPali weights: ~10 GB -- pull if local disk has room (D: drive check first)"
echo "  Nougat weights:  ~2.5 GB"
echo "  Decision: if either model is targeted as a production integration (Day 11 review),"
echo "  having weights locally cached saves re-download time on next session."
echo ""
echo "  Pull ColPali locally (run on local machine while instance is still up):"
echo "    python -c \"from huggingface_hub import snapshot_download; snapshot_download('vidore/colpali-v1.2', local_dir='models/colpali-v1.2')\""
echo ""
echo "  Pull Nougat locally:"
echo "    python -c \"from huggingface_hub import snapshot_download; snapshot_download('facebook/nougat-base', local_dir='models/nougat-base')\""
echo ""
echo "  VRAM budget estimate:"
echo "    ColPali (vidore/colpali-v1.2):  ~5 GB"
echo "    Nougat (facebook/nougat-base):  ~2 GB"
echo "    Total peak (sequential):        ~7 GB of 24 GB RTX 4090 -- safe margin"
