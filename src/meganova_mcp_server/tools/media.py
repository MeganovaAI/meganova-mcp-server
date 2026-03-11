"""Media tools — image generation, video generation, audio transcription."""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

    from meganova_mcp_server.config import Config


def register(mcp: FastMCP, config: Config) -> None:
    """Register media generation tools on the MCP server."""

    def _headers() -> dict:
        return {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }

    @mcp.tool()
    async def generate_image(
        prompt: str,
        model: str = "black-forest-labs/FLUX.1-dev",
        width: int = 1280,
        height: int = 720,
        negative_prompt: str = "",
        num_steps: int | None = None,
        guidance_scale: float = 30,
        seed: int | None = None,
    ) -> str:
        """Generate an image from a text prompt using MegaNova image models.

        Args:
            prompt: Text description of the desired image
            model: Image model name (e.g. "black-forest-labs/FLUX.1-dev", "ByteDance/SeedDream-4-5")
            width: Image width in pixels
            height: Image height in pixels
            negative_prompt: What to avoid in the image
            num_steps: Diffusion steps (None for model default)
            guidance_scale: Classifier-free guidance scale
            seed: Random seed (None for random)
        """
        payload: dict = {
            "model": model,
            "prompt": prompt,
            "width": width,
            "height": height,
            "guidance_scale": guidance_scale,
            "max_sequence_length": 256,
        }
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if num_steps is not None:
            payload["num_steps"] = num_steps
        if seed is not None:
            payload["seed"] = seed

        async with httpx.AsyncClient(base_url=config.api_url) as client:
            resp = await client.post(
                "/images/generation",
                json=payload,
                headers=_headers(),
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()

        images = data.get("data", [])
        if not images:
            return f"Image generation failed: {data.get('message', 'unknown error')}"

        # Return metadata — the actual b64 image data is too large for MCP text
        img = images[0]
        b64_len = len(img.get("b64_json", ""))
        approx_size_kb = (b64_len * 3 // 4) // 1024
        inference_time = img.get("timings", {}).get("inference", "?")
        return (
            f"Image generated successfully!\n"
            f"Model: {data.get('model', model)}\n"
            f"Size: {width}x{height} (~{approx_size_kb} KB)\n"
            f"Inference time: {inference_time}s\n"
            f"Base64 length: {b64_len} chars"
        )

    @mcp.tool()
    async def generate_video(
        model_name: str,
        prompt: str = "",
        **kwargs: str,
    ) -> str:
        """Generate a video using a MegaNova video generation model.

        Args:
            model_name: Video model name (e.g. "Byteplus/seedance-1-0-pro-250528")
            prompt: Text description of the desired video
        """
        payload: dict = {"model_name": model_name}
        if prompt:
            payload["prompt"] = prompt
        payload.update(kwargs)

        async with httpx.AsyncClient(base_url=config.api_url) as client:
            resp = await client.post(
                "/videos/generation",
                json=payload,
                headers=_headers(),
                timeout=300,
            )
            resp.raise_for_status()
            data = resp.json()

        status = data.get("status", "unknown")
        message = data.get("message", "")
        return f"Video generation status: {status}\n{message}"

    @mcp.tool()
    async def transcribe_audio(file_url: str, model: str = "Systran/faster-whisper-large-v3") -> str:
        """Transcribe audio from a URL using MegaNova's audio transcription.

        Args:
            file_url: URL of the audio file to transcribe
            model: Transcription model name
        """
        # Download the audio file first
        async with httpx.AsyncClient() as dl_client:
            dl_resp = await dl_client.get(file_url, timeout=60)
            dl_resp.raise_for_status()
            audio_bytes = dl_resp.content

        # Determine filename from URL
        filename = file_url.split("/")[-1].split("?")[0] or "audio.mp3"

        async with httpx.AsyncClient(base_url=config.api_url) as client:
            resp = await client.post(
                "/audio/transcriptions",
                files={"file": (filename, audio_bytes, "audio/mpeg")},
                data={"model": model},
                headers={"Authorization": f"Bearer {config.api_key}"},
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()

        text = data.get("text", str(data))
        return f"Transcription:\n{text}"
