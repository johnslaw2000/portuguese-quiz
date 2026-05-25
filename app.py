import os
import random
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]

db = SQLAlchemy(app)


class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    english = db.Column(db.String(100), nullable=False)
    portuguese = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)


class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player = db.Column(db.String(50), nullable=False)
    correct = db.Column(db.Integer, nullable=False, default=0)
    total = db.Column(db.Integer, nullable=False, default=0)


@app.route("/")
def home():
    scores = Score.query.order_by(Score.correct.desc()).all()
    return render_template("home.html", scores=scores)


@app.route("/words")
def words():
    all_words = Word.query.all()
    return render_template("words.html", words=all_words)


@app.route("/add-word", methods=["GET", "POST"])
def add_word():
    if request.method == "POST":
        word = Word(
            english=request.form["english"],
            portuguese=request.form["portuguese"],
            category=request.form["category"],
        )
        db.session.add(word)
        db.session.commit()
        return redirect(url_for("words"))
    return render_template("word_form.html", word=None)


@app.route("/edit-word/<int:id>", methods=["GET", "POST"])
def edit_word(id):
    word = Word.query.get_or_404(id)
    if request.method == "POST":
        word.english = request.form["english"]
        word.portuguese = request.form["portuguese"]
        word.category = request.form["category"]
        db.session.commit()
        return redirect(url_for("words"))
    return render_template("word_form.html", word=word)


@app.route("/delete-word/<int:id>")
def delete_word(id):
    word = Word.query.get_or_404(id)
    db.session.delete(word)
    db.session.commit()
    return redirect(url_for("words"))


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    all_words = Word.query.all()
    if len(all_words) < 4:
        return render_template("quiz.html", error="Add at least 4 words to start the quiz!")

    if request.method == "POST":
        correct_id = int(request.form["correct_id"])
        chosen = request.form["chosen"]
        correct_word = Word.query.get(correct_id)
        is_correct = chosen == correct_word.portuguese

        if "correct" not in session:
            session["correct"] = 0
            session["total"] = 0

        session["total"] += 1
        if is_correct:
            session["correct"] += 1

        return render_template(
            "result.html",
            is_correct=is_correct,
            correct_word=correct_word,
            chosen=chosen,
            correct=session["correct"],
            total=session["total"],
        )

    correct_word = random.choice(all_words)
    wrong_words = random.sample(
        [w for w in all_words if w.id != correct_word.id], 3
    )
    options = [correct_word.portuguese] + [w.portuguese for w in wrong_words]
    random.shuffle(options)

    return render_template(
        "quiz.html",
        correct_word=correct_word,
        options=options,
        error=None,
    )


@app.route("/save-score", methods=["POST"])
def save_score():
    player = request.form["player"]
    correct = int(request.form["correct"])
    total = int(request.form["total"])
    score = Score(player=player, correct=correct, total=total)
    db.session.add(score)
    db.session.commit()
    session.clear()
    return redirect(url_for("home"))


with app.app_context():
    try:
        db.create_all()
    except Exception:
        pass


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
