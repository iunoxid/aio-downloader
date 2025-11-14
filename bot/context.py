from __future__ import annotations

from dataclasses import dataclass

from .config import Settings
from .state import CallbackStore, UserSemaphores


@dataclass
class BotContext:
    settings: Settings
    callbacks: CallbackStore
    semaphores: UserSemaphores
    started_at: float
