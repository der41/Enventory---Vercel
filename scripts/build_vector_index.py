"""Build the chatbot's FAISS vector index against a live Neon DB and save it
to ../vector_index/ so it can be committed and shipped with the deploy.

Usage:
    export DATABASE_URL=postgresql://...  # Neon connection string
    export GOOGLE_API_KEY=...             # https://ai.google.dev
    python scripts/build_vector_index.py
"""
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS


REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "vector_index"


def fetch_products(database_url: str) -> list[tuple]:
    engine = create_engine(database_url)
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, name, description FROM Products_2")
        ).fetchall()
    return [(r[0], r[1], r[2]) for r in rows]


def main() -> int:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set.", file=sys.stderr)
        return 1
    if not os.environ.get("GOOGLE_API_KEY"):
        print("ERROR: GOOGLE_API_KEY not set.", file=sys.stderr)
        return 1

    products = fetch_products(database_url)
    if not products:
        print("ERROR: no products found — seed the database first.", file=sys.stderr)
        return 1

    docs = [f"{pid}\n{name}\n{desc or ''}" for pid, name, desc in products]
    print(f"Embedding {len(docs)} products...")

    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    store = FAISS.from_texts(docs, embeddings)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    store.save_local(str(OUTPUT_DIR))
    print(f"Saved FAISS index to {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
