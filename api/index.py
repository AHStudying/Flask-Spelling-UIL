from flask import Flask, render_template, request, redirect, url_for, send_file
import random
from gtts import gTTS
import os
import tempfile
import pyttsx3
import threading
from pydub import AudioSegment

app = Flask(__name__)

def load_word_list(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return [line.strip() for line in file]

word_list = load_word_list("words.txt")

current_word_idx = 0
wrong_words = []

def select_words(start_index, end_index, num_words=70):
    if 1 <= start_index <= end_index <= len(word_list):
        selected_words = word_list[start_index - 1:end_index]
        random.shuffle(selected_words)
        return selected_words[:num_words]
    else:
        return []

# Generate both standard and alternate pronunciation files
def generate_pronunciation_files(word):
    standard_tts = gTTS(text=word, lang='en')
    alt_tts = gTTS(text=word, lang='en', slow=True)

    standard_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    alt_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)

    standard_tts.save(standard_file.name)
    alt_tts.save(alt_file.name)

    return standard_file.name, alt_file.name

def check_word(user_input):
    if current_word_idx < len(main_contest_words):
        if user_input == main_contest_words[current_word_idx]:
            return True
        else:
            feedback = f"Incorrect. Correct answer: '{main_contest_words[current_word_idx]}'"
            return feedback
    return False

@app.route("/", methods=["GET", "POST"])
def index():
    global current_word_idx, main_contest_words, wrong_words

    if request.method == "POST":
        start_index = int(request.form["start_index"])
        end_index = int(request.form["end_index"])
        main_contest_words = select_words(start_index, end_index, num_words=70)
        current_word_idx = 0
        wrong_words = []

        # Generate pronunciation files for the selected word
        standard_pronunciation_file, alt_pronunciation_file = generate_pronunciation_files(main_contest_words[current_word_idx])

        return redirect(url_for("contest"))

    return render_template("index.html")

@app.route("/contest", methods=["GET", "POST"])
def contest():
    global current_word_idx

    if request.method == "POST":
        user_input = request.form["user_input"]
        feedback = check_word(user_input)

        if feedback == True:
            wrong_words.clear()
            current_word_idx += 1

            # Generate pronunciation files for the new word
            standard_pronunciation_file, alt_pronunciation_file = generate_pronunciation_files(main_contest_words[current_word_idx])

        else:
            wrong_words.append((main_contest_words[current_word_idx], user_input))

        if current_word_idx < len(main_contest_words):
            pronounced = False
            return render_template("contest.html", current_word_idx=current_word_idx, total_words=len(main_contest_words), feedback=feedback)
        else:
            return redirect(url_for("index"))

    if current_word_idx < len(main_contest_words):
        return render_template("contest.html", current_word_idx=current_word_idx, total_words=len(main_contest_words), feedback=None)
    else:
        return redirect(url_for("index"))

@app.route("/pronounce_standard")
def pronounce_standard():
    # Return the standard pronunciation file
    return send_file(standard_pronunciation_file, mimetype='audio/mpeg', as_attachment=True)

@app.route("/pronounce_alternate")
def pronounce_alternate():
    # Return the alternate pronunciation file
    return send_file(alt_pronunciation_file, mimetype='audio/mpeg', as_attachment=True)

@app.route("/alt_pronunciation")
def alt_pronunciation():
    # You can implement alt pronunciation logic if needed
    pass
