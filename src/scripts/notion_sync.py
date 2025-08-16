from collections import deque
from dataclasses import dataclass
import os

# src/scripts/sync.py
from pathlib import Path
import sys

from dotenv import load_dotenv
from notion_client import Client

# Ensure the project root (parent of 'src') is on sys.path
project_root = Path(__file__).resolve().parent.parent.parent  # up from src/scripts to project root
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.sqlite_functions import insert_question  # noqa: E402


@dataclass
class QA:
    topic: str
    question: str
    answer: str

load_dotenv()

notion = Client(auth=os.getenv("NOTION_TOKEN"))
db_id = os.getenv("NOTION_DATABASE_ID")

# Base data directory
DB_PATH = Path(__file__).parent.parent / "data" / "database.db"

def fetch_new_questions() -> deque:
    new_questions_per_folder = deque()
    query_results = notion.databases.query(
        database_id=db_id,
        filter={
            "property": "Synced",
            "checkbox": {
                "equals": False
            }
        }
    )

    results = query_results.get("results", [])

    for page in results:
        props = page["properties"]

        # Extract question
        question_prop = props.get("Question", {})
        if not question_prop.get("title") or len(question_prop["title"]) == 0:
            print("Skipping page with no Question title.")
            continue
        question = question_prop["title"][0]["text"]["content"].strip()

        # Extract answer
        answer_prop = props.get("Answer", {})
        if not answer_prop.get("rich_text") or len(answer_prop["rich_text"]) == 0:
            print("Skipping page with no Answer.")
            continue
        answer = answer_prop["rich_text"][0]["text"]["content"].strip()

        # Get folder/category for this question
        topic = get_folder_from_page(page)

        data = QA(topic, question, answer)

        # Add to folder bucket
        new_questions_per_folder.append(data)


        # Mark page as synced
        notion.pages.update(
            page_id=page["id"],
            properties={
                "Synced": {"checkbox": True}
            }
        )
    return new_questions_per_folder

def get_folder_from_page(page) -> str:
    props = page["properties"]
    folder_prop = props.get("Topic", {})

    return folder_prop["select"]["name"]

def check_all_synced() -> None:
    query_results = notion.databases.query(
        database_id=db_id,
        filter={
            "property": "Synced",
            "checkbox": {
                "equals": False
            }
        }
    )

    return False if query_results else True

def archive_pages() -> None:
    query_results = notion.databases.query(
        database_id=db_id,
        filter={
            "property": "Synced",
            "checkbox": {
                "equals": True
            }
        }
    )

    results = query_results.get("results", [])

    for page in results:
        notion.pages.update(
            page_id=page["id"],
            archived=True
        )


def main():
    new_questions = fetch_new_questions()

    if not new_questions:
        print("ℹ️ No new questions to sync.")
    else:
        total = 0
        while new_questions:
            item = new_questions.popleft()

            insert_question(item.topic, item.question, item.answer)
            total += 1

        print(f"✅ {total} new questions synced and saved.")

    # Now double-check if everything is synced
    all_synced = check_all_synced()

    if not all_synced:
        print("📦 All pages are synced. Archiving now...")
        archive_pages()
        print("✅ All synced pages archived.")
    else:
        print("⚠️ Some pages are still not synced. Archiving skipped.")

if __name__ == "__main__":
    main()
