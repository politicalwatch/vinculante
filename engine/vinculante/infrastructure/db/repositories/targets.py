from vinculante.domain.entities import TargetDocument
from .base import BaseRepository


class TargetRepository(BaseRepository[TargetDocument]):
    model = TargetDocument
