from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class AudioTask:
    user_id: int
    chat_id: int
    message_id: int
    media_url: str
    filename_hint: str
    created_at: float
    in_progress: bool = False


class UserSemaphores:
    def __init__(self, per_user_limit: int) -> None:
        self.per_user_limit = per_user_limit
        self._semaphores: Dict[int, asyncio.Semaphore] = {}

    def for_user(self, user_id: int) -> asyncio.Semaphore:
        if user_id not in self._semaphores:
            self._semaphores[user_id] = asyncio.Semaphore(self.per_user_limit)
        return self._semaphores[user_id]


class CallbackStore:
    def __init__(self) -> None:
        self._store: Dict[str, AudioTask] = {}

    def new_audio_token(self, *, user_id: int, chat_id: int, message_id: int, media_url: str, filename_hint: str) -> str:
        token = uuid.uuid4().hex[:24]
        self._store[token] = AudioTask(
            user_id=user_id,
            chat_id=chat_id,
            message_id=message_id,
            media_url=media_url,
            filename_hint=filename_hint,
            created_at=time.time(),
        )
        return token

    def get_audio_task(self, token: str) -> Optional[AudioTask]:
        task = self._store.get(token)
        # Expire after 30 minutes
        if task and time.time() - task.created_at > 1800:
            self._store.pop(token, None)
            return None
        return task

    def mark_in_progress(self, token: str) -> bool:
        task = self._store.get(token)
        if not task:
            return False
        if task.in_progress:
            return False
        task.in_progress = True
        return True

    def complete(self, token: str) -> None:
        self._store.pop(token, None)

