#!/bin/bash

# Activate conda environment
source $(conda info --base)/etc/profile.d/conda.sh
conda activate asr

echo "Installing Vietnamese Text Normalizer Packages..."
echo "=================================================="

# Install basic dependencies
echo -e "\n[1/5] Installing pandas and tabulate..."
pip install pandas tabulate

# Install soe-vinorm
echo -e "\n[2/5] Installing soe-vinorm..."
pip install soe-vinorm

# Install Viphoneme
echo -e "\n[3/5] Installing Viphoneme..."
pip install viphoneme

# Install sea-g2p
echo -e "\n[4/5] Installing sea-g2p..."
pip install sea-g2p

# Install NeMo text processing
echo -e "\n[5/5] Installing NeMo text processing..."
pip install nemo_text_processing

echo -e "\n=================================================="
echo "Installation complete!"
echo "Run: ./run_comparison.sh"
