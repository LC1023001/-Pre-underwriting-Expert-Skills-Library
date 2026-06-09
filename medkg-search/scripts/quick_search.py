"""quick_search.py: medkg语义搜索快捷脚本（PowerShell友好）"""
import sys, os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

query = sys.argv[1] if len(sys.argv) > 1 else "甲状腺结节"
top_n = int(sys.argv[2]) if len(sys.argv) > 2 else 5

# 直接内联搜索逻辑，避免依赖外部脚本路径
import sqlite3, struct, numpy as np
from sentence_transformers import SentenceTransformer

DB = r"C:\Users\lucha\WorkBuddy\medkg\medkg.db"
DIM = 1024

def vec_from_blob(blob):
    return np.frombuffer(blob, dtype=np.float32)

def cosine_sim(a, b):
    return float(np.dot(a, b))

model = SentenceTransformer("BAAI/bge-m3")
query_vec = model.encode([query], normalize_embeddings=True)[0]

conn = sqlite3.connect(DB)
rows = conn.execute(
    "SELECT book, category, content, vector FROM chunks"
).fetchall()
conn.close()

scored = []
for book, cat, content, vec_bytes in rows:
    vec = vec_from_blob(vec_bytes)
    score = cosine_sim(query_vec, vec)
    scored.append((score, book, cat, content))

scored.sort(reverse=True)
print(f"\n=== 医学知识库检索: '{query}' ===\n")
for i, (score, book, cat, content) in enumerate(scored[:top_n]):
    print(f"[{i+1}] 相似度={score:.4f} | {book} | {cat}")
    print(f"内容: {content[:300]}...")
    print()
