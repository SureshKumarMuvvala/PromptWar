"""
FAISS index builder — processes knowledge base JSON files into
a FAISS vector index + document metadata file.

Usage:
    python -m app.rag.indexer
"""

import asyncio
import json
import os

import numpy as np

from app.config import get_settings
from app.services.gemini_client import GeminiClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def build_index():
    """
    Read all JSON files from the knowledge base directory,
    embed each document, and save a FAISS index + metadata.
    """
    try:
        import faiss
    except ImportError:
        logger.error("FAISS is required to build the index: pip install faiss-cpu")
        return

    settings = get_settings()
    gemini = GeminiClient()
    kb_path = settings.KNOWLEDGE_BASE_PATH
    index_path = settings.FAISS_INDEX_PATH

    os.makedirs(index_path, exist_ok=True)

    # ── Load all knowledge base documents ────────────────────────
    all_documents = []
    for filename in os.listdir(kb_path):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(kb_path, filename)
        logger.info(f"Loading knowledge base file: {filename}")
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            all_documents.extend(data)
        elif isinstance(data, dict) and "documents" in data:
            all_documents.extend(data["documents"])
        else:
            all_documents.append(data)

    if not all_documents:
        logger.error("No documents found in knowledge base")
        return

    logger.info(f"Found {len(all_documents)} documents to index")

    # ── Generate embeddings ──────────────────────────────────────
    texts = []
    for doc in all_documents:
        # Build embedding text from available fields
        parts = []
        if "title" in doc:
            parts.append(doc["title"])
        if "description" in doc:
            parts.append(doc["description"])
        if "symptoms" in doc:
            if isinstance(doc["symptoms"], list):
                parts.append("Symptoms: " + ", ".join(doc["symptoms"]))
            else:
                parts.append("Symptoms: " + str(doc["symptoms"]))
        if "protocol" in doc:
            parts.append(doc["protocol"])
        if "content" in doc:
            parts.append(doc["content"])
        texts.append(" | ".join(parts) if parts else json.dumps(doc))

    logger.info("Generating embeddings via Gemini...")
    # Process in batches to avoid rate limits
    batch_size = 10
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        embeddings = await gemini.embed_texts(batch)
        all_embeddings.extend(embeddings)
        logger.info(f"Embedded {min(i + batch_size, len(texts))}/{len(texts)} documents")

    # ── Build FAISS index ────────────────────────────────────────
    embedding_matrix = np.array(all_embeddings, dtype=np.float32)
    dimension = embedding_matrix.shape[1]

    index = faiss.IndexFlatL2(dimension)
    index.add(embedding_matrix)

    # Save index
    faiss_file = os.path.join(index_path, "index.faiss")
    faiss.write_index(index, faiss_file)
    logger.info(f"FAISS index saved: {faiss_file} ({index.ntotal} vectors, dim={dimension})")

    # Save document metadata
    docs_file = os.path.join(index_path, "documents.json")
    with open(docs_file, "w", encoding="utf-8") as f:
        json.dump(all_documents, f, indent=2, ensure_ascii=False)
    logger.info(f"Document metadata saved: {docs_file}")

    logger.info("Index build complete!")


if __name__ == "__main__":
    asyncio.run(build_index())
