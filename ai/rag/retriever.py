from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer


class WeatherRAG:
    """
    Retrieval-Augmented Generation knowledge retriever for WeatherGPT.

    Retrieval pipeline:

        Query
          ↓
        FAISS semantic search
          ↓
        Activity/topic relevance
          ↓
        Diversity filtering
          ↓
        Final supporting knowledge

    RAG is supporting knowledge only.

    It must never override:
        - weather data
        - Risk Engine
        - Decision Engine
        - What-If Engine
        - Forecast Confidence
    """

    ACTIVITY_KEYWORDS = {
        "running": {
            "running",
            "run",
            "jogging",
            "jog",
        },
        "walking": {
            "walking",
            "walk",
            "hiking",
        },
        "cycling": {
            "cycling",
            "cycle",
            "bicycle",
            "bike",
        },
        "sports": {
            "sports",
            "sport",
            "football",
            "cricket",
            "tennis",
            "athletics",
        },
        "travel": {
            "travel",
            "travelling",
            "traveling",
            "journey",
            "trip",
        },
        "farming": {
            "farming",
            "farmer",
            "agriculture",
            "crop",
            "crops",
        },
        "outdoor_work": {
            "outdoor work",
            "construction",
            "labour",
            "labor",
            "worker",
            "work outside",
        },
        "outdoor": {
            "outdoor",
            "outside",
        },
    }

    TOPIC_KEYWORDS = {
        "heat": {
            "heat",
            "hot",
            "temperature",
            "celsius",
            "°c",
        },
        "rain": {
            "rain",
            "rainfall",
            "precipitation",
            "shower",
            "storm",
        },
        "wind": {
            "wind",
            "windy",
            "gust",
        },
        "humidity": {
            "humidity",
            "humid",
            "moisture",
        },
        "risk": {
            "risk",
            "danger",
            "unsafe",
            "safety",
            "hazard",
        },
        "decision": {
            "decision",
            "proceed",
            "caution",
            "postpone",
            "avoid",
            "recommendation",
        },
        "forecast": {
            "forecast",
            "prediction",
            "tomorrow",
            "future",
            "later",
        },
        "what_if": {
            "what if",
            "suppose",
            "assuming",
            "hypothetical",
            "scenario",
        },
        "confidence": {
            "confidence",
            "certainty",
            "reliable",
            "reliability",
        },
    }

    def __init__(
        self,
        knowledge_dir: str = "ai/rag/knowledge",
        model_name: str = "all-MiniLM-L6-v2",
        index_dir: str = "ai/rag/index",
        similarity_threshold: float = 0.30,
        diversity_threshold: float = 0.92,
    ):
        self.knowledge_dir = Path(
            knowledge_dir
        )

        self.index_dir = Path(
            index_dir
        )

        self.model_name = model_name

        self.similarity_threshold = (
            similarity_threshold
        )

        self.diversity_threshold = (
            diversity_threshold
        )

        self.index_path = (
            self.index_dir / "weather.index"
        )

        self.documents_path = (
            self.index_dir / "documents.txt"
        )

        self.metadata_path = (
            self.index_dir / "metadata.txt"
        )

        self.embedding_model = (
            SentenceTransformer(
                self.model_name
            )
        )

        self.documents: list[str] = []

        self.document_embeddings = None

        self.index = None

        if self._cached_index_is_valid():
            self._load_cached_index()
        else:
            self._load_knowledge()
            self._build_index()
            self._save_cached_index()

    # ==========================================================
    # KNOWLEDGE LOADING
    # ==========================================================

    def _load_knowledge(self) -> None:
        """Load all knowledge-base text files."""

        if not self.knowledge_dir.exists():
            raise FileNotFoundError(
                f"Knowledge directory not found: "
                f"{self.knowledge_dir}"
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

            if not text:
                continue

            self.documents.extend(
                self._chunk_text(text)
            )

    @staticmethod
    def _chunk_text(
        text: str,
        max_words: int = 120,
    ) -> list[str]:
        """
        Split knowledge into semantic chunks.

        Paragraphs are kept intact where possible.
        """

        paragraphs = [
            paragraph.strip()
            for paragraph in text.split("\n\n")
            if paragraph.strip()
        ]

        chunks: list[str] = []

        for paragraph in paragraphs:

            words = paragraph.split()

            if len(words) <= max_words:

                chunks.append(
                    paragraph
                )

                continue

            for start in range(
                0,
                len(words),
                max_words,
            ):

                chunk = " ".join(
                    words[
                        start:start + max_words
                    ]
                )

                if chunk:
                    chunks.append(
                        chunk
                    )

        return chunks

    # ==========================================================
    # FAISS
    # ==========================================================

    def _build_index(self) -> None:
        """Build the FAISS semantic index."""

        if not self.documents:
            raise ValueError(
                "Cannot build a RAG index without documents."
            )

        embeddings = (
            self.embedding_model.encode(
                self.documents,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
        )

        self.document_embeddings = (
            embeddings.astype("float32")
        )

        dimension = (
            self.document_embeddings.shape[1]
        )

        self.index = faiss.IndexFlatIP(
            dimension
        )

        self.index.add(
            self.document_embeddings
        )

    def _save_cached_index(self) -> None:
        """Save the FAISS index and documents."""

        self.index_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        faiss.write_index(
            self.index,
            str(self.index_path),
        )

        self.documents_path.write_text(
            "\n\n---DOCUMENT---\n\n".join(
                self.documents
            ),
            encoding="utf-8",
        )

        knowledge_files = sorted(
            self.knowledge_dir.glob("*.txt")
        )

        metadata_lines = [
            (
                f"{file_path.name}|"
                f"{file_path.stat().st_mtime_ns}"
            )
            for file_path in knowledge_files
        ]

        self.metadata_path.write_text(
            "\n".join(metadata_lines),
            encoding="utf-8",
        )

    def _cached_index_is_valid(self) -> bool:
        """Check whether cached RAG data is current."""

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
            (
                f"{file_path.name}|"
                f"{file_path.stat().st_mtime_ns}"
            )
            for file_path in knowledge_files
        ]

        cached_metadata = [
            line.strip()
            for line in self.metadata_path.read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
        ]

        return (
            expected_metadata
            == cached_metadata
        )

    def _load_cached_index(self) -> None:
        """Load the persisted FAISS index."""

        self.index = faiss.read_index(
            str(self.index_path)
        )

        documents_text = (
            self.documents_path.read_text(
                encoding="utf-8"
            )
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

        if (
            self.index.ntotal
            != len(self.documents)
        ):
            raise ValueError(
                "Cached FAISS index and document "
                "count do not match."
            )

        # Recreate embeddings for diversity checking.
        self.document_embeddings = (
            self.embedding_model.encode(
                self.documents,
                convert_to_numpy=True,
                normalize_embeddings=True,
            ).astype("float32")
        )

    # ==========================================================
    # TEXT ANALYSIS
    # ==========================================================

    @staticmethod
    def _normalise_text(
        text: str,
    ) -> str:
        """Normalize text for keyword matching."""

        return " ".join(
            text.lower().split()
        )

    def _find_categories(
        self,
        query: str,
        categories: dict[str, set[str]],
    ) -> set[str]:
        """Detect categories present in a query."""

        normalized_query = (
            self._normalise_text(query)
        )

        detected: set[str] = set()

        for category, keywords in categories.items():

            for keyword in keywords:

                if keyword in normalized_query:

                    detected.add(
                        category
                    )

                    break

        return detected

    def _document_category_score(
        self,
        document: str,
        activity_categories: set[str],
        topic_categories: set[str],
    ) -> float:
        """
        Calculate domain-specific relevance.

        Semantic similarity remains dominant.
        """

        normalized_document = (
            self._normalise_text(
                document
            )
        )

        bonus = 0.0

        # Activity bonus.
        for activity in activity_categories:

            keywords = (
                self.ACTIVITY_KEYWORDS.get(
                    activity,
                    set(),
                )
            )

            if any(
                keyword in normalized_document
                for keyword in keywords
            ):

                bonus += 0.10

        # Topic bonus.
        for topic in topic_categories:

            keywords = (
                self.TOPIC_KEYWORDS.get(
                    topic,
                    set(),
                )
            )

            if any(
                keyword in normalized_document
                for keyword in keywords
            ):

                bonus += 0.06

        return min(
            bonus,
            0.24,
        )

    # ==========================================================
    # DIVERSITY
    # ==========================================================

    def _is_too_similar(
        self,
        candidate_index: int,
        selected_indices: list[int],
    ) -> bool:
        """
        Prevent multiple near-duplicate documents from
        occupying the final result set.
        """

        if not selected_indices:
            return False

        candidate_vector = (
            self.document_embeddings[
                candidate_index
            ]
        )

        for selected_index in selected_indices:

            selected_vector = (
                self.document_embeddings[
                    selected_index
                ]
            )

            similarity = float(
                candidate_vector
                @ selected_vector
            )

            if (
                similarity
                >= self.diversity_threshold
            ):
                return True

        return False

    # ==========================================================
    # SEARCH
    # ==========================================================

    def search(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[str]:
        """Retrieve relevant documents."""

        results = (
            self.search_with_scores(
                query=query,
                top_k=top_k,
            )
        )

        return [
            document
            for document, _score in results
        ]

    def search_with_scores(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[tuple[str, float]]:
        """
        Perform semantic retrieval with:

        1. FAISS similarity
        2. Activity relevance
        3. Topic relevance
        4. Diversity filtering
        """

        if not query or not query.strip():
            return []

        if self.index is None:
            return []

        if not self.documents:
            return []

        top_k = max(
            1,
            min(
                top_k,
                len(self.documents),
            ),
        )

        # Retrieve a broad candidate pool.
        candidate_k = min(
            max(
                top_k * 8,
                20,
            ),
            len(self.documents),
        )

        query_embedding = (
            self.embedding_model.encode(
                [query],
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
        ).astype("float32")

        scores, indices = (
            self.index.search(
                query_embedding,
                candidate_k,
            )
        )

        activity_categories = (
            self._find_categories(
                query,
                self.ACTIVITY_KEYWORDS,
            )
        )

        topic_categories = (
            self._find_categories(
                query,
                self.TOPIC_KEYWORDS,
            )
        )

        candidates = []

        for score, index in zip(
            scores[0],
            indices[0],
        ):

            if index < 0:
                continue

            base_score = float(
                score
            )

            if (
                base_score
                < self.similarity_threshold
            ):
                continue

            document = (
                self.documents[index]
            )

            domain_bonus = (
                self._document_category_score(
                    document=document,
                    activity_categories=(
                        activity_categories
                    ),
                    topic_categories=(
                        topic_categories
                    ),
                )
            )

            final_score = min(
                1.0,
                base_score
                + domain_bonus,
            )

            candidates.append(
                {
                    "index": index,
                    "document": document,
                    "base_score": base_score,
                    "final_score": final_score,
                }
            )

        candidates.sort(
            key=lambda item: item[
                "final_score"
            ],
            reverse=True,
        )

        # ------------------------------------------------------
        # Diversity-aware selection
        # ------------------------------------------------------

        selected = []

        selected_indices = []

        for candidate in candidates:

            candidate_index = (
                candidate["index"]
            )

            if self._is_too_similar(
                candidate_index,
                selected_indices,
            ):
                continue

            selected.append(
                (
                    candidate["document"],
                    round(
                        candidate[
                            "final_score"
                        ],
                        3,
                    ),
                )
            )

            selected_indices.append(
                candidate_index
            )

            if len(selected) >= top_k:
                break

        return selected
