import json
import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

notion = Client(auth=os.getenv("NOTION_TOKEN"))
db_id = os.getenv("NOTION_DATABASE_ID")

# Base data directory
BASE_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

def get_folder_from_page(page):
    props = page["properties"]
    folder_prop = props.get("Folder", {})

    # If Folder is a select property
    if folder_prop.get("select") and folder_prop["select"].get("name"):
        return folder_prop["select"]["name"]

    # If Folder is a text property
    if folder_prop.get("rich_text") and len(folder_prop["rich_text"]) > 0:
        return folder_prop["rich_text"][0]["text"]["content"]

    # Default folder if none set
    return "default"

def load_json(folder):
    filepath = os.path.join(BASE_DATA_DIR, folder, "all_questions.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: JSON file {filepath} is corrupted, starting fresh.")
                return []
    return []

def save_json(folder, data):
    folder_path = os.path.join(BASE_DATA_DIR, folder)
    os.makedirs(folder_path, exist_ok=True)
    filepath = os.path.join(folder_path, "all_questions.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def fetch_new_questions():
    new_questions_per_folder = {}
    query_results = notion.databases.query(database_id=db_id)

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
        folder = get_folder_from_page(page)

        # Prepare question dict
        question_entry = {
            "question": question,
            "answer": answer,
        }

        # Add to folder bucket
        new_questions_per_folder.setdefault(folder, []).append(question_entry)

        # Mark page as synced
        notion.pages.update(
            page_id=page["id"],
            properties={
                "Synced": {"checkbox": True}
            }
        )

    return new_questions_per_folder

def main():
    new_questions = fetch_new_questions()

    if not new_questions:
        print("✅ No new questions found.")
        return

    for folder, questions in new_questions.items():
        print(f"Adding {len(questions)} questions to folder '{folder}'")

        existing = load_json(folder)
        existing.extend(questions)
        save_json(folder, existing)

    print("✅ All new questions synced and saved.")

if __name__ == "__main__":
    main()