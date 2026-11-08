import os
import sys
import time
import types
import hashlib
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

# Windows Application Control / WDAC shim for grpc cython
if "opentelemetry.exporter.otlp.proto.grpc.trace_exporter" not in sys.modules:
    m = types.ModuleType("opentelemetry.exporter.otlp.proto.grpc.trace_exporter")
    m.OTLPSpanExporter = type("OTLPSpanExporter", (), {})
    sys.modules["opentelemetry.exporter.otlp.proto.grpc.trace_exporter"] = m

import chromadb
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from google import genai

from app.core.config import settings

class GeminiCricketEmbeddings(Embeddings):
    """
    LangChain-compatible embedding generator using configured Gemini model
    with deterministic normalized offline fallback.
    """
    def __init__(self, api_key: str = "", model: str = "models/text-embedding-004"):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model
        self._client: Optional[genai.Client] = None

        if self.api_key and self.api_key.strip():
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"Warning: Failed to initialize Gemini embedding client ({e})")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if self._client:
            try:
                res = self._client.models.embed_content(
                    model=self.model,
                    contents=texts
                )
                return [e.values for e in res.embeddings]
            except Exception as e:
                print(f"Gemini batch embedding error ({e}). Using normalized vector fallback.")
        return [self._generate_deterministic_vector(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        if self._client:
            try:
                res = self._client.models.embed_content(
                    model=self.model,
                    contents=text
                )
                return res.embeddings[0].values
            except Exception as e:
                print(f"Gemini query embedding error ({e}). Using normalized vector fallback.")
        return self._generate_deterministic_vector(text)

    def _generate_deterministic_vector(self, text: str, dim: int = 768) -> List[float]:
        """
        Generates a deterministic, normalized 768-dimensional float embedding vector
        from text content for reliable offline operations and testing.
        """
        clean = text.lower().strip()
        h = hashlib.sha256(clean.encode("utf-8")).digest()
        vec = []
        for i in range(dim):
            byte_val = h[i % len(h)]
            # pseudo-float between -1.0 and 1.0
            val = ((byte_val * (i + 1) * 31) % 200 - 100) / 100.0
            vec.append(val)
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

class ChromaDBManager:
    """
    Manages persistent ChromaDB vector storage, LangChain integration,
    automatic collection provisioning, and deduplicated document upserts.
    Preserves all existing collections and records across restarts.
    """
    def __init__(self, persist_dir: Optional[Path] = None):
        self.persist_directory = str(persist_dir or settings.CHROMA_PERSIST_DIR)
        self.embeddings = GeminiCricketEmbeddings()
        self._client: Optional[chromadb.PersistentClient] = None
        self._narratives_store: Optional[Chroma] = None
        self._knowledge_store: Optional[Chroma] = None

    def get_client(self) -> chromadb.PersistentClient:
        if self._client is None:
            Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=self.persist_directory)
        return self._client

    def get_narratives_store(self) -> Chroma:
        """
        Returns LangChain Chroma vectorstore for match narratives.
        """
        if self._narratives_store is None:
            client = self.get_client()
            self._narratives_store = Chroma(
                client=client,
                collection_name="cricket_narratives",
                embedding_function=self.embeddings,
            )
        return self._narratives_store

    def get_knowledge_store(self) -> Chroma:
        """
        Returns LangChain Chroma vectorstore for cricket rules and knowledge.
        """
        if self._knowledge_store is None:
            client = self.get_client()
            self._knowledge_store = Chroma(
                client=client,
                collection_name="cricket_knowledge",
                embedding_function=self.embeddings,
            )
        return self._knowledge_store

    def get_collection(self):
        """
        Backward-compatible native collection accessor.
        """
        client = self.get_client()
        return client.get_or_create_collection(
            name="cricket_narratives",
            metadata={"description": "Historical cricket match narratives, iconic moments, rules, and trivia"}
        )

    def initialize_database(self) -> Dict[str, Any]:
        """
        Automatically provisions required collections in ChromaDB.
        Preserves existing documents across restarts without overwriting.
        """
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        client = self.get_client()

        # 1. Automatically ensure both collections exist
        col_narratives = client.get_or_create_collection(
            name="cricket_narratives",
            metadata={"description": "Historical cricket match narratives and iconic game reports"}
        )
        col_knowledge = client.get_or_create_collection(
            name="cricket_knowledge",
            metadata={"description": "Official cricket laws, DLS method, DRS, and tournament rules"}
        )

        narratives_count = col_narratives.count()
        knowledge_count = col_knowledge.count()

        # 2. Seed starter knowledge if empty, without overwriting existing data
        if narratives_count == 0:
            self._seed_starter_narratives()
            narratives_count = col_narratives.count()

        if knowledge_count == 0:
            self._seed_starter_rules()
            knowledge_count = col_knowledge.count()

        return {
            "status": "ready",
            "persist_directory": self.persist_directory,
            "collections": {
                "cricket_narratives": narratives_count,
                "cricket_knowledge": knowledge_count
            },
            "embedding_model": self.embeddings.model
        }

    def upsert_documents(
        self, 
        collection_type: str, 
        documents: List[Document], 
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Inserts or updates documents with deduplication based on deterministic IDs.
        """
        store = self.get_knowledge_store() if collection_type == "knowledge" else self.get_narratives_store()
        
        # Ensure deterministic IDs if not provided
        doc_ids = []
        for idx, doc in enumerate(documents):
            if ids and idx < len(ids):
                doc_ids.append(ids[idx])
            else:
                # Content hash ID
                h = hashlib.sha256(doc.page_content.encode("utf-8")).hexdigest()[:16]
                prefix = doc.metadata.get("id") or doc.metadata.get("type") or "doc"
                doc_ids.append(f"{prefix}_{h}")

        # Add / update documents in LangChain Chroma store
        store.add_documents(documents=documents, ids=doc_ids)
        return doc_ids

    def search_narratives(
        self, 
        query: str, 
        n_results: int = 3, 
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic similarity search over narratives using LangChain vectorstore.
        """
        store = self.get_narratives_store()
        kwargs: Dict[str, Any] = {"k": n_results}
        if filter_dict:
            kwargs["filter"] = filter_dict

        try:
            docs = store.similarity_search(query, **kwargs)
            return [
                {
                    "id": d.metadata.get("id", "doc"),
                    "text": d.page_content,
                    "metadata": d.metadata
                }
                for d in docs
            ]
        except Exception as e:
            # Fallback to direct client query
            col = self.get_collection()
            if col.count() == 0:
                return []
            res = col.query(query_texts=[query], n_results=min(n_results, col.count()))
            out = []
            if res and res.get("documents"):
                for t, m, i in zip(res["documents"][0], res["metadatas"][0], res["ids"][0]):
                    out.append({"id": i, "text": t, "metadata": m})
            return out

    def search_knowledge(
        self, 
        query: str, 
        n_results: int = 3, 
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic similarity search over cricket rules and knowledge.
        """
        store = self.get_knowledge_store()
        kwargs: Dict[str, Any] = {"k": n_results}
        if filter_dict:
            kwargs["filter"] = filter_dict

        docs = store.similarity_search(query, **kwargs)
        return [
            {
                "id": d.metadata.get("id", "rule"),
                "text": d.page_content,
                "metadata": d.metadata
            }
            for d in docs
        ]

    def health_check(self) -> Dict[str, Any]:
        """
        Health check verifying persistence, collection integrity, and search latency.
        """
        start_time = time.perf_counter()
        try:
            client = self.get_client()
            col_narratives = client.get_or_create_collection("cricket_narratives")
            col_knowledge = client.get_or_create_collection("cricket_knowledge")

            # Perform a test vector query
            test_res = self.search_narratives("cricket", n_results=1)
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            return {
                "status": "healthy",
                "engine": "LangChain + ChromaDB",
                "persist_directory": self.persist_directory,
                "latency_ms": latency_ms,
                "collections": {
                    "cricket_narratives": col_narratives.count(),
                    "cricket_knowledge": col_knowledge.count()
                },
                "embedding_model": self.embeddings.model,
                "test_query_returned": len(test_res) > 0
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "persist_directory": self.persist_directory
            }

    def _seed_starter_narratives(self):
        """
        Seeds iconic historical matches into cricket_narratives using LangChain Documents.
        """
        seed_data = [
            (
                "ind_pak_mcg_2022",
                "India vs Pakistan at Melbourne Cricket Ground (MCG), ICC Men's T20 World Cup 2022 Super 12. "
                "Chasing 160, India were reeling at 31/4 before Virat Kohli and Hardik Pandya staged a 113-run stand. "
                "With 28 required off 8 balls, Virat Kohli struck Haris Rauf for two legendary consecutive sixes: "
                "the first a straight back-foot loft over long-on, and the second flicked over fine leg. "
                "Kohli remained unbeaten on 82 off 53 balls in what is celebrated as his greatest T20I innings.",
                {"id": "ind_pak_mcg_2022", "match": "IND vs PAK 2022", "format": "T20", "year": "2022", "hero": "Virat Kohli", "venue": "MCG"}
            ),
            (
                "ind_sa_t20wc_final_2024",
                "India vs South Africa, ICC Men's T20 World Cup 2024 Final at Kensington Oval, Barbados. "
                "India scored 176/7 propelled by Virat Kohli's anchoring 76 off 59 balls. "
                "South Africa needed 30 runs off 30 balls with Heinrich Klaasen firing. "
                "Jasprit Bumrah bowled a 4-run 16th over and a 2-run 18th over, bowling Marco Jansen. "
                "Hardik Pandya defended 16 off the final over, with Suryakumar Yadav's miraculous boundary catch of David Miller. India won by 7 runs.",
                {"id": "ind_sa_t20wc_final_2024", "match": "IND vs SA 2024 Final", "format": "T20", "year": "2024", "hero": "Jasprit Bumrah", "venue": "Barbados"}
            ),
            (
                "eng_nz_wc_final_2019",
                "England vs New Zealand, ICC Cricket World Cup 2019 Final at Lord's, London. "
                "The match ended in a double tie (241 all out each, followed by 15 runs each in the Super Over). "
                "Ben Stokes scored 84 not out. England were awarded the trophy on the boundary countback rule, "
                "sparking global debates that led the ICC to eliminate boundary countback.",
                {"id": "eng_nz_wc_final_2019", "match": "ENG vs NZ 2019 Final", "format": "ODI", "year": "2019", "hero": "Ben Stokes", "venue": "Lord's"}
            ),
            (
                "headingley_ashes_2019",
                "The 3rd Ashes Test 2019 at Headingley between England and Australia. "
                "England needed 359 to win. At 286/9, 73 runs away, Ben Stokes (135*) and Jack Leach (1*) "
                "staged a legendary 10th-wicket partnership to win by 1 wicket.",
                {"id": "headingley_ashes_2019", "match": "England vs Australia 3rd Test 2019", "format": "Test", "year": "2019", "hero": "Ben Stokes", "venue": "Headingley"}
            )
        ]

        docs = [Document(page_content=item[1], metadata=item[2]) for item in seed_data]
        doc_ids = [item[0] for item in seed_data]
        self.upsert_documents("narratives", docs, doc_ids)

    def _seed_starter_rules(self):
        """
        Seeds official cricket rules into cricket_knowledge using LangChain Documents.
        """
        rules_data = [
            (
                "rule_dls_method",
                "The Duckworth-Lewis-Stern (DLS) method is a mathematical formula used to calculate target scores "
                "in rain-interrupted limited-overs cricket matches. It evaluates the combined resources of overs remaining "
                "and wickets in hand to adjust targets fairly.",
                {"id": "rule_dls_method", "type": "rule", "topic": "DLS Method"}
            ),
            (
                "rule_super_over",
                "A Super Over is a one-over-per-side tiebreaker used in limited-overs matches. "
                "Under revised ICC rules, if a Super Over is tied, subsequent Super Overs are played until a winner emerges.",
                {"id": "rule_super_over", "type": "rule", "topic": "Super Over"}
            ),
            (
                "rule_boundary_countback",
                "The boundary countback rule was used in the 2019 World Cup Final to break a tied Super Over based on total boundaries hit. "
                "It was subsequently abolished by the ICC in favor of repeated Super Overs.",
                {"id": "rule_boundary_countback", "type": "rule", "topic": "Boundary Countback"}
            ),
            (
                "rule_powerplay",
                "In T20 cricket, overs 1 through 6 are the mandatory Powerplay with only 2 fielders allowed outside the 30-yard circle.",
                {"id": "rule_powerplay", "type": "rule", "topic": "Powerplay"}
            )
        ]

        docs = [Document(page_content=item[1], metadata=item[2]) for item in rules_data]
        doc_ids = [item[0] for item in rules_data]
        self.upsert_documents("knowledge", docs, doc_ids)

chroma_manager = ChromaDBManager()
