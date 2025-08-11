import sqlite3

def insert_question(topic, question, answer, got_wrong=0, db_file="trivia.db"):
    """
    Inserts a trivia question into the database.

    Args:
        topic (str): The topic/category of the question.
        question (str): The trivia question text.
        answer (str): The correct answer.
        got_wrong (int): Number of times answered wrong (default 0).
        db_file (str): Path to SQLite database file.
    """
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO questions (topic, question, answer, got_wrong)
        VALUES (?, ?, ?, ?)
    """, (topic, question, answer, got_wrong))

    conn.commit()
    conn.close()
