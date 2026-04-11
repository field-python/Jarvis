#!/usr/bin/env python3
"""Semantic search against the Jarvis archive using ChromaDB + nomic-embed-text."""

import sys
import os
import chromadb
import ollama

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_db")
COLLECTION = "jarvis_archive"
TOP_K = 4
MAX_WORDS_PER_CHUNK = 150

def main():
    if len(sys.argv) < 2:
        print("Usage: semantic-search.py <query>", file=sys.stderr)
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    client = chromadb.PersistentClient(path=DB_DIR)
    try:
        collection = client.get_collection(COLLECTION)
    except Exception:
        print("Index not built yet. Run build-index.py first.", file=sys.stderr)
        sys.exit(1)

    resp = ollama.embeddings(model="nomic-embed-text", prompt=query)
    embedding = resp["embedding"]

    results = collection.query(
        query_embeddings=[embedding],
        n_results=TOP_K,
        include=["documents", "metadatas"]
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]

    for doc, meta in zip(docs, metas):
        source = meta.get("source", "unknown")
        words = doc.split()
        snippet = " ".join(words[:MAX_WORDS_PER_CHUNK])
        print(f"[{source}]\n{snippet}\n")

if __name__ == "__main__":
    main()
