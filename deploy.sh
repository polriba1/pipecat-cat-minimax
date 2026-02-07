#!/usr/bin/env bash
#
# Script de desplegament a Pipecat Cloud
# Ús: ./deploy.sh
#
set -euo pipefail

AGENT_NAME="catalan-voice-agent"
SECRET_SET="catalan-voice-agent-secrets"
IMAGE="ghcr.io/polriba1/pipecat-cat-minimax:latest"

echo "=== Desplegament de l'agent de veu en català ==="
echo ""

# 1. Verificar que pipecat CLI està instal·lat
if ! command -v pipecat &> /dev/null; then
    echo "Instal·lant pipecat-ai-cli..."
    uv tool install pipecat-ai-cli
fi

# 2. Verificar autenticació
echo "[1/4] Verificant autenticació a Pipecat Cloud..."
pipecat cloud auth login 2>/dev/null || {
    echo "Cal iniciar sessió a Pipecat Cloud."
    pipecat cloud auth login
}

# 3. Configurar secrets
echo "[2/4] Configurant secrets..."
if [ -f .env ]; then
    pipecat cloud secrets set "$SECRET_SET" --file .env
    echo "  Secrets configurats des de .env"
else
    echo "  ERROR: No s'ha trobat el fitxer .env"
    echo "  Copia env.example a .env i omple les API keys:"
    echo "    cp env.example .env"
    exit 1
fi

# 3. Build i push de la imatge (si Docker disponible)
echo "[3/4] Build i push de la imatge Docker..."
if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo "  Construint imatge per ARM64..."
    docker buildx build --platform=linux/arm64 -t "$IMAGE" --push .
else
    echo "  Docker no disponible localment."
    echo "  La imatge es construeix automàticament via GitHub Actions."
    echo "  Fes push al repo i espera que el workflow acabi."
    echo "  Imatge: $IMAGE"
fi

# 4. Desplegar
echo "[4/4] Desplegant a Pipecat Cloud..."
pipecat cloud deploy "$AGENT_NAME" "$IMAGE" \
    --secrets "$SECRET_SET" \
    --profile agent-1x \
    --region eu-central

echo ""
echo "=== Desplegament completat! ==="
echo ""
echo "Per iniciar l'agent:"
echo "  pipecat cloud agent start $AGENT_NAME --use-daily"
echo ""
echo "Per veure logs:"
echo "  pipecat cloud agent logs $AGENT_NAME"
