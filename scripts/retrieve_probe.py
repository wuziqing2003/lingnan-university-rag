import chromadb


from app.rag.chain import embed_client,get_embedding
from playground.test.ingest_pdfs import CHROMA_PATH,COLLECTION_NAME


def probe(question: str,n_results:int=3):
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

    print(f"问题: {question}")
    print("-" * 40)

    for i,(doc,meta,dist) in enumerate(zip(docs,metas,dists),start=1):
        source = (meta or {}).get("source","未知")
        preview = (doc or {})[:200].replace("\n"," ")
        print(f"[{i}],source={source}")
        print(f"    distance={dist:.4f}")
        print(f"    preview={preview}")
        print()


if __name__ == "__main__":
    # 改成你想测的问题
    probe("研究生国家奖学金和国家助学金能不能兼得？")
    probe("研究生三助一辅岗位怎么申请？")