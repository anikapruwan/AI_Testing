#!/bin/bash

# Advanced RAG Setup Script

echo "Setting up Advanced RAG Environment..."

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Download sample models (this will cache them for faster loading)
echo "Downloading sample models..."
python3 -c "
from sentence_transformers import SentenceTransformer
print('Downloading BGE model...')
SentenceTransformer('BAAI/bge-small-en-v1.5')
print('Downloading re-ranker model...')
SentenceTransformer('cross-encoder/ms-marco-MiniLM-L-6-v2')
print('Models downloaded successfully!')
"

echo "Setup complete!"
echo "To activate the environment, run: source venv/bin/activate"