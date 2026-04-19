#!/usr/bin/env python3
"""Build semantic search index from Jarvis archive — incremental by default."""

import hashlib
import json
import os
import sys
import chromadb
import ollama

ARCHIVE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR      = os.path.join(ARCHIVE_DIR, "chroma_db")
MANIFEST    = os.path.join(DB_DIR, "indexed_files.json")
COLLECTION  = "jarvis_archive"
CHUNK_SIZE  = 500  # words per chunk

FORCE = "--force" in sys.argv   # Jarvis rebuild-index --force → full re-index


def chunk_text(text, size=CHUNK_SIZE):
    words = text.split()
    for i in range(0, len(words), size):
        yield " ".join(words[i:i+size])


def file_hash(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


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
            doc_id    = f"{rel_path}::{i}"
            embedding = get_embedding(chunk)
            collection.upsert(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[{"source": rel_path, "chunk": i}],
            )
            count += 1
        return count
    except Exception as e:
        print(f"  SKIP {rel_path}: {e}")
        return 0


def delete_file_chunks(collection, rel_path, n_chunks):
    """Remove all indexed chunks for a file (used when file is deleted or re-indexed)."""
    ids = [f"{rel_path}::{i}" for i in range(n_chunks)]
    try:
        collection.delete(ids=ids)
    except Exception:
        pass


def load_manifest():
    if os.path.exists(MANIFEST):
        try:
            with open(MANIFEST) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_manifest(manifest):
    os.makedirs(DB_DIR, exist_ok=True)
    with open(MANIFEST, "w") as f:
        json.dump(manifest, f, indent=2)


def main():
    client     = chromadb.PersistentClient(path=DB_DIR)
    collection = client.get_or_create_collection(COLLECTION)
    manifest   = {} if FORCE else load_manifest()

    extensions = {".txt", ".md", ".html", ".rst"}

    indexed_files  = 0
    skipped_files  = 0
    total_chunks   = 0
    current_paths  = set()

    for root, dirs, files in os.walk(ARCHIVE_DIR):
        dirs[:] = [d for d in dirs if d not in ("chroma_db", "venv", "wikipedia", ".git")]
        for fname in files:
            if not any(fname.endswith(ext) for ext in extensions):
                continue
            fpath = os.path.join(root, fname)
            rel   = os.path.relpath(fpath, ARCHIVE_DIR)
            current_paths.add(rel)

            mtime = os.path.getmtime(fpath)
            fhash = file_hash(fpath)

            prev = manifest.get(rel)
            if prev and prev.get("hash") == fhash and not FORCE:
                skipped_files += 1
                total_chunks  += prev.get("chunks", 0)
                continue

            # File is new or changed — delete old chunks first, then re-index
            if prev and prev.get("chunks", 0) > 0:
                delete_file_chunks(collection, rel, prev["chunks"])

            print(f"  index  {rel}")
            chunks = index_file(collection, fpath, rel)
            manifest[rel] = {"hash": fhash, "mtime": mtime, "chunks": chunks}
            if chunks > 0:
                indexed_files += 1
                total_chunks  += chunks

    # Remove manifest entries for files that no longer exist
    deleted = [r for r in list(manifest.keys()) if r not in current_paths]
    for rel in deleted:
        print(f"  remove {rel} (deleted)")
        old_chunks = manifest[rel].get("chunks", 0)
        if old_chunks > 0:
            delete_file_chunks(collection, rel, old_chunks)
        del manifest[rel]

    save_manifest(manifest)

    label = "FULL" if FORCE else "incremental"
    print(f"\nDone ({label}). Indexed {indexed_files} new/changed files, "
          f"skipped {skipped_files} unchanged. "
          f"{total_chunks} total chunks in index.")
    if FORCE:
        print("(Use 'Jarvis rebuild-index' without --force for fast incremental updates)")
    else:
        print("(Use 'Jarvis rebuild-index --force' to re-index everything)")


if __name__ == "__main__":
    main()
