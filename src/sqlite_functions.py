from collections import deque
from pathlib import Path
import sqlite3

import numpy as np
from sentence_transformers import SentenceTransformer, util

DB_PATH = Path(__file__).parent.parent / "data" / "database.db"

def insert_question(topic: str, question: str, answer: str) -> None:
    """
    Inserts a trivia question into the database.

    Args:
        topic (str): The topic/category of the question.
        question (str): The trivia question text.
        answer (str): The correct answer.
        got_wrong (int): Number of times answered wrong (default 0).
        db_file (str): Path to SQLite database file.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO questions (topic, question, answer, got_wrong)
        VALUES (?, ?, ?, ?)
    """, (topic, question, answer, 0))

    conn.commit()
    conn.close()

def delete_questions(ids: int | list[int]) -> None:
    """
    Deletes one or more trivia questions from the database.

    Args:
        ids (int | list[int]): The id(s) of the item(s) to delete
    """
    if isinstance(ids, int):
        ids = [ids]  # wrap single int in a list

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        for qid in ids:
            cursor.execute("SELECT * FROM questions WHERE id=?", (qid,))
            row = cursor.fetchone()

            if not row:
                print(f"No question found with id={qid}")
                continue

            user_input = input(
                f"Delete this question (id={qid})?\n"
                f"Question: {row[2]}\n"
                f"Answer: {row[3]}\n"
                f"(y/n): "
            )

            if user_input.lower().strip() == "y":
                cursor.execute("DELETE FROM questions WHERE id=?", (qid,))
                print(f"Deleted question id={qid}")
            else:
                print(f"Skipped question id={qid}")

        conn.commit()

def get_unique_topics() -> list:
    """
    Obtains all unique topics from the database
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Select distinct topics
        cursor.execute("SELECT DISTINCT topic FROM questions")
        rows = cursor.fetchall()

    # Extract topics from rows (each row is a tuple like ('Harry Potter',))
    topics = [row[0] for row in rows]
    return topics


def add_question() -> None:
    """
    Inserts as many trivia questions as necessary into the database.
    """

    topics = get_unique_topics()

    topic = input(f"Please Use One of These {topics}")

    question = input("What is the question?")

    answer = input("What is the answer?")

    insert_question(topic,question,answer)


def load_topic(topic: str) -> list:
    """
    Loads all questions from a given topic

    Args:
        topic (str): name of the topic
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM questions WHERE topic=?", (topic,))

        rows = cursor.fetchall()

    return rows

def normalize_text(x: str) -> str:
    return (x or "").strip().casefold()

def check_for_duplicates(topic: str, threshold: float = 0.8) -> list:
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


def remove_column() -> None:

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # 1. Rename the old table
        cursor.execute("ALTER TABLE questions RENAME TO questions_old;")

        # 2. Create a new table without the 'got_wrong' column
        cursor.execute("""
            CREATE TABLE questions (
                id INTEGER PRIMARY KEY,
                topic TEXT,
                question TEXT,
                answer TEXT
            );
        """)

        # 3. Copy the data over (excluding got_wrong)
        cursor.execute("""
            INSERT INTO questions (id, topic, question, answer)
            SELECT id, topic, question, answer FROM questions_old;
        """)

        # 4. Drop the old table
        cursor.execute("DROP TABLE questions_old;")

        conn.commit()

if __name__ == "__main__":
    # check_for_duplicates("Stranger Things", threshold=0.6)
    delete_questions([1,199,306,244])
