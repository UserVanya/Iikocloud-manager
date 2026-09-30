"""Окна чтения меню одного ключа (выпуск 0.3.0).

iiko отдаёт меню организации не чаще раза в 120 с, а ключ читает меню не чаще раза в 30 с —
это общий запас на все организации ключа. Прежде предел меню был блокирующим лимитером
метода «одно меню в 120 с на ключ»: второй вопрос ЖДАЛ до двух минут, и вызывающий бросал
ждать раньше. Теперь окна не ждут: не пора — сразу ``MenuTooEarly`` с числом секунд. После
«слишком часто» (429) от iiko чтение меню всего ключа встаёт на паузу.
"""

import math
from collections.abc import Callable
from time import monotonic
from typing import Any

from iikocloud.exceptions import MenuTooEarly


class MenuWindows:
    """Окно ключа, окна организаций и пауза — у одного менеджера (один ключ)."""

    def __init__(
        self,
        per_key_sec: float = 30.0,
        per_organization_sec: float = 120.0,
        pause_sec: float = 300.0,
        *,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self.per_key_sec = per_key_sec
        self.per_organization_sec = per_organization_sec
        self.pause_sec = pause_sec
        self._clock = clock
        self._key_last: float | None = None
        self._organization_last: dict[str, float] = {}
        self._paused_until: float | None = None

    def wait(self, organization_id: Any) -> tuple[int, str | None]:
        """Через сколько секунд можно читать меню организации и почему нельзя сейчас."""
        now = self._clock()
        if self._paused_until is not None and now < self._paused_until:
            return math.ceil(self._paused_until - now), "paused"
        last = self._organization_last.get(str(organization_id))
        organization_wait = 0.0 if last is None else last + self.per_organization_sec - now
        key_wait = (
            0.0 if self._key_last is None else self._key_last + self.per_key_sec - now
        )
        if organization_wait > 0 and organization_wait >= key_wait:
            return math.ceil(organization_wait), "organization"
        if key_wait > 0:
            return math.ceil(key_wait), "key"
        return 0, None

    def take(self, organization_id: Any) -> None:
        """Занять окна ключа и организации; не пора — ``MenuTooEarly``, окна не тронуты."""
        seconds, reason = self.wait(organization_id)
        if reason is not None:
            raise MenuTooEarly(seconds, reason)
        now = self._clock()
        self._key_last = now
        self._organization_last[str(organization_id)] = now

    def pause(self) -> None:
        """«Слишком часто» от iiko — меню всего ключа ждут ``pause_sec``."""
        self._paused_until = self._clock() + self.pause_sec

    def resize(
        self,
        *,
        per_key_sec: float | None = None,
        per_organization_sec: float | None = None,
        pause_sec: float | None = None,
    ) -> None:
        """Новые окна — сразу; когда меню читали в последний раз, помнится."""
        if per_key_sec is not None:
            self.per_key_sec = per_key_sec
        if per_organization_sec is not None:
            self.per_organization_sec = per_organization_sec
        if pause_sec is not None:
            self.pause_sec = pause_sec

    def state(self) -> dict[str, Any]:
        """Окна и пауза словарём — для экрана состояния вызывающего."""
        now = self._clock()
        paused = (
            0 if self._paused_until is None else max(0, math.ceil(self._paused_until - now))
        )
        return {
            "paused_for_sec": paused,
            "per_key_sec": self.per_key_sec,
            "per_organization_sec": self.per_organization_sec,
            "pause_sec": self.pause_sec,
        }
