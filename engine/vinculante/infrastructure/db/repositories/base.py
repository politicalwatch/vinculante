from typing import Generic, TypeVar

from sqlalchemy.orm import Session

from vinculante.domain.base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    model: type[T]

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, id: int) -> T | None:
        return self.db.get(self.model, id)

    def get_all(self) -> list[T]:
        return list(self.db.query(self.model).all())

    def save(self, instance: T) -> T:
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def bulk_save(self, instances: list[T]) -> list[T]:
        self.db.add_all(instances)
        self.db.commit()
        return instances

    def delete(self, id: int) -> None:
        instance = self.get_by_id(id)
        if instance:
            self.db.delete(instance)
            self.db.commit()
