#!/bin/bash
set -e  # Exit on first error

trap 'echo "❌ Pipeline failed at step $(basename ${BASH_SOURCE[0]})"; exit 1' ERR

echo "================================================="
echo "🚀 STARTING SLIDE GENERATION PIPELINE"
echo "================================================="

echo ""
echo "[1/3] 📝 Parsing content.txt → building slide config..."
if ! /usr/bin/python3 build_config.py; then
    echo "❌ Failed to build config"
    exit 1
fi

echo ""
echo "[2/3] 🖼  Downloading & validating images..."
if ! /usr/bin/python3 bulk_download.py; then
    echo "❌ Failed to download images"
    exit 1
fi

echo ""
echo "[3/3] 🎨 Rendering slides to PNG..."
if ! node generate-slides.js; then
    echo "❌ Failed to generate slides"
    exit 1
fi

echo ""
echo "================================================="
echo "✅ SUCCESS! Slides ready in ./output/gym/"
echo "================================================="
echo ""
echo "Next step: Run batch-schedule.js to post to TikTok"
echo "  $ TIKTOK_INTEGRATION_ID=<id> node batch-schedule.js"
