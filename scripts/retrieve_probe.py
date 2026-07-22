from app.rag.chain import get_embedding
from app.rag.hybrid import hybrid_search, dense_rank, build_bm25_index, _id_to_doc
from scripts.ingest_pdfs import CHROMA_PATH, COLLECTION_NAME
import chromadb


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

if __name__ == "__main__":
    q1 = "研究生三助一辅岗位怎么申请？"
    q2 = "研究生国家奖学金和国家助学金有什么区别？"

    probe_dense(q1)
    probe_hybrid(q1)
    probe_dense(q2)
    probe_hybrid(q2)
























    