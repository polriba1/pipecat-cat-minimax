"""
Test script to validate all API keys and services work correctly.
Tests: Deepgram STT, Groq LLM, MiniMax TTS
"""

import asyncio
import os
import sys

import aiohttp
from dotenv import load_dotenv

load_dotenv(override=True)

PASS = "PASS"
FAIL = "FAIL"


async def test_deepgram():
    """Test Deepgram API key is valid."""
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        return FAIL, "DEEPGRAM_API_KEY not set"

    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.deepgram.com/v1/projects",
            headers={"Authorization": f"Token {api_key}"},
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                projects = data.get("projects", [])
                return PASS, f"{len(projects)} project(s) found"
            else:
                text = await resp.text()
                return FAIL, f"HTTP {resp.status}: {text[:100]}"


async def test_groq():
    """Test Groq API key with a small Llama 3.3 70B request."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return FAIL, "GROQ_API_KEY not set"

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "user", "content": "Digues 'hola' en catala. Nomes una paraula."}
                ],
                "max_tokens": 10,
            },
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                content = data["choices"][0]["message"]["content"]
                return PASS, f"Llama 3.3 70B response: '{content.strip()}'"
            else:
                text = await resp.text()
                return FAIL, f"HTTP {resp.status}: {text[:200]}"


async def test_minimax():
    """Test MiniMax TTS API with a short Catalan phrase."""
    api_key = os.getenv("MINIMAX_API_KEY")
    group_id = os.getenv("MINIMAX_GROUP_ID")
    if not api_key:
        return FAIL, "MINIMAX_API_KEY not set"
    if not group_id:
        return FAIL, "MINIMAX_GROUP_ID not set"

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.minimax.io/v1/t2a_v2",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "speech-2.6-turbo",
                "text": "Hola, soc un assistent en catala.",
                "stream": False,
                "voice_setting": {
                    "voice_id": "Calm_Woman",
                    "speed": 1.0,
                    "vol": 1.0,
                    "pitch": 0,
                },
                "audio_setting": {
                    "sample_rate": 24000,
                    "format": "pcm",
                },
                "language_boost": "Catalan",
            },
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("base_resp", {}).get("status_code") == 0:
                    audio_hex = data.get("data", {}).get("audio", "")
                    audio_bytes = len(bytes.fromhex(audio_hex)) if audio_hex else 0
                    return PASS, f"speech-2.6-turbo generated {audio_bytes} bytes of audio in Catalan"
                else:
                    return FAIL, f"API error: {data.get('base_resp', {})}"
            else:
                text = await resp.text()
                return FAIL, f"HTTP {resp.status}: {text[:200]}"


async def test_pipecat_imports():
    """Test that all Pipecat imports work."""
    try:
        from pipecat.services.deepgram.stt import DeepgramSTTService
        from pipecat.services.groq.llm import GroqLLMService
        from pipecat.services.minimax.tts import MiniMaxHttpTTSService
        from pipecat.transcriptions.language import Language
        from pipecat.audio.vad.silero import SileroVADAnalyzer

        assert Language.CA == "ca"
        return PASS, "All Pipecat imports OK, Language.CA verified"
    except Exception as e:
        return FAIL, str(e)


async def main():
    print("=" * 60)
    print("  Validacio de serveis - Agent de Veu en Catala")
    print("=" * 60)
    print()

    tests = [
        ("Pipecat Imports", test_pipecat_imports),
        ("Deepgram STT (Nova-3)", test_deepgram),
        ("Groq LLM (Llama 3.3 70B)", test_groq),
        ("MiniMax TTS (Speech 2.6 Turbo + Catala)", test_minimax),
    ]

    results = []
    for name, test_fn in tests:
        print(f"  Testing {name}...", end=" ", flush=True)
        try:
            status, detail = await test_fn()
        except Exception as e:
            status, detail = FAIL, str(e)
        results.append((name, status, detail))
        print(f"[{status}] {detail}")

    print()
    print("=" * 60)
    passed = sum(1 for _, s, _ in results if s == PASS)
    total = len(results)
    print(f"  Results: {passed}/{total} passed")
    if passed == total:
        print("  Tot correcte! L'agent esta llest per desplegar.")
    else:
        print("  Hi ha errors. Revisa les API keys.")
    print("=" * 60)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
