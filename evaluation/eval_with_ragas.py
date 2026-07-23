"""用法（在项目根目录）：
python evaluation/eval_with_ragas.py --mode no_rerank
python evaluation/eval_with_ragas.py --mode rerank
"""
import sys
import argparse
import json

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datetime import datetime
from datasets import Dataset
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas import evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import answer_relevancy, context_precision, faithfulness

from app.core.config import DEEPSEEK_API_KEY, SiliconFlow_API_KEY
from app.rag.chain import SYSTEM_PROMPT
from app.rag.hybrid import hybrid_search
from app.rag.rerank import rerank_documents

answer_relevancy.strictness = 1
ROOT = Path(__file__).resolve().parents[1]
GT_PATH = ROOT / "evaluation" / "ground_truth.json"


def get_contexts(question: str, mode: str) -> list[str]:
    candidates = hybrid_search(question, n_results=10)
    if mode == "rerank":
        return rerank_documents(question, candidates, top_n=3)
    return candidates[:3]


def get_answer(question: str, contexts: list[str]) -> str:
    llm = ChatOpenAI(
        model="deepseek-chat",  
        base_url="https://api.deepseek.com",
        api_key=DEEPSEEK_API_KEY,
        temperature=0,
        max_tokens=1024,
        streaming=False,
    )
    context = "\n\n".join(contexts)
    msg = [
        ("system", SYSTEM_PROMPT),
        ("human", f"【检索资料】\n{context}\n\n【问题】\n{question}"),
    ]
    content = llm.invoke(msg).content
    if isinstance(content, list):
        content = "".join(
            part.get("text", str(part)) if isinstance(part, dict) else str(part)
            for part in content
        )
    return str(content).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["no_rerank", "rerank"], required=True)
    parser.add_argument("--gt", default=str(GT_PATH))
    parser.add_argument(
        "--out",
        default=None,
        help="默认写到 evaluation/results_{mode}.json",
    )
    args = parser.parse_args()
    out_path = Path(args.out or ROOT / "evaluation" / f"results_{args.mode}.json")

    items = json.loads(Path(args.gt).read_text(encoding="utf-8"))

    questions, answers, contexts_list, gts = [], [], [], []
    for item in items:
        q = item["question"]
        ctx = get_contexts(q, args.mode)
        ans = get_answer(q, ctx)
        print(f"[{item['id']}] done")
        questions.append(q)
        answers.append(ans)
        contexts_list.append(ctx)
        gts.append(item["ground_truth"])


    dataset = Dataset.from_dict(
        {
            "user_input": questions,
            "response": answers,
            "retrieved_contexts": contexts_list,
            "reference": gts,
        }
    )

    judge = LangchainLLMWrapper(
        ChatOpenAI(
            model="deepseek-chat",
            base_url="https://api.deepseek.com",
            api_key=DEEPSEEK_API_KEY,
            temperature=0,
            max_tokens=4096,
        )
    )
    emb = LangchainEmbeddingsWrapper(
        OpenAIEmbeddings(
            model="BAAI/bge-large-zh-v1.5",
            base_url="https://api.siliconflow.cn/v1",
            api_key=SiliconFlow_API_KEY,
            check_embedding_ctx_length=False,
        )
    )

    result = evaluate(
        dataset,
        metrics=[context_precision, faithfulness, answer_relevancy],
        llm=judge,
        embeddings=emb,
    )
    print(result)

    scores = {}
    for k, v in result._repr_dict.items():
        scores[k] = None if v != v else float(v)  # NaN -> None

    summary = {
        "mode": args.mode,
        "n": len(items),
        "time": datetime.now().isoformat(timespec="seconds"),
        "scores": scores,
    }
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved:", out_path)


if __name__ == "__main__":
    main()