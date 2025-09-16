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
        INSERT INTO questions (topic, question, answer, likelihood)
        VALUES (?, ?, ?, ?)
    """, (topic, question, answer, 3))

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

def add_likelihood_column():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE questions ADD COLUMN likelihood INTEGER DEFAULT 3")
        conn.commit()

def list_questions():
    """List all questions in the database."""
    topics = get_unique_topics()
    for topic in topics:
        print(f"\n--- Topic: {topic} ---")
        questions = load_topic(topic)
        for q in questions:
            print(f"ID: {q[0]} | Q: {q[2]} | A: {q[3]} | Likelihood: {q[4]}")

def interactive_menu():
    while True:
        print("\n=== Trivia Database Manager ===")
        print("1. List all questions")
        print("2. Add a question")
        print("3. Delete question(s)")
        print("4. Modify question or answer")
        print("5. Quit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            list_questions()

        elif choice == "2":
            add_question()

        elif choice == "3":
            ids_str = input("Enter question ID(s) to delete (comma separated): ")
            try:
                ids = [int(x.strip()) for x in ids_str.split(",")]
                delete_questions(ids)
            except ValueError:
                print("Invalid input. Please enter integer IDs separated by commas.")

        elif choice == "4":
            try:
                qid = int(input("Enter the question ID to modify: "))
                field = input("Modify 'question' or 'answer'? ").strip().lower()
                if field not in ("question", "answer"):
                    print("Invalid field. Must be 'question' or 'answer'.")
                    continue
                modify_entry(qid, field)
            except ValueError:
                print("Invalid input. ID must be an integer.")

        elif choice == "5":
            print("Exiting...")
            break

        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    interactive_menu()
