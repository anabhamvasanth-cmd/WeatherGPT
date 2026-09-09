from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer


class WeatherRAG:
    """Retrieve relevant WeatherGPT knowledge using FAISS."""

    def __init__(
        self,
        knowledge_dir: str = "ai/rag/knowledge",
        model_name: str = "all-MiniLM-L6-v2",
        index_dir: str = "ai/rag/index",
    ):
        self.knowledge_dir = Path(knowledge_dir)
        self.index_dir = Path(index_dir)
        self.model_name = model_name

        self.index_path = self.index_dir / "weather.index"
        self.documents_path = self.index_dir / "documents.txt"
        self.metadata_path = self.index_dir / "metadata.txt"

        self.embedding_model = SentenceTransformer(
            self.model_name
        )

        self.documents = []
        self.index = None

        if self._cached_index_is_valid():
            self._load_cached_index()
        else:
            self._load_knowledge()
            self._build_index()
            self._save_cached_index()

    def _load_knowledge(self) -> None:
        """Load text documents from the knowledge directory."""

        if not self.knowledge_dir.exists():
            raise FileNotFoundError(
                f"Knowledge directory not found: {self.knowledge_dir}"
            )

        text_files = sorted(
            self.knowledge_dir.glob("*.txt")
        )

        if not text_files:
            raise FileNotFoundError(
                "No knowledge documents found."
            )

        self.documents = []

        for file_path in text_files:
            text = file_path.read_text(
                encoding="utf-8"
            ).strip()

            if text:
                self.documents.extend(
                    self._chunk_text(text)
                )

    @staticmethod
    def _chunk_text(
        text: str,
        max_words: int = 120,
    ) -> list[str]:
        """Split a document into manageable text chunks."""

        paragraphs = [
            paragraph.strip()
            for paragraph in text.split("\n\n")
            if paragraph.strip()
        ]

        chunks = []

        for paragraph in paragraphs:
            words = paragraph.split()

            if len(words) <= max_words:
                chunks.append(paragraph)
                continue

            for start in range(
                0,
                len(words),
                max_words,
            ):
                chunk = " ".join(
                    words[start:start + max_words]
                )

                if chunk:
                    chunks.append(chunk)

        return chunks

    def _build_index(self) -> None:
        """Create a FAISS vector index from the knowledge documents."""

        if not self.documents:
            raise ValueError(
                "Cannot build a RAG index without documents."
            )

        embeddings = self.embedding_model.encode(
            self.documents,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        dimension = embeddings.shape[1]

        self.index = faiss.IndexFlatIP(
            dimension
        )

        self.index.add(
            embeddings.astype("float32")
        )

    def _save_cached_index(self) -> None:
        """Save the FAISS index and documents for reuse."""

        self.index_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        faiss.write_index(
            self.index,
            str(self.index_path),
        )

        self.documents_path.write_text(
            "\n\n---DOCUMENT---\n\n".join(self.documents),
            encoding="utf-8",
        )

        knowledge_files = sorted(
            self.knowledge_dir.glob("*.txt")
        )

        metadata_lines = []

        for file_path in knowledge_files:
            metadata_lines.append(
                f"{file_path.name}|{file_path.stat().st_mtime_ns}"
            )

        self.metadata_path.write_text(
            "\n".join(metadata_lines),
            encoding="utf-8",
        )

    def _cached_index_is_valid(self) -> bool:
        """Check whether a cached index matches the knowledge files."""

        if not (
            self.index_path.exists()
            and self.documents_path.exists()
            and self.metadata_path.exists()
        ):
            return False

        knowledge_files = sorted(
            self.knowledge_dir.glob("*.txt")
        )

        if not knowledge_files:
            return False

        expected_metadata = [
            f"{file_path.name}|{file_path.stat().st_mtime_ns}"
            for file_path in knowledge_files
        ]

        cached_metadata = [
            line.strip()
            for line in self.metadata_path.read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
        ]

        return expected_metadata == cached_metadata

    def _load_cached_index(self) -> None:
        """Load a previously saved FAISS index and documents."""

        self.index = faiss.read_index(
            str(self.index_path)
        )

        documents_text = self.documents_path.read_text(
            encoding="utf-8"
        )

        self.documents = [
            document.strip()
            for document in documents_text.split(
                "\n\n---DOCUMENT---\n\n"
            )
            if document.strip()
        ]

        if not self.documents:
            raise ValueError(
                "Cached RAG index contains no documents."
            )

        if self.index.ntotal != len(self.documents):
            raise ValueError(
                "Cached FAISS index and document count do not match."
            )

    def search(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[str]:
        """Retrieve the most relevant knowledge chunks."""

        if not query or not query.strip():
            return []

        if self.index is None:
            return []

        if not self.documents:
            return []

        top_k = max(
            1,
            min(top_k, len(self.documents)),
        )

        query_embedding = self.embedding_model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        scores, indices = self.index.search(
            query_embedding.astype("float32"),
            top_k,
        )

        results = []

        for index in indices[0]:
            if index < 0:
                continue

            results.append(
                self.documents[index]
            )

        return results
