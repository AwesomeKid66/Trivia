from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).parent.parent / 'data' / 'database.db'

def insert_question(topic, question, answer, got_wrong=0) -> None:
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

    cursor.execute('''
        INSERT INTO questions (topic, question, answer, got_wrong)
        VALUES (?, ?, ?, ?)
    ''', (topic, question, answer, got_wrong))

    conn.commit()
    conn.close()

def delete_question(id) -> str:
    """
    Deletes a trivia question from the database
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('DELETE FROM questions WHERE id=?', (id))

    conn.commit()
    conn.close()

def get_unique_topics() -> list:
    """
    Obtains all unique topics from the database
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Select distinct topics
    cursor.execute('SELECT DISTINCT topic FROM questions')
    rows = cursor.fetchall()

    conn.close()

    # Extract topics from rows (each row is a tuple like ('Harry Potter',))
    topics = [row[0] for row in rows]
    return topics


def add_question() -> None:
    """
    Inserts as many trivia questions as necessary into the database.
    """

    topics = get_unique_topics()

    topic = input(f'Please Use One of These {topics}')

    question = input('What is the question?')

    answer = input('What is the answer?')

    insert_question(topic,question,answer)
