# Agent de Veu en Català - Pipecat

Agent conversacional de veu en català desplegable a Pipecat Cloud.

## Stack

| Component | Servei | Detall |
|-----------|--------|--------|
| STT | Deepgram | Nova-3, idioma `ca` |
| LLM | Groq | Llama 3.3 70B Versatile |
| TTS | MiniMax | Speech 2.6 Turbo, idioma `Catalan` |
| VAD | Silero | Detecció d'activitat de veu |

## Configuració ràpida

### 1. API Keys

Copia i omple les claus:

```bash
cp env.example .env
```

Necessites:
- `DEEPGRAM_API_KEY` - [console.deepgram.com](https://console.deepgram.com)
- `GROQ_API_KEY` - [console.groq.com](https://console.groq.com)
- `MINIMAX_API_KEY` + `MINIMAX_GROUP_ID` - [platform.minimax.io](https://platform.minimax.io)

### 2. Executar en local

```bash
uv sync
uv run bot.py
```

S'obrirà el navegador a `http://localhost:7860`.

### 3. Desplegar a Pipecat Cloud

#### Opció A: Script automàtic

```bash
./deploy.sh
```

#### Opció B: Pas a pas

```bash
# Instal·lar CLI
uv tool install pipecat-ai-cli

# Login
pipecat cloud auth login

# Secrets
pipecat cloud secrets set catalan-voice-agent-secrets --file .env

# La imatge Docker es construeix automàticament via GitHub Actions
# (push al repo i espera que acabi el workflow)

# Desplegar
pipecat cloud deploy

# Iniciar
pipecat cloud agent start catalan-voice-agent --use-daily
```

## Imatge Docker

La imatge es construeix automàticament via GitHub Actions i es puja a:

```
ghcr.io/polriba1/pipecat-cat-minimax:latest
```

Per construir-la manualment:

```bash
docker buildx build --platform=linux/arm64 -t ghcr.io/polriba1/pipecat-cat-minimax:latest --push .
```

## Estructura del projecte

```
├── bot.py              # Agent principal (entry point)
├── pyproject.toml      # Dependències Python
├── uv.lock             # Lock file
├── Dockerfile          # Container ARM64 per Pipecat Cloud
├── pcc-deploy.toml     # Configuració de desplegament
├── deploy.sh           # Script de desplegament automatitzat
├── env.example         # Plantilla de variables d'entorn
└── .github/workflows/
    └── build-and-push.yml  # CI/CD per build i push de la imatge
```
