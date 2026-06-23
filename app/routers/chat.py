import uuid
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.chat_message import ChatMessage
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatMessageResponse, ChatHistoryResponse, DecomposeRequest, DecomposeResponse, SuggestRoutineRequest, SuggestRoutineResponse
from app.services import ai_service, agenda_service
from app.utils.deps import get_current_user_id, get_current_user_obj

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("")
async def chat(
    data: ChatRequest,
    user: User = Depends(get_current_user_obj),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
    )
    recent_messages = list(reversed(result.scalars().all()))

    pending_tasks = await agenda_service.get_pending_tasks_for_optimization(db, user.id)

    user_msg = ChatMessage(user_id=user.id, role="user", content=data.message)
    db.add(user_msg)
    await db.commit()

    try:
        ai_response = await ai_service.chat_with_ai(user, data.message, recent_messages, pending_tasks)
    except Exception:
        raise HTTPException(status_code=503, detail="Servico de IA temporariamente indisponivel")

    assistant_msg = ChatMessage(user_id=user.id, role="assistant", content=ai_response)
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    return {"role": "assistant", "content": ai_response, "id": str(assistant_msg.id), "created_at": str(assistant_msg.created_at)}


@router.get("/history", response_model=ChatHistoryResponse)
async def chat_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size

    total_result = await db.execute(
        select(func.count()).select_from(ChatMessage).where(ChatMessage.user_id == user_id)
    )
    total = total_result.scalar() or 0

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    messages = list(reversed(result.scalars().all()))

    return ChatHistoryResponse(
        messages=[ChatMessageResponse(id=m.id, role=m.role, content=m.content, created_at=m.created_at) for m in messages],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/decompose", response_model=DecomposeResponse)
async def decompose_project(
    data: DecomposeRequest,
    user: User = Depends(get_current_user_obj),
):
    try:
        result = await ai_service.decompose_project(user, data.project_description)
        parsed = json.loads(result) if isinstance(result, str) else result
        return DecomposeResponse(tasks=parsed.get("tasks", []), message="Projeto decomposto com sucesso")
    except Exception:
        raise HTTPException(status_code=503, detail="Servico de IA temporariamente indisponivel")


@router.post("/suggest-routine", response_model=SuggestRoutineResponse)
async def suggest_routine(
    data: SuggestRoutineRequest,
    user: User = Depends(get_current_user_obj),
    db: AsyncSession = Depends(get_db),
):
    pending = await agenda_service.get_pending_tasks_for_optimization(db, user.id)
    try:
        result = await ai_service.suggest_routine(user, data.preferences, pending)
        parsed = json.loads(result) if isinstance(result, str) else result
        return SuggestRoutineResponse(routine=parsed.get("routine", {}), message="Rotina sugerida com sucesso")
    except Exception:
        raise HTTPException(status_code=503, detail="Servico de IA temporariamente indisponivel")
