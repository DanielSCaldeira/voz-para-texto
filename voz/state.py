"""Estado mutável compartilhado entre módulos."""

from dataclasses import dataclass


@dataclass
class DitadorState:
    pausado: bool = False
    ultimo_len: int = 0   # quantos caracteres foram colados por último (para undo)


state = DitadorState()
