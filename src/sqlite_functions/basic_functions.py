from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).parent.parent.parent / "data" / "database.db"

def insert_question(topic: str, question: str, answer: str) -> None:
    """
    Inserts a trivia question into the database.

    Args:
        topic (str): The topic/category of the question.
        question (str): The trivia question text.
        answer (str): The correct answer.
        db_file (str): Path to SQLite database file.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO questions (topic, question, answer)
        VALUES (?, ?, ?)
    """, (topic, question, answer))

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


def modify_entry(id: int, field: str) -> None:
    """Modify either the question or answer for a given ID interactively.

    Args:
        qid: The ID of the question to update.
        field: Either "question" or "answer".
    """
    if field not in ("question", "answer"):
        raise ValueError("field must be either 'question' or 'answer'")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Fetch current value
        cursor.execute(f"SELECT {field} FROM questions WHERE id = ?", (id,))  # noqa: S608
        row = cursor.fetchone()

        if not row:
            print(f"No entry found with id {id}")
            return

        current_value = row[0]
        print(f"Current {field}: {current_value}")

        confirm = input(f"Would you like to change this {field}? (y/n): ").strip().lower()
        if confirm != "y":
            print("No changes made.")
            return

        # Ask for new value
        new_value = input(f"Enter new {field}: ").strip()

        cursor.execute(f"UPDATE questions SET {field} = ? WHERE id = ?", (new_value, id))  # noqa: S608
        conn.commit()

        print(f"{field.capitalize()} updated successfully.")


if __name__ == "__main__":
    # check_for_duplicates("Stranger Things", threshold=0.6)
    modify_entry(321, "question")
