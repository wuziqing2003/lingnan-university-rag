from __future__ import annotations
import re
import chromadb
from rank_bm25 import BM25Okapi
from app.rag.chain import get_embedding

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "lingnan_rag_pdfs"


CANDIDATE_N = 10
RRF_K = 60


_bm25: None | BM25Okapi = None
_ids : list[str] = []
_docs : list[str] = []
_id_to_doc : dict[str, str] = {}
###定义一个函数，用来分词
def tokenize(text):
    ##将输入的文本转换为小写
    text = (text or "").lower()
    ##使用正则表达式，将文本中的中文字符和英文单词提取出来
    return re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z0-9]+", text)

def get_collection():
    chroma = chromadb.PersistentClient(path=CHROMA_PATH)
    return chroma.get_or_create_collection(COLLECTION_NAME)
##定义一个函数，用来将collection里面的每个块进行分词，切记每个词出现的次数
##计算每个块有多少个词
def build_bm25_index(force:bool=False):
##定义四个全局变量
    global _bm25, _ids, _docs, _id_to_doc

##判断BM25倒排索引是否已经存在
    if _bm25 is not None and not force:
        return
# Chroma 稠密向量集合
    collection = get_collection()
##在collection里面拿到两个列表
    data = collection.get(include=["documents"])
#一个存放着每个chunk的ID
    _ids = data["ids"] or []
#一个存放着每个chunk的原文
    _docs = data["documents"] or []
#判断这两个是否为空
    if not _ids or not _docs:
         raise RuntimeError("Chroma 集合为空，请先运行 scripts/ingest_pdfs.py 入库")
##将原文的内容进行分词
    tokenized = [tokenize(doc) for doc in _docs]
##计算分词后每个词的出现率，出现率越少分越高
    _bm25 = BM25Okapi(tokenized)

    _id_to_doc = dict(zip(_ids,_docs))

# # 这是 _bm25 对象内部的核心数据结构（简化还原）
# _bm25 = {
#     # 1. 原始词渣列表（留着备用，用于算词频）
#     "corpus": [
#         ['国家', '奖学金', '每生', '每年', '10000', '元'],  # doc_0
#         ['国家', '励志', '奖学金', '每生', '每年', '6000', '元'], # doc_1
#         ['国家', '助学金', '平均', '每生', '每年', '3700', '元'] # doc_2
#     ],
    
#     # 2. 每篇文档的长度（词的数量）
#     "doc_len": [6, 7, 7],  # doc_0有6个词，doc_1有7个词，doc_2有7个词
    
#     # 3. 所有文档的平均长度
#     "avgdl": 6.67,  # (6+7+7)/3 ≈ 6.67

#     # 4. 🔥 最核心的 IDF（逆文档频率）词典
#     # 记录每一个“词”在多少篇文档里出现过（文档频率 DF）
#     "idf": {
#         '国家': 0.0,      # 3篇文档都有 -> log(3/3)=0 -> 这个词毫无区分度（常见词）
#         '奖学金': 0.405,  # 2篇有（doc_0, doc_1）-> log(3/2)=0.405
#         '每生': 0.0,      # 3篇都有 -> 区分度为0（没啥用）
#         '每年': 0.0,      # 3篇都有 -> 区分度为0
#         '10000': 1.099,  # 仅1篇有（doc_0）-> log(3/1)=1.099（权重极高！）
#         '元': 0.0,        # 3篇都有 -> 区分度为0
#         '励志': 1.099,    # 仅1篇有（doc_1）-> 权重极高
#         '6000': 1.099,    # 仅1篇有（doc_1）
#         '助学金': 1.099,  # 仅1篇有（doc_2）-> 能完美区分doc_2
#         '平均': 1.099,    # 仅1篇有（doc_2）
#         '3700': 1.099,    # 仅1篇有（doc_2）
#     }
# }
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


def hybrid_search(question,n_results =3):


    vec_ids = dense_rank(question,n=CANDIDATE_N)
    kw_ids = bm25_rank(question,n=CANDIDATE_N)

    fused_ids = rrf_fuse([vec_ids,kw_ids])[:n_results]


    return [_id_to_doc[i] for i in fused_ids if i in _id_to_doc ]
  

