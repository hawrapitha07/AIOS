from typing import List, Dict, Any

from aios.knowledge.base import BaseKnowledge


class DocumentKnowledge(BaseKnowledge):
    """Simple in-memory document knowledge source."""

    def __init__(self, name: str):
        super().__init__(name)
        self.documents: List[Dict[str, Any]] = []

    def add(
        self,
        content: str,
        metadata: Dict[str, Any] | None = None
    ):
        self.documents.append({
            "content": content,
            "metadata": metadata or {}
        })

    def search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        query_words = query.lower().split()

        results = []

        for document in self.documents:
            content = document["content"].lower()

            score = sum(
                1 for word in query_words
                if word in content
            )

            if score > 0:
                results.append({
                    "content": document["content"],
                    "metadata": document["metadata"],
                    "score": score
                })

        results.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        return results[:top_k]