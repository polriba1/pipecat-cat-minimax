# Instruccions de Desplegament Completes

## Objectiu

Desplegar un agent de veu en català a Pipecat Cloud amb aquest stack:
- **STT**: Deepgram Nova-3 (idioma: català `ca`)
- **LLM**: Llama 3.3 70B Versatile via Groq
- **TTS**: MiniMax Speech 2.6 Turbo (idioma: català, `Language.CA`)

## Prerequisits

Necessites tenir instal·lat:
1. **Python 3.10+** (recomanat 3.12)
2. **uv** (gestor de paquets Python) - `pip install uv` o `curl -LsSf https://astral.sh/uv/install.sh | sh`
3. **Docker Desktop** (amb Docker Buildx) - necessari per builds ARM64
4. Compte a **Pipecat Cloud** (https://pipecat.daily.co) - necessita billing configurat
5. Compte a **GitHub** (per GitHub Container Registry - ghcr.io)

## Estructura del Projecte

```
pipecat-cat-minimax/
├── bot.py                  # Agent principal (entry point per Pipecat Cloud)
├── pyproject.toml          # Dependències Python (uv-managed)
├── uv.lock                 # Lock de dependències (120 paquets)
├── Dockerfile              # Container ARM64 amb dailyco/pipecat-base:latest
├── .dockerignore            # Exclou fitxers innecessaris del build
├── pcc-deploy.toml          # Configuració de desplegament a Pipecat Cloud
├── deploy.sh                # Script automatitzat de desplegament
├── test_services.py         # Test de validació de les API keys
├── .env                     # API keys REALS (NO comitejat a git)
├── env.example              # Plantilla de les API keys
└── DEPLOY_INSTRUCTIONS.md   # AQUEST FITXER
```

## Pas 0: Verificar que el .env existeix i té les keys

El fitxer `.env` ja hauria d'existir amb les keys reals. Verifica que conté:

```
DEEPGRAM_API_KEY="4142b3196427d19b..."   (key de Deepgram)
MINIMAX_API_KEY="eyJhbGciOiJSUzI..."     (JWT token de MiniMax)
MINIMAX_GROUP_ID="1994321192248418387"   (Group ID de MiniMax)
GROQ_API_KEY="gsk_wJRIonIfIBY..."        (key de Groq)
```

Si no existeix, copia la plantilla i omple-la:
```bash
cp env.example .env
```

## Pas 1: Instal·lar les eines CLI

```bash
# Instal·lar el CLI de Pipecat
uv tool install pipecat-ai-cli

# Verificar que funciona
pipecat --version
# Hauria de dir: ᓚᘏᗢ Pipecat CLI Version: 0.1.15 (o superior)
```

## Pas 2: Validar que les API keys funcionen

```bash
# Instal·lar dependències locals
uv sync

# Executar tests de connectivitat
uv run test_services.py
```

Hauria de mostrar 4/4 PASS. Si alguna key falla, revisa el `.env`.

## Pas 3: Login a Pipecat Cloud

```bash
pipecat cloud auth login
```

Això obrirà el navegador. Inicia sessió amb el teu compte de https://pipecat.daily.co.
Has de tenir billing configurat al compte.

## Pas 4: Pujar els secrets a Pipecat Cloud

```bash
pipecat cloud secrets set catalan-voice-agent-secrets --file .env
```

Verifica que s'han pujat:
```bash
pipecat cloud secrets list catalan-voice-agent-secrets
```

## Pas 5: Login a GitHub Container Registry (ghcr.io)

Necessites un **Personal Access Token (PAT)** de GitHub amb permisos `write:packages`.

1. Ves a GitHub > Settings > Developer settings > Personal access tokens > Tokens (classic)
2. Crea un token amb permís `write:packages`
3. Login:

```bash
echo "EL_TEU_GITHUB_TOKEN" | docker login ghcr.io -u EL_TEU_USERNAME --password-stdin
```

**ALTERNATIVA: Docker Hub** - Si prefereixes Docker Hub:
1. Canvia `image` a `pcc-deploy.toml` per: `polriba1/catalan-voice-agent:latest`
2. Fes `docker login` amb les teves credencials de Docker Hub
3. Actualitza la variable `IMAGE` a `deploy.sh`

## Pas 6: Construir la imatge Docker (ARM64)

**IMPORTANT**: Pipecat Cloud requereix imatges ARM64 (`linux/arm64`).

```bash
# Crear un builder multi-plataforma (només cal fer-ho un cop)
docker buildx create --name pipecat-builder --use

# Construir i pujar la imatge
docker buildx build \
    --platform=linux/arm64 \
    -t ghcr.io/polriba1/pipecat-cat-minimax:latest \
    --push \
    .
```

Si tens problemes amb buildx, assegura't que Docker Desktop té habilitada
l'opció "Use containerd for pulling and storing images".

**Temps estimat**: 3-5 minuts la primera vegada.

## Pas 7: Desplegar a Pipecat Cloud

```bash
pipecat cloud deploy
```

Això llegeix el `pcc-deploy.toml` i desplega l'agent amb:
- Nom: `catalan-voice-agent`
- Imatge: `ghcr.io/polriba1/pipecat-cat-minimax:latest`
- Secrets: `catalan-voice-agent-secrets`
- Perfil: `agent-1x` (0.5 vCPU, 1 GB RAM)
- Regió: `eu-central`

Verifica l'estat:
```bash
pipecat cloud agent status catalan-voice-agent
```

## Pas 8: Iniciar una sessió i provar l'agent

```bash
pipecat cloud agent start catalan-voice-agent --use-daily
```

Això retornarà una URL de Daily.co. Obre-la al navegador amb micròfon
habilitat i parla en català amb l'agent.

## Script Automatitzat (Tot en un)

Si vols fer tots els passos amb una sola comanda:

```bash
chmod +x deploy.sh
./deploy.sh
```

El script fa: verificar prerequisites → validar .env → login Pipecat Cloud
→ pujar secrets → build Docker ARM64 → push → deploy.

## Desenvolupament Local (sense Pipecat Cloud)

Per provar l'agent localment sense desplegar:

```bash
uv sync
uv run bot.py
```

Això obrirà `http://localhost:7860` al navegador amb una interfície WebRTC.

## Resolució de Problemes

### "exec format error" durant el build
→ Assegura't d'usar `--platform=linux/arm64` amb `docker buildx build`.
→ Docker Desktop ha de tenir habilitada l'emulació multi-plataforma.

### "no match for platform in manifest"
→ La imatge base `dailyco/pipecat-base:latest` és ARM64-only.
→ Has d'usar `docker buildx` (no `docker build` normal).

### "Could not validate credentials" a Pipecat Cloud
→ Executa `pipecat cloud auth login` de nou.

### L'agent no respon en català
→ Verifica que `language="ca"` està configurat al DeepgramSTTService.
→ Verifica que `Language.CA` està configurat al MiniMaxHttpTTSService.
→ El system prompt ja indica al LLM que respongui en català.

### Error de MiniMax "invalid group_id"
→ Verifica que `MINIMAX_GROUP_ID` al .env és correcte (va a la plataforma MiniMax > Account).

## Notes Tècniques

### Patró Bot Runner
El `bot.py` segueix el patró oficial de Pipecat Cloud amb 3 funcions:
1. `run_bot(transport, runner_args)` - Lògica del pipeline (transport-agnostic)
2. `bot(runner_args)` - Entry point que Pipecat Cloud crida
3. `if __name__ == "__main__": main()` - Per execució local

### Pipeline de Processament
```
Micròfon → [Transport Input] → [Deepgram STT ca] → [Context Aggregator User]
→ [Groq Llama 3.3 70B] → [MiniMax TTS 2.6 Catalan] → [Transport Output] → Altaveu
→ [Context Aggregator Assistant]
```

### Versions Rellevants
- pipecat-ai: 0.0.101
- Deepgram model: nova-3
- Groq model: llama-3.3-70b-versatile
- MiniMax model: speech-2.6-turbo
- Language: ca (Catalan) mapejat a "Catalan" per MiniMax
