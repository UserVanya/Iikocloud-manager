"""Меню V3 вместе с ответом iiko как он есть (выпуск 0.4.0)."""

from dataclasses import dataclass, field

from iikocloud_client import MenuV3


@dataclass(frozen=True)
class MenuV3Answer:
    """Меню V3 и тело ответа iiko, из которого оно разобрано (выпуск 0.4.0).

    ``raw`` — тело ответа байт в байт, как его прислал iiko: те же пробелы, порядок полей
    и буквы, что пришли по сети (сжатие передачи — gzip и подобное — снимает HTTP-клиент,
    само тело не трогается). ``content_type`` — заголовок Content-Type ответа или ``None``,
    если iiko его не прислал. В ``repr`` тело не попадает: меню весит мегабайты.
    """

    menu: MenuV3
    raw: bytes = field(repr=False)
    content_type: str | None
