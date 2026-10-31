import logging
import time
from collections import defaultdict, deque
from threading import Lock
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.database.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.chat.schemas import (
    ChatAnswerResponse,
    CreateChatSessionRequest,
    RenameChatSessionRequest,
    ChatSessionResponse,
    ChatSessionSummary,
    QueryRequest,
    SendMessageRequest,
)
from app.modules.chat.service import (
    create_session,
    delete_session,
    get_context_messages,
    get_session_with_messages,
    list_sessions,
    rename_session,
    save_exchange,
    set_archived,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])
rate_limit_cache = defaultdict(deque)
rate_limit_lock = Lock()


def rate_limit_check(client_ip: str, limit: int, period: int) -> bool:
    current_time = time.time()
    key = f"rate_limit:{client_ip}"
    with rate_limit_lock:
        timestamps = rate_limit_cache[key]
        while timestamps and current_time - timestamps[0] >= period:
            timestamps.popleft()
        if len(timestamps) >= limit:
            return False
        timestamps.append(current_time)
        return True


def _conversation_context(
    db: Session, session_id: int | None, user: User
) -> str:
    if session_id is None:
        return ""
    messages = get_context_messages(db, session_id, user)
    parts = []
    total_chars = 0
    for message in messages:
        content = message.content[:2000]
        if total_chars + len(content) > 8000:
            break
        parts.append(f"{message.role}: {content}")
        total_chars += len(content)
    return "\n".join(parts)


def _check_rate_limit(request: Request) -> None:
    config = request.app.state.config
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limit_check(
        client_ip, config.RATE_LIMIT, config.RATE_LIMIT_PERIOD
    ):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")


def _generate_and_save(
    content: str,
    session_id: int | None,
    request: Request,
    db: Session,
    user: User,
) -> ChatAnswerResponse:
    start_time = time.perf_counter()
    query = content.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    conversation = _conversation_context(db, session_id, user)
    result = request.app.state.rag_service.generate_answer(
        query, conversation=conversation
    )
    sources = result.get("sources", [])
    session = save_exchange(
        db, user, query, result["answer"], sources, session_id
    )
    return ChatAnswerResponse(
        session_id=session.id,
        answer=result["answer"],
        sources=sources,
        metadata={
            "response_time_ms": round(
                (time.perf_counter() - start_time) * 1000, 2
            ),
            "sources_count": len(sources),
        },
    )


@router.post(
    "/ask",
    response_model=ChatAnswerResponse,
    status_code=status.HTTP_200_OK,
)
async def ask(
    payload: QueryRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> ChatAnswerResponse:
    _check_rate_limit(request)
    try:
        return _generate_and_save(
            payload.query, payload.session_id, request, db, user
        )
    except AppError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        logger.exception("Chat request failed")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "Please try again later",
            },
        )


@router.post(
    "/sessions",
    response_model=ChatSessionSummary,
    status_code=status.HTTP_201_CREATED,
)
def create_chat_session(
    payload: CreateChatSessionRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> ChatSessionSummary:
    return create_session(db, user, payload.title)


@router.post(
    "/sessions/{session_id}/messages",
    response_model=ChatAnswerResponse,
)
async def send_message(
    session_id: int,
    payload: SendMessageRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> ChatAnswerResponse:
    _check_rate_limit(request)
    try:
        return _generate_and_save(
            payload.content, session_id, request, db, user
        )
    except AppError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        logger.exception("Chat message failed")
        raise HTTPException(status_code=500, detail="Unable to send message")


@router.get("/sessions", response_model=list[ChatSessionSummary])
def get_sessions(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    search: str | None = Query(default=None, max_length=200),
    include_archived: bool = False,
) -> list[ChatSessionSummary]:
    return list_sessions(db, user, search, include_archived)


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
def get_session(
    session_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> ChatSessionResponse:
    return get_session_with_messages(db, session_id, user)


@router.patch(
    "/sessions/{session_id}", response_model=ChatSessionSummary
)
def rename_chat_session(
    session_id: int,
    payload: RenameChatSessionRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> ChatSessionSummary:
    return rename_session(db, session_id, user, payload.title)


@router.post(
    "/sessions/{session_id}/archive", response_model=ChatSessionSummary
)
def archive_chat_session(
    session_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> ChatSessionSummary:
    return set_archived(db, session_id, user, True)


@router.post(
    "/sessions/{session_id}/unarchive", response_model=ChatSessionSummary
)
def unarchive_chat_session(
    session_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> ChatSessionSummary:
    return set_archived(db, session_id, user, False)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_session(
    session_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    delete_session(db, session_id, user)