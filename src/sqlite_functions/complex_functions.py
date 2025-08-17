from collections import deque
from pathlib import Path
import sqlite3

import numpy as np
from sentence_transformers import SentenceTransformer

DB_PATH = Path(__file__).parent.parent.parent / "data" / "database.db"


def normalize_text(x: str) -> str:
    return (x or "").strip().casefold()

def check_for_duplicates(topic: str, threshold: float = 0.6) -> list:
    """
    Find groups of semantically similar questions in the database for a given topic.

    Args:
        topic (str): The topic to filter questions on.
        threshold (float): Cosine similarity threshold (0-1). Default=0.8

    Returns:
        list of clusters, where each cluster is a list of dicts with id/question/answer
    """
    model = SentenceTransformer("all-MiniLM-L6-v2")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, question, answer FROM questions WHERE topic = ?",
            (topic,),
        )
        rows = cursor.fetchall()

    if not rows:
        print(f"No questions found for topic: {topic}")
        return []

    ids = [row[0] for row in rows]
    questions = [row[1] for row in rows]
    answers = [row[2] for row in rows]

    # Compute embeddings (normalized so dot = cosine similarity)
    embeddings = model.encode(questions, normalize_embeddings=True)
    embeddings = np.asarray(embeddings, dtype=np.float32)

    # Cosine similarity matrix
    sim_matrix = embeddings @ embeddings.T
    n = len(rows)

    # Build adjacency graph
    adj = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            score = float(sim_matrix[i, j])
            if score >= threshold:
                adj[i].append(j)
                adj[j].append(i)

    # Find connected components (clusters)
    visited = [False] * n
    clusters = []
    for i in range(n):
        if visited[i] or not adj[i]:
            continue
        comp = []
        q = deque([i])
        visited[i] = True
        while q:
            u = q.popleft()
            comp.append({
                "id": ids[u],
                "question": questions[u],
                "answer": answers[u],
            })
            for v in adj[u]:
                if not visited[v]:
                    visited[v] = True
                    q.append(v)
        if len(comp) >= 2:  # only keep real clusters
            clusters.append(comp)

    # Print clusters for review
    for ci, comp in enumerate(clusters, start=1):
        print(f"\n=== Cluster {ci} (size={len(comp)}) ===")
        for item in comp:
            print(f"[{item['id']}] Q: {item['question']} | A: {item['answer']}")

    return clusters

if __name__ == "__main__":
    check_for_duplicates("Marvel")