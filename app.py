import os
import random
import secrets
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, session, url_for


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "game_data.sqlite3"

DIFFICULTIES = {
    "easy": {"name": "かんたん", "max_number": 50, "max_attempts": 10},
    "normal": {"name": "ふつう", "max_number": 100, "max_attempts": 7},
    "hard": {"name": "むずかしい", "max_number": 500, "max_attempts": 9},
}

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)


@contextmanager
def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database():
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS games (
                id TEXT PRIMARY KEY,
                difficulty TEXT NOT NULL,
                answer INTEGER NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                max_attempts INTEGER NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                won INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS statistics (
                difficulty TEXT PRIMARY KEY,
                games_played INTEGER NOT NULL DEFAULT 0,
                best_attempts INTEGER
            );
            """
        )
        connection.executemany(
            "INSERT OR IGNORE INTO statistics (difficulty) VALUES (?)",
            [(difficulty,) for difficulty in DIFFICULTIES],
        )


def get_statistics():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT difficulty, games_played, best_attempts FROM statistics"
        ).fetchall()
    return {row["difficulty"]: row for row in rows}


def finish_game(game_id, won, attempts):
    with get_connection() as connection:
        connection.execute(
            "UPDATE games SET completed = 1, won = ? WHERE id = ?",
            (int(won), game_id),
        )
        connection.execute(
            """
            UPDATE statistics
            SET games_played = games_played + 1,
                best_attempts = CASE
                    WHEN ? = 1 AND (best_attempts IS NULL OR ? < best_attempts)
                    THEN ?
                    ELSE best_attempts
                END
            WHERE difficulty = (
                SELECT difficulty FROM games WHERE id = ?
            )
            """,
            (int(won), attempts, attempts, game_id),
        )


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "start":
            difficulty = request.form.get("difficulty", "")
            if difficulty not in DIFFICULTIES:
                flash("難易度を選んでください。", "error")
                return redirect(url_for("index"))

            settings = DIFFICULTIES[difficulty]
            game_id = session.get("game_id") or uuid.uuid4().hex
            with get_connection() as connection:
                connection.execute(
                    """
                    INSERT OR REPLACE INTO games
                        (id, difficulty, answer, attempts, max_attempts, completed, won)
                    VALUES (?, ?, ?, 0, ?, 0, 0)
                    """,
                    (
                        game_id,
                        difficulty,
                        random.randint(1, settings["max_number"]),
                        settings["max_attempts"],
                    ),
                )
            session["game_id"] = game_id
            return redirect(url_for("index"))

        if action == "guess":
            game_id = session.get("game_id")
            with get_connection() as connection:
                game = connection.execute(
                    "SELECT * FROM games WHERE id = ?", (game_id,)
                ).fetchone()

            if game is None or game["completed"]:
                flash("まず新しいゲームを始めてください。", "error")
                return redirect(url_for("index"))

            guess_text = request.form.get("guess", "").strip()
            try:
                guess = int(guess_text)
            except ValueError:
                flash("数字を入力してください。", "error")
                return redirect(url_for("index"))

            settings = DIFFICULTIES[game["difficulty"]]
            if not 1 <= guess <= settings["max_number"]:
                flash(
                    f"1から{settings['max_number']}までの数字を入力してください。",
                    "error",
                )
                return redirect(url_for("index"))

            attempts = game["attempts"] + 1
            with get_connection() as connection:
                connection.execute(
                    "UPDATE games SET attempts = ? WHERE id = ?",
                    (attempts, game_id),
                )

            if guess == game["answer"]:
                finish_game(game_id, won=True, attempts=attempts)
                flash(f"正解です！{attempts}回で当たりました。", "success")
            elif attempts == game["max_attempts"]:
                finish_game(game_id, won=False, attempts=attempts)
                flash(
                    f"残念！挑戦回数の上限です。正解は{game['answer']}でした。",
                    "error",
                )
            elif guess < game["answer"]:
                flash("もっと大きい数字です。", "info")
            else:
                flash("もっと小さい数字です。", "info")

            return redirect(url_for("index"))

        flash("操作を選び直してください。", "error")
        return redirect(url_for("index"))

    game = None
    game_id = session.get("game_id")
    if game_id:
        with get_connection() as connection:
            game = connection.execute(
                "SELECT * FROM games WHERE id = ?", (game_id,)
            ).fetchone()

    return render_template(
        "index.html",
        game=game,
        difficulties=DIFFICULTIES,
        statistics=get_statistics(),
    )


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)
