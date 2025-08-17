from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).parent.parent.parent / "data" / "database.db"

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