#!/usr/bin/env bash
#
# Script COMPLET de desplegament a Pipecat Cloud
# Ús: ./deploy.sh
#
# Fa tot el procés: valida keys, build Docker ARM64, push i deploy.
#
set -euo pipefail

AGENT_NAME="catalan-voice-agent"
SECRET_SET="catalan-voice-agent-secrets"
REGISTRY="ghcr.io"
IMAGE_NAME="polriba1/pipecat-cat-minimax"
VERSION="latest"
IMAGE="${REGISTRY}/${IMAGE_NAME}:${VERSION}"
REGION="eu-central"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "==========================================================="
echo "  Desplegament Agent de Veu en Catala - Pipecat Cloud"
echo "==========================================================="
echo ""

# ----------------------------------------------------------
# 0. Verificar prerequisits
# ----------------------------------------------------------
echo -e "${YELLOW}[0/6]${NC} Verificant prerequisits..."

for cmd in docker uv; do
    if ! command -v "$cmd" &> /dev/null; then
        echo -e "${RED}ERROR:${NC} '$cmd' no trobat. Instal·la'l primer."
        exit 1
    fi
done

if ! docker info &> /dev/null; then
    echo -e "${RED}ERROR:${NC} Docker daemon no esta corrent. Executa 'docker' o 'Docker Desktop'."
    exit 1
fi

# Instal·lar CLI si cal
if ! command -v pipecat &> /dev/null; then
    echo "  Instal·lant pipecat-ai-cli..."
    uv tool install pipecat-ai-cli
fi

echo -e "  ${GREEN}OK${NC}"

# ----------------------------------------------------------
# 1. Verificar .env
# ----------------------------------------------------------
echo -e "${YELLOW}[1/6]${NC} Verificant API keys..."

if [ ! -f .env ]; then
    echo -e "${RED}ERROR:${NC} No s'ha trobat .env"
    echo "  Executa: cp env.example .env  (i omple les claus)"
    exit 1
fi

REQUIRED_KEYS=("DEEPGRAM_API_KEY" "GROQ_API_KEY" "MINIMAX_API_KEY" "MINIMAX_GROUP_ID")
for key in "${REQUIRED_KEYS[@]}"; do
    val=$(grep "^${key}=" .env | cut -d'=' -f2- | tr -d '"' | tr -d "'")
    if [ -z "$val" ] || [ "$val" = "your_key_here" ]; then
        echo -e "${RED}ERROR:${NC} $key no configurat a .env"
        exit 1
    fi
    echo -e "  ${GREEN}✓${NC} $key configurat"
done

# ----------------------------------------------------------
# 2. Test rapid de connectivitat API
# ----------------------------------------------------------
echo -e "${YELLOW}[2/6]${NC} Testejant connectivitat APIs..."

GROQ_KEY=$(grep "^GROQ_API_KEY=" .env | cut -d'=' -f2- | tr -d '"' | tr -d "'")
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer ${GROQ_KEY}" \
    "https://api.groq.com/openai/v1/models" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "  ${GREEN}✓${NC} Groq API accessible"
else
    echo -e "  ${YELLOW}AVÍS:${NC} Groq API retorna HTTP $HTTP_CODE (pot ser normal si la key te restriccions)"
fi

# ----------------------------------------------------------
# 3. Login a Pipecat Cloud
# ----------------------------------------------------------
echo -e "${YELLOW}[3/6]${NC} Login a Pipecat Cloud..."
echo "  (S'obrira el navegador per autenticar-te)"
pipecat cloud auth login

# ----------------------------------------------------------
# 4. Configurar secrets
# ----------------------------------------------------------
echo -e "${YELLOW}[4/6]${NC} Pujant secrets a Pipecat Cloud..."
pipecat cloud secrets set "$SECRET_SET" --file .env
echo -e "  ${GREEN}OK${NC} Secrets configurats com '$SECRET_SET'"

# ----------------------------------------------------------
# 5. Build i Push de la imatge Docker
# ----------------------------------------------------------
echo -e "${YELLOW}[5/6]${NC} Build i push de la imatge Docker (ARM64)..."
echo "  Imatge: $IMAGE"

# Login al registry
echo "  Login a $REGISTRY..."
docker login "$REGISTRY"

# Build ARM64 + push
echo "  Construint per linux/arm64 (pot trigar uns minuts)..."
docker buildx create --name pipecat-builder --use 2>/dev/null || docker buildx use pipecat-builder 2>/dev/null || true
docker buildx build \
    --platform=linux/arm64 \
    -t "$IMAGE" \
    --push \
    .

echo -e "  ${GREEN}OK${NC} Imatge pujada a $IMAGE"

# ----------------------------------------------------------
# 6. Deploy a Pipecat Cloud
# ----------------------------------------------------------
echo -e "${YELLOW}[6/6]${NC} Desplegant a Pipecat Cloud..."
pipecat cloud deploy
echo ""
echo -e "${GREEN}==========================================================="
echo "  DESPLEGAMENT COMPLETAT!"
echo "===========================================================${NC}"
echo ""
echo "Per iniciar una sessio:"
echo "  pipecat cloud agent start $AGENT_NAME --use-daily"
echo ""
echo "Per veure logs:"
echo "  pipecat cloud agent logs $AGENT_NAME"
echo ""
echo "Per aturar:"
echo "  pipecat cloud agent stop $AGENT_NAME"
echo ""
