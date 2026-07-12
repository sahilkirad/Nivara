from sqlalchemy.orm import Session

from app.db.models import SemanticMemory
from app.memory.semantic.product_knowledge import DEFAULT_SEMANTIC_PRODUCT_KNOWLEDGE


class SemanticMemoryService:
    def __init__(self, db: Session):
        self.db = db

    def load_product_knowledge(self) -> list[dict]:
        rows = (
            self.db.query(SemanticMemory)
            .filter(SemanticMemory.active.is_(True))
            .order_by(SemanticMemory.created_at.desc())
            .limit(100)
            .all()
        )

        if rows:
            return [row.content for row in rows]

        return DEFAULT_SEMANTIC_PRODUCT_KNOWLEDGE