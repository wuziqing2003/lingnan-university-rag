
import jieba
import chromadb
from rank_bm25 import BM25Okapi
from app.rag.chain import get_embedding
from concurrent.futures import ThreadPoolExecutor

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "lingnan_rag_pdfs"


CANDIDATE_N = 10
RRF_K = 60


_bm25: None | BM25Okapi = None
_ids : list[str] = []
_docs : list[str] = []
_id_to_doc : dict[str, str] = {}
_id_to_meta : dict[str,dict] = {}
for _w in (
    "三助一辅",
    "国家奖学金",
    "国家助学金",
    "学业奖学金",
    "保留入学资格",
    "学业预警",
    "勤工助学",
):

    jieba.add_word(_w)

def tokenize(text):
    text = (text or "").lower()
    tokens=[]
    for token in jieba.lcut(text):
        token = token.strip()
        if not token:
            continue
        if token in {"\n", "\r", "\t"}:
            continue
        if all(not ch.isalnum() and not ("\u4e00" <= ch <= "\u9fff") for ch in token):
            continue
        tokens.append(token)
    return tokens


def get_collection():
    chroma = chromadb.PersistentClient(path=CHROMA_PATH)
    return chroma.get_or_create_collection(COLLECTION_NAME)
##定义一个函数，用来将collection里面的每个块进行分词，切记每个词出现的次数
##计算每个块有多少个词
def build_bm25_index(force:bool=False):
##定义四个全局变量
    global _bm25, _ids, _docs, _id_to_doc,_id_to_meta
    if _bm25 is not None and not force:
        return
    collection = get_collection()
    data = collection.get(include=["documents","metadatas"])
    _ids = data["ids"] or []
    _docs = data["documents"] or []
    metas = data["metadatas"] or []
    if not _ids or not _docs:
         raise RuntimeError("Chroma 集合为空，请先运行 scripts/ingest_pdfs.py 入库")
    tokenized = [tokenize(doc) for doc in _docs]
    _bm25 = BM25Okapi(tokenized)
    _id_to_doc = dict(zip(_ids,_docs))
    _id_to_meta = dict(zip(_ids,metas))

###根据向量排名
def dense_rank(question,n=CANDIDATE_N):
##打开仓库
    collection = get_collection()
###将问题转换为向量去向量库里取十条最最相似的结果
    result = collection.query(
        query_embeddings=[get_embedding(question)],
        n_results=n,      
    )
###返回最相似的这十条结果的ID
    return result["ids"][0] or []


##根据分词排名
def bm25_rank(question,n):
##先调用函数生成一个BM25索引
    build_bm25_index()
##直接断言_bm25已经存在了，如果错误直接终止
    assert _bm25 is  not None
###将问题分词之后去给_bm25里面的每个词赋分
    scores = _bm25.get_scores(tokenize(question))
##之后根据分数进行倒序排序，分数高的在前面例如ranked_idx = [1, 3, 4, 0, 2]
    ranked_idx = sorted(range(len(scores)),key=lambda i:scores[i],reverse=True)
##只取排名前十，记住列表里面存放的是每个分数对应的下标
    top_idx = ranked_idx[:n]
###返回一个新的列表，列表里面存的是根据分数排名的对应文档的ID
    return [_ids[i] for i in top_idx]


##定义一个根据两个列表排名得出总排名的函数
def rrf_fuse(rank_lists, k=RRF_K):
##先创建一个空字典，用来存在两个列表综合得出的ID和对应分数
    scores:dict[str,float] = {}
##遍历两个列表
    for ranking in rank_lists:
####遍历每个列表的里面的每个ID，比如列表里面第一个ID那rank=1
        for rank,doc_id in enumerate(ranking,start=1):
##计算每个ID得到的综合分数，在原有的分数上进行叠加
            scores[doc_id] = scores.get(doc_id,0.0) + 1.0/(k+rank)
###对字典中得出的每个ID对应的分数进行排名，最终拿到一个列表，里面存放着ID
    return sorted(scores.keys(),key=lambda i:scores[i],reverse=True)


def hybrid_search(question,n_results =10):
    with ThreadPoolExecutor(max_workers=2) as pool:
        dense_fut = pool.submit(dense_rank,question,n=CANDIDATE_N)
        kw_fut = pool.submit(bm25_rank,question,n=CANDIDATE_N)
        vec_ids = dense_fut.result()
        kw_ids = kw_fut.result()



    fused_ids = rrf_fuse([vec_ids,kw_ids])[:n_results]

    hits = []
    for doc_id in fused_ids:
        if doc_id not in _id_to_doc:
            continue
        meta = _id_to_meta.get(doc_id) or {}
        hits.append({
            "id":doc_id,
            "text":_id_to_doc[doc_id],
            "source": meta.get("source", "未知"),
            "page": meta.get("page"), 
        })
    return hits
  

