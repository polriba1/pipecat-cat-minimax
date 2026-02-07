"""
Agent de veu en català amb Pipecat.

Stack:
  - STT: Deepgram Nova-3 (català)
  - LLM: Llama 3.3 70B Versatile via Groq
  - TTS: MiniMax Speech 2.6 Turbo (català)
"""

import os

import aiohttp
from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import LLMMessagesFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.groq.llm import GroqLLMService
from pipecat.services.minimax.tts import MiniMaxHttpTTSService
from pipecat.transcriptions.language import Language
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.daily.transport import DailyParams
from deepgram import LiveOptions

load_dotenv(override=True)

SYSTEM_PROMPT = (
    "Ets un assistent d'intel·ligència artificial amable i útil que parla en català. "
    "Respon sempre en català de manera natural i conversacional. "
    "Sigues concís i clar en les teves respostes. "
    "Si l'usuari parla en un altre idioma, respon igualment en català."
)


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    """Pipeline principal de l'agent de veu."""
    async with aiohttp.ClientSession() as session:
        # --- STT: Deepgram Nova-3 amb català ---
        stt = DeepgramSTTService(
            api_key=os.getenv("DEEPGRAM_API_KEY"),
            live_options=LiveOptions(
                model="nova-3",
                language="ca",
                smart_format=True,
            ),
        )

        # --- LLM: Groq amb Llama 3.3 70B Versatile ---
        llm = GroqLLMService(
            api_key=os.getenv("GROQ_API_KEY"),
            model="llama-3.3-70b-versatile",
        )

        # --- TTS: MiniMax Speech 2.6 Turbo amb català ---
        tts = MiniMaxHttpTTSService(
            api_key=os.getenv("MINIMAX_API_KEY"),
            group_id=os.getenv("MINIMAX_GROUP_ID", ""),
            model="speech-2.6-turbo",
            voice_id=os.getenv("MINIMAX_VOICE_ID", "Calm_Woman"),
            aiohttp_session=session,
            params=MiniMaxHttpTTSService.InputParams(
                language=Language.CA,
                speed=1.0,
                volume=1.0,
                pitch=0,
            ),
        )

        # --- Context del LLM ---
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        context = OpenAILLMContext(messages)
        context_aggregator = llm.create_context_aggregator(context)

        # --- Pipeline ---
        pipeline = Pipeline(
            [
                transport.input(),
                stt,
                context_aggregator.user(),
                llm,
                tts,
                transport.output(),
                context_aggregator.assistant(),
            ]
        )

        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                enable_metrics=True,
                enable_usage_metrics=True,
            ),
        )

        @transport.event_handler("on_client_connected")
        async def on_client_connected(transport, client):
            logger.info("Client connectat")
            await task.queue_frames([LLMMessagesFrame(messages)])

        @transport.event_handler("on_client_disconnected")
        async def on_client_disconnected(transport, client):
            logger.info("Client desconnectat")
            await task.cancel()

        runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)
        await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Entry point per Pipecat Cloud i execució local."""
    transport_params = {
        "daily": lambda: DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_enabled=True,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.5)),
        ),
        "webrtc": lambda: TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_enabled=True,
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.5)),
        ),
    }
    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
