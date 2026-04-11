#!/usr/bin/env python3
"""Build semantic search index from Jarvis archive."""

import os
import sys
import chromadb
import ollama

ARCHIVE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(ARCHIVE_DIR, "chroma_db")
COLLECTION = "jarvis_archive"
CHUNK_SIZE = 500  # words per chunk

def chunk_text(text, size=CHUNK_SIZE):
    words = text.split()
    for i in range(0, len(words), size):
        yield " ".join(words[i:i+size])

def get_embedding(text):
    resp = ollama.embeddings(model="nomic-embed-text", prompt=text)
    return resp["embedding"]

def index_file(collection, filepath, rel_path):
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read().strip()
        if len(text) < 50:
            return 0
        count = 0
        for i, chunk in enumerate(chunk_text(text)):
            doc_id = f"{rel_path}::{i}"
            embedding = get_embedding(chunk)
            collection.upsert(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[{"source": rel_path, "chunk": i}]
            )
            count += 1
        return count
    except Exception as e:
        print(f"  SKIP {rel_path}: {e}")
        return 0

def main():
    client = chromadb.PersistentClient(path=DB_DIR)
    collection = client.get_or_create_collection(COLLECTION)

    extensions = {".txt", ".md", ".html", ".rst"}
    total_chunks = 0
    total_files = 0

    for root, dirs, files in os.walk(ARCHIVE_DIR):
        # Skip the vector DB and venv directories
        dirs[:] = [d for d in dirs if d not in ("chroma_db", "venv", "wikipedia")]
        for fname in files:
            if any(fname.endswith(ext) for ext in extensions):
                fpath = os.path.join(root, fname)
                rel = os.path.relpath(fpath, ARCHIVE_DIR)
                print(f"Indexing: {rel}")
                chunks = index_file(collection, fpath, rel)
                total_chunks += chunks
                if chunks > 0:
                    total_files += 1

    print(f"\nDone. Indexed {total_files} files, {total_chunks} chunks.")
    print(f"Database saved to: {DB_DIR}")

if __name__ == "__main__":
    main()
