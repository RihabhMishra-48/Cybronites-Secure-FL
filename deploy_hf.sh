#!/bin/bash
# AI Guardian: Automated HF Space Deployment

echo "AI GUARDIAN | STARTING CLOUD DEPLOYMENT..."

cd deployment_hf

# Ensure branch is main
git branch -M main

# Attempt to push
echo "AI GUARDIAN | PUSHING TO HUGGING FACE (requires Access Token)..."
git push -u huggingface main --force

echo "AI GUARDIAN | PUSH COMPLETE. VERIFY AT: https://huggingface.co/spaces/mdark4025/Cybronites"
