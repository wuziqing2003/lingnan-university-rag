import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.rag.chain import get_embedding
from app.rag.hybrid import hybrid_search
from app.rag.rerank import rerank_documents
from scripts.ingest_pdfs import CHROMA_PATH, COLLECTION_NAME

import chromadb
from app.rag.rewrite import rewrite_query

def probe_dense(question:str,n_results=3):
    chroma = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = chroma.get_or_create_collection(COLLECTION_NAME)

    result = collection.query(
        query_embeddings=[get_embedding(question)],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
    docs = result["documents"][0] or []
    metas = result["metadatas"][0] or []
    dists = result["distances"][0] or []

    print(f"[DENSE] 问题: {question}")
    print("-" * 40)

    for i,(doc,meta,dist) in enumerate(zip(docs,metas,dists),start=1):
        source = (meta or {}).get("source","未知")
        preview = (doc or "")[:200].replace("\n"," ")
        print(f"[{i}] source={source} distance{dist:.4f}")
        print(f"      preview={preview}")
        print()

def probe_hybrid(question,n_results=3):
    docs = hybrid_search(question, n_results=n_results)
    print(f"[HYBRID] 问题: {question}")
    print("-" * 40)
    for i,doc in enumerate(docs,start=1):
        preview = (doc or "")[:200].replace("\n", " ")
        print(f"[{i}] preview={preview}")
        print()

def probe_rerank(question:str):
    candidates = hybrid_search(question,n_results=10)
    print(f"[HYBRID Top10] 问题: {question}")
    for i,doc in enumerate(candidates,start=1):
        print(f"  cand[{i}] {(doc or '')[:120].replace(chr(10), ' ')}")

    reranked = rerank_documents(question,candidates,top_n=3)
    print(f"[RERANK Top3] 问题: {question}")
    for i, doc in enumerate(reranked, 1):
        print(f"  [{i}] {(doc or '')[:200].replace(chr(10), ' ')}")
    print()


def compare_hybrid_vs_rerank(question: str, gold_keywords: list[str]):
    candidates = hybrid_search(question, n_results=10)
    hybrid_top3 = candidates[:3]
    rerank_top3 = rerank_documents(question, candidates, top_n=3)
    def hit_rank(docs):
        for i, d in enumerate(docs, 1):
            if all(k in (d or "") for k in gold_keywords):
                return i
        return None  # Top3 未命中
    print(f"问题: {question}")
    print(f"金标关键词: {gold_keywords}")
    print(f"Hybrid  Top3 金标位次: {hit_rank(hybrid_top3)}")
    print(f"Rerank  Top3 金标位次: {hit_rank(rerank_top3)}")








if __name__ == "__main__":




    q = "助学金怎么领？"
    print("原问:", q)
    print("改写:", rewrite_query(q))


















    