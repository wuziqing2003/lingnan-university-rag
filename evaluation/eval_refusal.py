"""用法（在项目根目录）：
python evaluation/eval_refusal.py
python evaluation/eval_refusal.py --mode no_rerank
"""
import sys
import argparse
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluation.eval_with_ragas import get_contexts, get_answer,_text

ROOT = Path(__file__).resolve().parents[1]
GOLD_PATH = ROOT / "evaluation" / "refusal_gold.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["no_rerank", "rerank"], default="rerank")
    parser.add_argument("--gold", default=str(GOLD_PATH))
    parser.add_argument(
        "--out",
        default=str(ROOT / "evaluation" / "refusal_run.json"),
        help="把每题问答落盘，方便事后打标",
    )
    args = parser.parse_args()

    items = json.loads(Path(args.gold).read_text(encoding="utf-8"))
    records = []

    for item in items:
        q = item["question"]
        ctx = get_contexts(q, args.mode)
        ans = get_answer(q, _text(ctx))

        print(f"\n[{item['id']}] expect={item['expect']}")
        print(f"Q: {q}")
        print(f"A: {ans}")
        print("--- contexts preview ---")
        for i, c in enumerate(ctx, 1):
            preview = (c or "").replace("\n", " ")[:200]
            print(f"  [{i}] {preview}")
        print("-" * 40)

        records.append(
            {
                "id": item["id"],
                "expect": item["expect"],
                "question": q,
                "answer": ans,
                "contexts": ctx,
                "gold_points": item.get("gold_points", []),
                "forbidden": item.get("forbidden", []),
            }
        )

    Path(args.out).write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nsaved: {args.out}")


if __name__ == "__main__":
    main()