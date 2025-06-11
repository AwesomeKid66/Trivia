import json
import os
import string
import random
from thefuzz import fuzz
from IPython.display import clear_output

class TriviaGame:
    def __init__(self, filename="marvel.json"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(base_dir, "..", "data")
        self.filename = os.path.join(self.data_dir, filename)
        self.questions = self.load_questions()

    def load_questions(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as file:
                    data = json.load(file)
                    if isinstance(data, list):
                        return data
                    else:
                        print(f"Warning: {self.filename} does not contain a list, starting fresh.")
                        return []
            except json.JSONDecodeError:
                print(f"Warning: {self.filename} is empty or corrupted, starting fresh.")
                return []
        else:
            return []

    def save_questions(self):
        with open(self.filename, "w") as file:
            json.dump(self.questions, file, indent=2)

    def add_question(self, question, answer):
        question = question.strip()
        answer = answer.strip()
        if not question or not answer:
            print("Error: Question and answer cannot be empty.")
            return False
        self.questions.append({"question": question, "answer": answer})
        self.save_questions()
        print("Question added successfully!")
        return True

    def normalize(self, text, ignore_words=None):
        words = text.lower().split()
        ignore_words = set(ignore_words or [])
        cleaned_words = [
            ''.join(ch for ch in word if ch not in string.punctuation)
            for word in words
            if word not in ignore_words
        ]
        return ' '.join(cleaned_words).strip()

    def run_quiz(self, source="marvel", tolerance=85):
        filename = os.path.join(self.data_dir, f"{source}.json")
        questions = self.load_json_file(filename)

        if not questions:
            print(f"No questions found in {filename}. Please add some first!")
            return

        questions_shuffled = questions[:]
        random.shuffle(questions_shuffled)

        score = 0
        for i, qa in enumerate(questions_shuffled, 1):
            print(f"\nQuestion {i}: {qa['question']}")
            if ';' in qa['answer']:
                print("(Please separate each part of your answer with a semicolon ';')")
            user_answer = input("Your answer: ").strip()

            clear_output(wait=True)

            if user_answer.lower() == 'exit':
                break

            correct_answer = qa['answer'].strip()

            def normalize_list(answer, ignore_words=None):
                ignore_words = set(ignore_words or [])
                return sorted([
                    ''.join(ch for ch in part.lower().strip() if ch not in string.punctuation)
                    for part in answer.split(';')
                    if part.lower().strip() not in ignore_words
                ])

            if ';' in correct_answer:
                ignore_words = qa.get("ignore", [])
                user_parts = normalize_list(user_answer, ignore_words)
                correct_parts = normalize_list(correct_answer, ignore_words)
                is_correct = user_parts == correct_parts
                similarity = fuzz.ratio(', '.join(user_parts), ', '.join(correct_parts))
            else:
                ignore_words = qa.get("ignore", [])
                alternatives = self.get_alternatives(correct_answer)
                norm_user = self.normalize(user_answer, ignore_words)
                norm_correct = self.normalize(correct_answer, ignore_words)
                is_correct = False
                for alt in alternatives:
                    norm_alt = self.normalize(alt, ignore_words)
                    if norm_user == norm_alt:
                        is_correct = True
                        break

                if not is_correct:
                    similarity = fuzz.ratio(norm_user, norm_correct)
                    is_correct = similarity >= tolerance
                else:
                    similarity = 100  # perfect match

            if is_correct:
                print(f"Correct! 🎉   ANSWER: {correct_answer}")
                score += 1

                if source == "learning":
                    qa["correct_count"] = qa.get("correct_count", 0) + 1
                    if qa["correct_count"] >= 3:
                        questions.remove(qa)
                        print("✅ Mastered! Removed from learning.json.")
                    else:
                        print(f"Progress: {qa['correct_count']} / 3 correct to remove.")
            else:
                print(f"""Wrong. The correct answer was: {correct_answer} \n    You answered: {user_answer} \n similarity:{similarity} ;; tolerance:{tolerance}""")
                if source != "learning":
                    self.add_unique_question("learning.json", qa)

        if source == "learning":
            self.save_json_file("learning.json", questions)

        print(f"\nQuiz complete! You scored {score} out of {len(questions_shuffled)}.")

    def load_json_file(self, filename):
        full_path = os.path.join(self.data_dir, filename) if not os.path.isabs(filename) else filename
        if os.path.exists(full_path):
            try:
                with open(full_path, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
            except json.JSONDecodeError:
                pass
        return []

    def save_json_file(self, filename, data):
        full_path = os.path.join(self.data_dir, filename) if not os.path.isabs(filename) else filename
        with open(full_path, "w") as f:
            json.dump(data, f, indent=2)

    def add_unique_question(self, filename, question_entry):
        data = self.load_json_file(filename)
        if question_entry not in data:
            question_entry = question_entry.copy()  # Avoid mutating original
            question_entry["correct_count"] = 0
            self.save_json_file(filename, data + [question_entry])

    def get_alternatives(self, answer):
        answer = answer.strip()
        if '(' in answer and ')' in answer:
            before = answer[:answer.index('(')].strip()
            inside = answer[answer.index('(')+1 : answer.index(')')].strip()
            return [before, inside]
        else:
            return [answer]
