from pathlib import Path
from langchain_text_splitters import CharacterTextSplitter,RecursiveCharacterTextSplitter

SAMPLE = Path("data/chunk_experiment_sample.txt")
SIZES = [128,256,512]
GOLDENS = ["第九条", "复查主要包括以下方面", "视为放弃入学资格"]

def naive_split(text: str , size : int):
    raw = [text[i:i+size] for i in range(0,len(text),size)]
    return [c.strip() for c in raw if c.strip()]

def preview(s , n = 36):
    return s.replace("\n","\\n")[:n]

def report(name : str ,size :int ,chunks: list[str]):
    print(f"\n===== {name} | size={size} | n={len(chunks)} =====")
    for g in GOLDENS:
        hits = [i for i,c in enumerate(chunks) if g in c]
        print(f" golden[{g!r}] in chunks : {hits}")
    for i, c in enumerate(chunks):
        end_ok = c.rstrip().endswith(("。", "；", "！", "？"))
        flag = "" if end_ok else "  <<可能腰斩"
        print(f"  [{i}] len={len(c):3d} head={preview(c)!r} tail={preview(c[-36:])!r}{flag}")

def main():
    text = SAMPLE.read_text(encoding="utf-8").strip()
    print(f"sample_chars={len(text)}")

    for size in SIZES:
        char = CharacterTextSplitter(
            separator="",
            chunk_size=size,
            chunk_overlap=0,
            length_function=len,

        )
        recur = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", "。", "；", "，", " ", ""],
            chunk_size=size,
            chunk_overlap=0,
            length_function=len,
        )
        report("naive", size, naive_split(text, size))
        report("Character", size, char.split_text(text))
        report("Recursive", size, recur.split_text(text))


if __name__ == "__main__":
    main()