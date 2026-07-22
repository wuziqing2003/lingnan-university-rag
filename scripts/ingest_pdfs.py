from pathlib import Path
import chromadb
import fitz 
from openai import OpenAI
from app.core.config import SiliconFlow_API_KEY
from app.rag.chain import get_embedding
from langchain_text_splitters import RecursiveCharacterTextSplitter
CHUNK_SIZE = 256
CHUNK_OVERLAP = 50
PDF_DIR=Path("data/pdfs")
CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "lingnan_rag_pdfs"  # 新库名，避免和旧 lingnan_rag 搅在一起
RESET = True  # True=先删同名 collection 再重建；第二次全量重跑也建议 True
###创建与硅基流动的连接
embed_client = OpenAI(
    api_key=SiliconFlow_API_KEY,
    base_url="https://api.siliconflow.cn/v1",
)


####提取PDF中的文字，第一步是找到PDF并打开，
# 第二步是将PDF中的内容按页码存储到列表里
##第三步是用换行符把各页文字拼成一个大字符串，去掉首尾空白
def extract_text(pdf_path:Path):
    doc = fitz.open(pdf_path)
    parts = []
    for page in doc:
        parts.append(page.get_text())
    doc.close()
    return "\n".join(parts).strip()

###对文字进行切块
def chunk_text(text:str ,chunk_size:int=CHUNK_SIZE ):
    splitter =  RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", "。", "；", "，", " ", ""],
        chunk_size=chunk_size,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,

    )
    chunks = splitter.split_text(text or "")
    return [c.strip() for c in chunks if c.strip()]
 

def main():
    ##找到路径中的所有PDF,按文件名排序
    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"{PDF_DIR}文件夹里面没有PDF文件")
    ###创建与向量库的连接
    chroma = chromadb.PersistentClient(path=CHROMA_PATH)
    ###全量重建开关，每次执行的时候都会删除原有的collection
    if RESET:
        try:
            chroma.delete_collection(COLLECTION_NAME)
            print(f"已删除旧 collection: {COLLECTION_NAME}")
        except Exception:
            pass
    collection = chroma.get_or_create_collection(COLLECTION_NAME)

    ok_files = 0
    skip_files = []
    total_chunks = 0
    global_i = 0 

    for pdf_path in pdf_files:
        print(f"处理中：{pdf_path.name}")
        text = extract_text(pdf_path)
        if len(text) < 50:
            skip_files.append(pdf_path.name)
            print(f"  -> 跳过（文本过短/可能是扫描件）")
            continue
            
        chunks = chunk_text(text)
        ids, documents, embeddings, metadatas  = [], [], [], []

        for chunk in chunks:
            ids.append(f"{pdf_path.stem}_{global_i}")
            documents.append(chunk)
            embeddings.append(get_embedding(chunk))
            metadatas.append({"source": pdf_path.name})
            global_i += 1
            total_chunks += 1

        collection.add(
            ids = ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        ok_files += 1
        print(f"")
        print(f"  -> 入库 {len(chunks)} 块")

    print("========== 汇总 ==========")
    print(f"成功文件: {ok_files}")
    print(f"跳过文件: {len(skip_files)}")
    for name in skip_files:
        print(f"  - {name}")
    print(f"总块数: {total_chunks}")
    print(f"collection: {COLLECTION_NAME}")
    print("入库完成")


    
if __name__ == "__main__":
    main()


