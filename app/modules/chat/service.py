from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.chat.models import ChatMessage, ChatSession


def get_owned_session(db: Session, session_id: int, user: User) -> ChatSession:
    session = db.scalar(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user.id,
            ChatSession.deleted_at.is_(None),
        )
    )
    if session is None:
        raise AppError("Chat session not found", status_code=404)
    return session


def create_session(
    db: Session, user: User, title: str | None = None
) -> ChatSession:
    session = ChatSession(user=user, title=title or "New conversation")
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_context_messages(
    db: Session, session_id: int, user: User, max_messages: int = 12
) -> list[ChatMessage]:
    session = get_owned_session(db, session_id, user)
    if session.archived_at is not None:
        raise AppError(
            "Archived conversations cannot receive new messages",
            status_code=409,
        )
    return list(
        db.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
            .limit(max_messages)
        ).all()
    )[::-1]


def save_exchange(
    db: Session,
    user: User,
    query: str,
    answer: str,
    sources: list[dict],
    session_id: int | None = None,
) -> ChatSession:
    session = (
        get_owned_session(db, session_id, user)
        if session_id is not None
        else ChatSession(user=user, title=query[:200])
    )
    if session.archived_at is not None:
        raise AppError(
            "Archived conversations cannot receive new messages",
            status_code=409,
        )
    if session.id is None:
        db.add(session)
        db.flush()

    session.updated_at = datetime.now(timezone.utc)
    session.messages.extend(
        [
            ChatMessage(role="user", content=query),
            ChatMessage(role="assistant", content=answer, sources=sources),
        ]
    )
    db.commit()
    db.refresh(session)
    return session


def list_sessions(
    db: Session,
    user: User,
    search: str | None = None,
    include_archived: bool = False,
) -> list[ChatSession]:
    query = select(ChatSession).where(
        ChatSession.user_id == user.id,
        ChatSession.deleted_at.is_(None),
    )
    if not include_archived:
        query = query.where(ChatSession.archived_at.is_(None))
    if search:
        term = f"%{search.strip()}%"
        query = query.outerjoin(ChatMessage).where(
            or_(
                ChatSession.title.ilike(term),
                ChatMessage.content.ilike(term),
            )
        ).distinct()
    return list(db.scalars(query.order_by(ChatSession.updated_at.desc())).all())


def rename_session(
    db: Session, session_id: int, user: User, title: str
) -> ChatSession:
    session = get_owned_session(db, session_id, user)
    session.title = title.strip()
    db.commit()
    db.refresh(session)
    return session


def set_archived(
    db: Session, session_id: int, user: User, archived: bool
) -> ChatSession:
    session = get_owned_session(db, session_id, user)
    session.archived_at = datetime.now(timezone.utc) if archived else None
    db.commit()
    db.refresh(session)
    return session


def delete_session(db: Session, session_id: int, user: User) -> None:
    session = get_owned_session(db, session_id, user)
    session.deleted_at = datetime.now(timezone.utc)
    db.commit()


def get_session_with_messages(
    db: Session, session_id: int, user: User
) -> ChatSession:
    session = db.scalar(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(
            ChatSession.id == session_id,
            ChatSession.user_id == user.id,
            ChatSession.deleted_at.is_(None),
        )
    )
    if session is None:
        raise AppError("Chat session not found", status_code=404)
    return session