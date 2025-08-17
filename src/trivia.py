from pathlib import Path
import random
import string

from thefuzz import fuzz

import sqlite_functions.basic_functions as sqlf


class TriviaGame:
    """
    A class to manage, store, and run trivia quizzes from SQLite database.

    Features:
        - Interactive question adding
        - Fuzzy answer matching
        - Learning mode that removes mastered questions
    """

    def __init__(self):
        """
        Initialize the TriviaGame and set up file paths.
        """
        self._DB_PATH = Path(__file__).parent.parent / "data" / "database.db"

    # =======================
    # === Public Methods ====
    # =======================

    def run_quiz(self, topic: str):
        """
        Run a trivia quiz with optional fuzzy matching and spaced repetition.

        Parameters
        ----------
        source : str
            Filename (in the directory) to load questions from. Default is 'all_questions.json'.
        """
        questions = sqlf.load_topic(topic)
        if not questions:
            print(f"No questions found for {topic}. Please add some first!")
            return

        random.shuffle(questions)
        score = 0
        questions_asked = 0

        for i, qa in enumerate(questions, 1):
            question = qa[2]
            answer = qa[3].strip()
            print(f"\nQuestion {i}: {question}")
            if ";" in answer:
                print("(Separate answers with a semicolon ';')")

            user_answer = input("Your answer: (Type 'exit' to stop quiz) ").lower().strip()
            if user_answer == "exit":
                break

            questions_asked += 1
            correct = self._check_answer(user_answer, answer)

            if correct:
                print(f"Correct! 🎉   ANSWER: {answer}")
                score += 1
            else:
                print(f"InCorrect :(.  ANSWER: {answer}")

        print(f"\nQuiz complete! You scored {score} out of {questions_asked}.")

    # ==========================
    # === Internal Utilities ===
    # ==========================

    def _check_answer(self, user_answer, correct_answer):
        """
        Determine whether the user's answer is correct using normalization and fuzzy matching.
        """
        tolerance = 85

        if ";" in correct_answer:
            user_parts = self._normalize_list(user_answer)
            correct_parts = self._normalize_list(correct_answer)
            similarity = fuzz.ratio(", ".join(user_parts), ", ".join(correct_parts))
            return similarity >= tolerance

        else:
            norm_user_answer = self._normalize(user_answer)
            alternatives = self._get_alternatives(correct_answer)
            for alt in alternatives:
                if norm_user_answer == self._normalize(alt):
                    return True
            similarity = fuzz.ratio(norm_user_answer, self._normalize(correct_answer))
            return similarity >= tolerance

    def _normalize(self, text):
        """
        Normalize a single-answer string: lowercase, remove punctuation, ignore common words.
        """
        words = text.lower().split()
        cleaned = [
            "".join(ch for ch in word if ch not in string.punctuation)
            for word in words
        ]
        return " ".join(cleaned).strip()

    def _normalize_list(self, answer):
        """
        Normalize multi-part answers separated by semicolons.
        """
        return sorted([
            "".join(ch for ch in answer_part.lower().strip() if ch not in string.punctuation)
            for answer_part in answer.split(";")
        ])

    def _get_alternatives(self, answer):
        """
        Return alternative answers if the main answer contains parenthetical options.
        """
        answer = answer.strip()
        if "(" in answer and ")" in answer:
            before = answer[:answer.index("(")].strip()
            inside = answer[answer.index("(") + 1: answer.index(")")].strip()
            return [before, inside]
        return [answer]

