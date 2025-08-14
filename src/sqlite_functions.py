from pathlib import Path
import sqlite3

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

def delete_question(id: int) -> list:
    """
    Deletes a trivia question from the database

    Args:
        id (int): The id of the item to delete
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM questions WHERE id=?", (id,))
        row = cursor.fetchone()

        user_input = input(f"Is this the question and answer you would like to delete(y/n)?\nQuestion: {row[2]}\nAnswer: {row[3]}\n")
        if user_input.lower().strip() == "n":
            return
        cursor.execute("DELETE FROM questions WHERE id=?", (id,))

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

def check_for_duplicates() -> list:
    """
    Checks if there are any possible duplicate questions/answer in the database.
    Currently just checks if the answers are the same and flags if they are
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("""SELECT answer, COUNT(*) AS count"
                       FROM questions
                       GROUP BY answer
                       HAVING COUNT(*) > 1""")
        rows = cursor.fetchall

    return rows
