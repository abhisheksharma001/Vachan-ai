"""
Provider-specific pause/prosody markup for voice chunks.

Not every TTS provider supports SSML `<break>`; this module maps our neutral
pause metadata into the right textual or SSML cue for each backend.
"""
from __future__ import annotations

from app.voice.burst import VoiceChunk


def apply_prosody(chunks: list[VoiceChunk], provider: str) -> list[dict]:
    """
    Convert VoiceChunks into provider-specific utterances.

    Supported providers:
      - elevenlabs_v2      -> SSML <break>
      - elevenlabs_v3      -> textual ... / — (no <break> support)
      - azure / google     -> SSML <break>
      - retell             -> trailing "-"
      - livekit            -> plain text (player sends chunks separately)
      - default            -> plain text + pause metadata
    """
    provider = provider.lower()

    if provider in ("elevenlabs_v2", "azure", "google"):
        return [
            {
                "text": f"<speak>{c.text}<break time='{c.pause_after_ms}ms'/></speak>",
                "pause_after_ms": c.pause_after_ms,
            }
            for c in chunks
        ]

    if provider == "elevenlabs_v3":
        return [
            {
                "text": c.text + (" ..." if c.pause_after_ms > 300 else ""),
                "pause_after_ms": c.pause_after_ms,
            }
            for c in chunks
        ]

    if provider == "retell":
        return [
            {
                "text": c.text + (" -" if c.pause_after_ms > 250 else ""),
                "pause_after_ms": c.pause_after_ms,
            }
            for c in chunks
        ]

    # livekit and default: the player consumes chunks separately.
    return [{"text": c.text, "pause_after_ms": c.pause_after_ms} for c in chunks]
