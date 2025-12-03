import os
from pathlib import Path
import random
import sqlite3

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

# -------------------------
# Basic Flask / DB setup
# -------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "database" / "database.db"

app = Flask(__name__, template_folder="templates")

# Config from environment, with safe dev defaults
app.config["SECRET_KEY"] = os.getenv("TRIVIA_SECRET_KEY", "dev-secret-key")
DB_PATH = Path(os.getenv("TRIVIA_DB_PATH", DEFAULT_DB_PATH))


def normalize_user_name(raw):
    """Strip whitespace and ensure we always have a simple string."""
    return (raw or "").strip()


def get_db():
    """Open a new SQLite connection. Caller must close it."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """
    Ensure the progress table + unique index exist.

    Matches your Django model: user_name, question_id, status, updated_at.
    (questions table already exists from your original DB.) :contentReference[oaicite:0]{index=0}
    """
    conn = get_db()
    cur = conn.cursor()

    # progress table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name VARCHAR(100) NOT NULL,
            question_id INTEGER NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'unanswered',
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
        );
        """
    )

    # unique(user_name, question_id) so we can upsert
    cur.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS progress_user_question_uniq
        ON progress(user_name, question_id);
        """
    )

    conn.commit()
    conn.close()


# -------------------------
# HTML routes (pages)
# -------------------------


@app.route("/")
def index():
    """
    Topic list page (home).

    Shows distinct topics from the questions table.
    """
    conn = get_db()
    cur = conn.execute(
        "SELECT DISTINCT topic FROM questions WHERE topic IS NOT NULL ORDER BY topic;"
    )
    topics = [row["topic"] for row in cur.fetchall()]
    conn.close()

    return render_template("index.html", topics=topics)


@app.route("/study/<topic>/enter/")
def enter_name(topic):
    """
    Page where user types their name before studying a topic.
    """
    return render_template("enter_name.html", topic=topic)


@app.route("/study/<topic>/")
def study(topic):
    """
    Study mode:
      - ?user=<name>  (required)
      - ?mode=all (default) OR mode=missed

    mode=all:
      - all questions for the topic, minus those marked 'correct'

    mode=missed:
      - only questions currently marked 'wrong' for this user & topic
    """
    raw_name = request.args.get("user")
    user_name = normalize_user_name(raw_name)

    if not user_name:
        # bounce back to enter-name if missing/empty
        return render_template("enter_name.html", topic=topic)

    mode = request.args.get("mode", "all")
    if mode not in ("all", "missed"):
        mode = "all"

    conn = get_db()

    questions = []

    if mode == "missed":
        # Only questions currently marked wrong
        cur = conn.execute(
            """
            SELECT q.id, q.question, q.answer, q.likelihood
            FROM questions q
            JOIN progress p ON p.question_id = q.id
            WHERE q.topic = ?
              AND p.user_name = ?
              AND p.status = 'wrong';
            """,
            (topic, user_name),
        )
        for row in cur.fetchall():
            questions.append(
                {
                    "id": row["id"],
                    "question": row["question"],
                    "answer": row["answer"],
                    "likelihood": row["likelihood"],
                }
            )
    else:
        # All questions for this topic, excluding ones the user already got correct
        q_cur = conn.execute(
            "SELECT id, question, answer, likelihood FROM questions WHERE topic = ?;",
            (topic,),
        )
        for row in q_cur.fetchall():
            qid = row["id"]
            p_cur = conn.execute(
                """
                SELECT status
                FROM progress
                WHERE user_name = ? AND question_id = ? AND status = 'correct';
                """,
                (user_name, qid),
            )
            if p_cur.fetchone() is None:
                questions.append(
                    {
                        "id": row["id"],
                        "question": row["question"],
                        "answer": row["answer"],
                        "likelihood": row["likelihood"],
                    }
                )

    conn.close()

    return render_template(
        "study.html",
        topic=topic,
        questions=questions,
        user=user_name,
        mode=mode,
    )


@app.route("/stats/<user_name>/")
def stats(user_name):
    """
    Stats page for a user:
      - overall totals
      - per-topic breakdown
      - lists of questions (correct / wrong) per topic
    """
    user_name = normalize_user_name(user_name)
    conn = get_db()

    # Overall totals
    cur = conn.execute(
        """
        SELECT
            SUM(CASE WHEN status = 'correct' THEN 1 ELSE 0 END) AS correct_count,
            SUM(CASE WHEN status = 'wrong' THEN 1 ELSE 0 END) AS wrong_count,
            COUNT(*) AS total_count
        FROM progress
        WHERE user_name = ?;
        """,
        (user_name,),
    )
    overall_row = cur.fetchone()

    if not overall_row or overall_row["total_count"] is None:
        overall = None
    else:
        total = overall_row["total_count"]
        correct = overall_row["correct_count"] or 0
        wrong = overall_row["wrong_count"] or 0
        completion = (correct / total * 100.0) if total else 0.0
        overall = {
            "total": total,
            "correct": correct,
            "wrong": wrong,
            "completion": completion,
        }

    # Per-topic breakdown
    cur = conn.execute(
        """
        SELECT
            q.topic AS topic,
            SUM(CASE WHEN p.status = 'correct' THEN 1 ELSE 0 END) AS correct_count,
            SUM(CASE WHEN p.status = 'wrong' THEN 1 ELSE 0 END) AS wrong_count,
            COUNT(*) AS total_count
        FROM progress p
        JOIN questions q ON q.id = p.question_id
        WHERE p.user_name = ?
        GROUP BY q.topic
        ORDER BY q.topic;
        """,
        (user_name,),
    )
    topic_rows = [
        {
            "topic": row["topic"],
            "correct": row["correct_count"] or 0,
            "wrong": row["wrong_count"] or 0,
            "total": row["total_count"] or 0,
        }
        for row in cur.fetchall()
    ]

    # Detailed questions by topic & status
    cur = conn.execute(
        """
        SELECT
            q.id AS question_id,
            q.topic AS topic,
            q.question AS question_text,
            q.answer AS answer_text,
            p.status AS status,
            p.updated_at AS updated_at
        FROM progress p
        JOIN questions q ON q.id = p.question_id
        WHERE p.user_name = ?
        ORDER BY q.topic ASC, p.updated_at DESC;
        """,
        (user_name,),
    )

    by_topic = {}
    for row in cur.fetchall():
        topic = row["topic"] or "Untitled"
        if topic not in by_topic:
            by_topic[topic] = {
                "correct": [],
                "wrong": [],
                "unanswered": [],
            }
        status = row["status"]
        if status not in by_topic[topic]:
            status_key = "unanswered"
        else:
            status_key = status

        by_topic[topic][status_key].append(
            {
                "id": row["question_id"],
                "question": row["question_text"],
                "answer": row["answer_text"],
                "status": row["status"],
                "updated_at": row["updated_at"],
            }
        )

    conn.close()

    return render_template(
        "stats.html",
        user_name=user_name,
        overall=overall,
        topic_rows=topic_rows,
        by_topic=by_topic,
    )


@app.route("/user/<user_name>/")
def user_home(user_name):
    """
    User landing page:
      - shows per-topic progress
      - buttons to study all / missed
      - links to stats & resets
    """
    user_name = normalize_user_name(user_name)
    conn = get_db()

    # Overall summary (reuse stats logic)
    cur = conn.execute(
        """
        SELECT
            SUM(CASE WHEN status = 'correct' THEN 1 ELSE 0 END) AS correct_count,
            SUM(CASE WHEN status = 'wrong' THEN 1 ELSE 0 END) AS wrong_count,
            COUNT(*) AS total_count
        FROM progress
        WHERE user_name = ?;
        """,
        (user_name,),
    )
    overall_row = cur.fetchone()
    if not overall_row or overall_row["total_count"] is None:
        overall = None
    else:
        total = overall_row["total_count"]
        correct = overall_row["correct_count"] or 0
        wrong = overall_row["wrong_count"] or 0
        completion = (correct / total * 100.0) if total else 0.0
        overall = {
            "total": total,
            "correct": correct,
            "wrong": wrong,
            "completion": completion,
        }

    # Per-topic breakdown
    cur = conn.execute(
        """
        SELECT
            q.topic AS topic,
            SUM(CASE WHEN p.status = 'correct' THEN 1 ELSE 0 END) AS correct_count,
            SUM(CASE WHEN p.status = 'wrong' THEN 1 ELSE 0 END) AS wrong_count,
            COUNT(*) AS total_count
        FROM progress p
        JOIN questions q ON q.id = p.question_id
        WHERE p.user_name = ?
        GROUP BY q.topic
        ORDER BY q.topic;
        """,
        (user_name,),
    )
    topic_rows = [
        {
            "topic": row["topic"],
            "correct": row["correct_count"] or 0,
            "wrong": row["wrong_count"] or 0,
            "total": row["total_count"] or 0,
        }
        for row in cur.fetchall()
    ]

    conn.close()

    return render_template(
        "user_home.html",
        user_name=user_name,
        overall=overall,
        topic_rows=topic_rows,
    )


@app.route("/reset_progress/<user_name>/", methods=["POST"])
def reset_progress_user(user_name):
    """
    Reset ALL progress for this user across all topics.
    """
    user_name = normalize_user_name(user_name)
    conn = get_db()
    conn.execute("DELETE FROM progress WHERE user_name = ?;", (user_name,))
    conn.commit()
    conn.close()
    return redirect(url_for("user_home", user_name=user_name))


@app.route("/reset_progress/<user_name>/<topic>/", methods=["POST"])
def reset_topic_progress(user_name, topic):
    """
    Reset progress for this user in a single topic.
    """
    user_name = normalize_user_name(user_name)
    conn = get_db()
    conn.execute(
        """
        DELETE FROM progress
        WHERE user_name = ?
          AND question_id IN (SELECT id FROM questions WHERE topic = ?);
        """,
        (user_name, topic),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("user_home", user_name=user_name))


# -------------------------
# Progress update endpoint
# -------------------------


@app.route("/update_progress/", methods=["POST"])
def update_progress():
    """
    Upsert progress row for a question.
    """
    data = request.get_json(force=True) or {}
    user_name = normalize_user_name(data.get("user_name"))
    question_id = data.get("question_id")
    status = data.get("status")

    if not (user_name and question_id and status):
        return jsonify({"success": False, "error": "Missing fields"}), 400

    if status not in ("correct", "wrong", "unanswered"):
        return jsonify({"success": False, "error": "Invalid status"}), 400

    conn = get_db()
    conn.execute(
        """
        INSERT INTO progress (user_name, question_id, status, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_name, question_id)
        DO UPDATE SET
            status = excluded.status,
            updated_at = CURRENT_TIMESTAMP;
        """,
        (user_name, question_id, status),
    )
    conn.commit()
    conn.close()

    return jsonify({"success": True, "status": status})


# -------------------------
# JSON API endpoints
# (equivalents of your DRF views)
# -------------------------


@app.route("/api/questions/", methods=["GET"])
def api_get_questions():
    """
    GET all questions (like your Django get_questions).
    """
    conn = get_db()
    cur = conn.execute("SELECT id, question, answer, likelihood FROM questions;")
    results = [
        {
            "id": row["id"],
            "question": row["question"],
            "answer": row["answer"],
            "likelihood": row["likelihood"],
        }
        for row in cur.fetchall()
    ]
    conn.close()
    return jsonify(results)


@app.route("/api/check_answer/<int:qid>/", methods=["POST"])
def api_check_answer(qid):
    """
    Check answer against DB.
    """
    data = request.get_json(force=True) or {}
    user_answer = (data.get("answer") or "").strip().lower()

    conn = get_db()
    cur = conn.execute("SELECT answer FROM questions WHERE id = ?;", (qid,))
    row = cur.fetchone()
    conn.close()

    if row is None:
        return jsonify({"correct": False, "message": "Invalid question"}), 404

    correct_answer = (row["answer"] or "").strip().lower()
    correct = user_answer == correct_answer
    return jsonify({"correct": correct})


@app.route("/api/topics/", methods=["GET"])
def api_get_topics():
    """
    List unique topics.
    """
    conn = get_db()
    cur = conn.execute("SELECT DISTINCT topic FROM questions WHERE topic IS NOT NULL;")
    topics = sorted(row["topic"] for row in cur.fetchall())
    conn.close()
    return jsonify(topics)


@app.route("/api/questions/<topic_name>/", methods=["GET"])
def api_get_questions_by_topic(topic_name):
    """
    Shuffled questions for a topic.
    """
    conn = get_db()
    cur = conn.execute(
        "SELECT id, question, answer, likelihood FROM questions WHERE topic = ?;",
        (topic_name,),
    )
    rows = list(cur.fetchall())
    conn.close()

    random.shuffle(rows)

    data = [
        {
            "id": row["id"],
            "question": row["question"],
            "answer": row["answer"],
            "likelihood": row["likelihood"],
        }
        for row in rows
    ]
    return jsonify(data)


# -------------------------
# Tiny admin overview
# -------------------------


@app.route("/admin/overview/")
def admin_overview():
    """
    Simple helper page:
      - total questions
      - total topics
      - list of users with counts
    """
    conn = get_db()

    cur = conn.execute("SELECT COUNT(*) AS c FROM questions;")
    total_questions = cur.fetchone()["c"]

    cur = conn.execute("SELECT COUNT(DISTINCT topic) AS c FROM questions WHERE topic IS NOT NULL;")
    total_topics = cur.fetchone()["c"]

    cur = conn.execute(
        """
        SELECT
            user_name,
            SUM(CASE WHEN status = 'correct' THEN 1 ELSE 0 END) AS correct_count,
            SUM(CASE WHEN status = 'wrong' THEN 1 ELSE 0 END) AS wrong_count,
            COUNT(*) AS total_count
        FROM progress
        GROUP BY user_name
        ORDER BY user_name;
        """
    )
    user_rows = [
        {
            "user_name": row["user_name"],
            "correct": row["correct_count"] or 0,
            "wrong": row["wrong_count"] or 0,
            "total": row["total_count"] or 0,
        }
        for row in cur.fetchall()
    ]

    conn.close()

    return render_template(
        "admin_overview.html",
        total_questions=total_questions,
        total_topics=total_topics,
        user_rows=user_rows,
    )


# -------------------------
# Entry point
# -------------------------

if __name__ == "__main__":
    init_db()
    app.run(debug=os.environ["ENV"] == "dev")
