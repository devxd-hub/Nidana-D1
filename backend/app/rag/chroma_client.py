"""ChromaDB persistent vector index client with provenance validation and SQLite reconciliation."""

import logging
import os
from typing import Any, Dict, List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import ApprovalState
from app.models import ContentChunk
from app.rag.embedding import EmbeddingAdapter

logger = logging.getLogger(__name__)


class ChromaVectorIndex:
    """Manages the derived, rebuildable ChromaDB index for approved educational content chunks."""

    def __init__(self, persist_dir: Optional[str] = None, collection_name: Optional[str] = None):
        settings = get_settings()
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIRECTORY
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        self.embedding_adapter = EmbeddingAdapter()

        os.makedirs(self.persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False, is_persistent=True),
        )
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Approved NIDANA curriculum learning content chunks"},
        )

    def count(self) -> int:
        """Returns total chunk count in the collection."""
        return self.collection.count()

    def index_chunk(self, chunk: ContentChunk) -> None:
        """Indexes a single approved SQLite chunk into ChromaDB."""
        if chunk.approval_state != ApprovalState.APPROVED.value:
            logger.info("Skipping unapproved chunk %s", chunk.id)
            return

        vector = self.embedding_adapter.embed_text(chunk.text_content)
        metadata = {
            "chunk_id": chunk.id,
            "chapter_id": chunk.chapter_id,
            "concept_id": chunk.concept_id or "",
            "subject_id": chunk.subject_id or "",
            "class_level": int(chunk.class_level),
            "language": chunk.language,
            "source_title": chunk.source_title,
            "source_locator": chunk.source_locator or "",
            "section_title": chunk.section_title or "",
            "page_number": int(chunk.page_number or 0),
            "approval_state": chunk.approval_state,
            "content_version": chunk.content_version,
            "checksum": chunk.checksum or "",
        }

        self.collection.upsert(
            ids=[chunk.id],
            embeddings=[vector],
            documents=[chunk.text_content],
            metadatas=[metadata],
        )

    def rebuild_from_sqlite(self, db: Session) -> Dict[str, Any]:
        """Rebuilds the ChromaDB collection entirely from authoritative SQLite ContentChunks."""
        try:
            # Drop and recreate collection
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Approved NIDANA curriculum learning content chunks"},
        )

        approved_chunks = (
            db.query(ContentChunk)
            .filter(ContentChunk.approval_state == ApprovalState.APPROVED.value)
            .all()
        )

        indexed_count = 0
        for chunk in approved_chunks:
            self.index_chunk(chunk)
            indexed_count += 1

        logger.info("Successfully rebuilt ChromaDB index with %d chunks.", indexed_count)
        return {
            "status": "rebuilt",
            "indexed_chunks": indexed_count,
            "collection_name": self.collection_name,
        }

    def query(
        self,
        query_text: str,
        class_level: int,
        subject_id: Optional[str] = None,
        chapter_id: Optional[str] = None,
        language: Optional[str] = None,
        top_k: int = 4,
    ) -> List[Dict[str, Any]]:
        """Queries ChromaDB using exact metadata filters before semantic retrieval."""
        # Build exact where clause
        where_conditions: List[Dict[str, Any]] = [
            {"class_level": {"$eq": int(class_level)}},
            {"approval_state": {"$eq": ApprovalState.APPROVED.value}},
        ]
        if subject_id:
            where_conditions.append({"subject_id": {"$eq": subject_id}})
        if chapter_id:
            where_conditions.append({"chapter_id": {"$eq": chapter_id}})
        if language and language != "bilingual":
            # Match specific language or bilingual chunks
            where_conditions.append({"language": {"$in": [language, "bilingual"]}})

        where_filter: Dict[str, Any]
        if len(where_conditions) == 1:
            where_filter = where_conditions[0]
        else:
            where_filter = {"$and": where_conditions}

        query_vector = self.embedding_adapter.embed_text(query_text)

        try:
            results = self.collection.query(
                query_embeddings=[query_vector],
                where=where_filter,
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )

            matched_chunks: List[Dict[str, Any]] = []
            if results and results.get("ids") and results["ids"][0]:
                for i, chunk_id in enumerate(results["ids"][0]):
                    matched_chunks.append({
                        "id": chunk_id,
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "score": 1.0 - (results["distances"][0][i] if "distances" in results else 0.0),
                        "retrieval_mode": "vector",
                    })
            if matched_chunks:
                return matched_chunks

        except Exception as exc:
            logger.warning("ChromaDB vector query failed: %s. Falling back to keyword filter.", exc)

        # Keyword / metadata fallback
        return self._keyword_fallback(
            query_text=query_text,
            class_level=class_level,
            subject_id=subject_id,
            chapter_id=chapter_id,
            top_k=top_k,
        )

    def _keyword_fallback(
        self,
        query_text: str,
        class_level: int,
        subject_id: Optional[str] = None,
        chapter_id: Optional[str] = None,
        top_k: int = 4,
    ) -> List[Dict[str, Any]]:
        """Honest fallback when vector search produces zero results or encounters an exception."""
        all_records = self.collection.get(include=["documents", "metadatas"])
        if not all_records or not all_records.get("ids"):
            return []

        tokens = set(query_text.lower().split())
        scored_chunks = []

        for i, chunk_id in enumerate(all_records["ids"]):
            meta = all_records["metadatas"][i]
            if meta.get("class_level") != class_level:
                continue
            if subject_id and meta.get("subject_id") != subject_id:
                continue
            if chapter_id and meta.get("chapter_id") != chapter_id:
                continue

            doc_text = all_records["documents"][i]
            match_count = sum(1 for tok in tokens if tok in doc_text.lower())
            score = match_count / max(len(tokens), 1)

            scored_chunks.append({
                "id": chunk_id,
                "text": doc_text,
                "metadata": meta,
                "score": score,
                "retrieval_mode": "keyword_fallback",
            })

        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]

    def get_health(self) -> Dict[str, Any]:
        """Readiness inspection distinguishing ChromaDB from SQLite without leaking paths."""
        try:
            count = self.collection.count()
            return {
                "status": "healthy",
                "collection": self.collection_name,
                "indexed_records": count,
                "embedding_model": self.embedding_adapter.model_name,
                "dimensions": self.embedding_adapter.dimension,
            }
        except Exception as exc:
            return {
                "status": "unhealthy",
                "error": str(exc),
            }
