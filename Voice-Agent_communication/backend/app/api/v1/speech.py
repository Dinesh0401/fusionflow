from fastapi import APIRouter, Depends, Request, UploadFile

from ...core.config import get_settings
from ...schemas.speech import SpeechProcessResponse
from ...services.audio_pipeline import AudioPipelineService
from ...services.decision_ledger import DecisionLedger

router = APIRouter()


def get_audio_pipeline(request: Request, settings=Depends(get_settings)) -> AudioPipelineService:
    ledger: DecisionLedger | None = getattr(request.app.state, "decision_ledger", None)
    return AudioPipelineService(settings=settings, decision_ledger=ledger)


@router.post("/transcribe", response_model=SpeechProcessResponse)
async def transcribe_audio(
    session_id: str,
    file: UploadFile,
    pipeline: AudioPipelineService = Depends(get_audio_pipeline),
) -> SpeechProcessResponse:
    audio_bytes = await file.read()
    result = await pipeline.process_audio(session_id=session_id, audio_bytes=audio_bytes)
    return result
