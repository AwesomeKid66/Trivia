import json
import os
import random
import string

from IPython.display import clear_output
from thefuzz import fuzz


class TriviaGame:
    """
    A class to manage, store, and run trivia quizzes from JSON files.

    Features:
        - Interactive question adding
        - Fuzzy answer matching
        - Learning mode that removes mastered questions
    """

    def __init__(self, dir_name):
        """
        Initialize the TriviaGame and set up file paths.

        Parameters
        ----------
        dir_name : str
            Name of the subdirectory (within '../data') to store questions.
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self._data_dir = os.path.join(base_dir, '..', 'data')
        self._dir_path = os.path.join(self._data_dir, dir_name)
        self._questions_file = os.path.join(self._dir_path, 'all_questions.json')

        os.makedirs(self._dir_path, exist_ok=True)
        self._questions = self._load_questions()

    # =======================
    # === Public Methods ====
    # =======================

    def run_quiz(self, source='all_questions.json', tolerance=85):
        """
        Run a trivia quiz with optional fuzzy matching and spaced repetition.

        Parameters
        ----------
        source : str
            Filename (in the directory) to load questions from. Default is 'all_questions.json'.
        tolerance : int
            Fuzzy match tolerance (0–100). Defaults to 85.
        """
        questions = self._load_json_file(source)
        if not questions:
            print(f'No questions found in {source}. Please add some first!')
            return

        random.shuffle(questions)
        score = 0
        questions_asked = 0

        for i, qa in enumerate(questions, 1):
            print(f"\nQuestion {i}: {qa['question']}")
            if ';' in qa['answer']:
                print("(Separate answers with a semicolon ';')")

            user_answer = input("Your answer: (Type 'exit' to stop quiz) ").strip()
            clear_output(wait=True)
            if user_answer.lower() == 'exit':
                break

            questions_asked += 1
            correct = self._check_answer(user_answer, qa, tolerance)
            correct_answer = qa['answer'].strip()

            if correct:
                print(f'Correct! 🎉   ANSWER: {correct_answer}')
                score += 1

                if source == 'learning':
                    qa['correct_count'] = qa.get('correct_count', 0) + 1
                    if qa['correct_count'] >= 3:
                        questions.remove(qa)
                        print('✅ Mastered! Removed from learning.json.')
                    else:
                        print(f"Progress: {qa['correct_count']} / 3 correct to remove.")
            else:
                print(f'Wrong. Correct answer: {correct_answer}')
                print(f'    You answered: {user_answer}')
                if source != 'learning':
                    self._add_unique_question('learning.json', qa)

        if source == 'learning':
            self._save_json_file('learning.json', questions)

        print(f'\nQuiz complete! You scored {score} out of {questions_asked}.')

    def add_questions_interactively(self):
        """
        Prompt the user to enter trivia questions and answers interactively.
        """
        print("Enter trivia questions. Type 'exit' to stop.")
        while True:
            q = input("Enter a question (or 'exit'): ").strip()
            if q.lower() == 'exit':
                break
            a = input("Enter the answer (or 'exit'): ").strip()
            if a.lower() == 'exit':
                break
            self._add_question(q, a)

    # ==========================
    # === Internal Utilities ===
    # ==========================

    def _add_question(self, question, answer):
        """
        Add a new question-answer pair to the list and save it.
        """
        question = question.strip()
        answer = answer.strip()
        if not question or not answer:
            print('Error: Question and answer cannot be empty.')
            return False
        self._questions.append({'question': question, 'answer': answer})
        self._save_questions()
        print('Question added successfully!')
        return True

    def _check_answer(self, user_answer, qa, tolerance):
        """
        Determine whether the user's answer is correct using normalization and fuzzy matching.
        """
        correct_answer = qa['answer'].strip()
        ignore_words = qa.get('ignore', [])

        if ';' in correct_answer:
            user_parts = self._normalize_list(user_answer, ignore_words)
            correct_parts = self._normalize_list(correct_answer, ignore_words)
            similarity = fuzz.ratio(', '.join(user_parts), ', '.join(correct_parts))
            return user_parts == correct_parts or similarity >= tolerance

        else:
            norm_user = self._normalize(user_answer, ignore_words)
            alternatives = self._get_alternatives(correct_answer)
            for alt in alternatives:
                if norm_user == self._normalize(alt, ignore_words):
                    return True
            similarity = fuzz.ratio(norm_user, self._normalize(correct_answer, ignore_words))
            return similarity >= tolerance

    def _load_questions(self):
        """
        Load all saved questions from 'all_questions.json'.
        """
        if os.path.exists(self._questions_file):
            try:
                with open(self._questions_file) as file:
                    data = json.load(file)
                    return data if isinstance(data, list) else []
            except json.JSONDecodeError:
                print(f'Warning: {self._questions_file} is empty or corrupted.')
        return []

    def _save_questions(self):
        """
        Save the current list of questions to 'all_questions.json'.
        """
        with open(self._questions_file, 'w') as file:
            json.dump(self._questions, file, indent=2)

    def _normalize(self, text, ignore_words=None):
        """
        Normalize a single-answer string: lowercase, remove punctuation, ignore common words.
        """
        words = text.lower().split()
        ignore_words = set(ignore_words or [])
        cleaned = [
            ''.join(ch for ch in word if ch not in string.punctuation)
            for word in words
            if word not in ignore_words
        ]
        return ' '.join(cleaned).strip()

    def _normalize_list(self, answer, ignore_words=None):
        """
        Normalize multi-part answers separated by semicolons.
        """
        ignore_words = set(ignore_words or [])
        return sorted([
            ''.join(ch for ch in part.lower().strip() if ch not in string.punctuation)
            for part in answer.split(';')
            if part.lower().strip() not in ignore_words
        ])

    def _get_alternatives(self, answer):
        """
        Return alternative answers if the main answer contains parenthetical options.
        """
        answer = answer.strip()
        if '(' in answer and ')' in answer:
            before = answer[:answer.index('(')].strip()
            inside = answer[answer.index('(') + 1: answer.index(')')].strip()
            return [before, inside]
        return [answer]

    def _load_json_file(self, filename):
        """
        Load a JSON file and return its contents.
        """
        path = os.path.join(self._dir_path, filename)
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
            except json.JSONDecodeError:
                pass
        return []

    def _save_json_file(self, filename, data):
        """
        Save data (list of questions) to a JSON file.
        """
        path = os.path.join(self._dir_path, filename)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def _add_unique_question(self, filename, question_entry):
        """
        Add a question to a file only if it's not already present.
        """
        data = self._load_json_file(filename)
        if question_entry not in data:
            new_entry = question_entry.copy()
            new_entry['correct_count'] = 0
            data.append(new_entry)
            self._save_json_file(filename, data)
