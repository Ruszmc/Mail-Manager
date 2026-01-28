from fastapi import APIRouter

from ..schemas import AiRequest, AiResponse
from ..services.ai import summarize, extract_actions, draft_reply

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/summarize", response_model=AiResponse)
def summarize_endpoint(payload: AiRequest):
    return AiResponse(result=summarize(payload.subject, payload.snippet, payload.body))


@router.post("/actions", response_model=AiResponse)
def actions_endpoint(payload: AiRequest):
    return AiResponse(result=extract_actions(payload.subject, payload.snippet, payload.body))


@router.post("/draft", response_model=AiResponse)
def draft_endpoint(payload: AiRequest):
    return AiResponse(result=draft_reply(payload.subject, payload.snippet, payload.body, payload.language))
