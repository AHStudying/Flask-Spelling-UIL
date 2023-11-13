from flask import Flask, render_template, request, redirect, url_for, send_file
import random
from gtts import gTTS
import os
import tempfile
import io

app = Flask(__name__)

def load_word_list(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return [line.strip() for line in file]

word_list = load_word_list("words.txt")

current_word_idx = 0
main_contest_words = []
wrong_words = []
temp_file_name = None

def select_words(start_index, end_index, num_words=70):
    if 1 <= start_index <= end_index <= len(word_list):
        selected_words = word_list[start_index - 1:end_index]
        random.shuffle(selected_words)
        return selected_words[:num_words]
    else:
        return []

def generate_and_play_word(word):
    global temp_file_name
    if temp_file_name:
        try:
            os.remove(temp_file_name)
        except PermissionError:
            pass

    tts = gTTS(text=word, lang='en')
    temp_file_name = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
    tts.save(temp_file_name)

    # Read the mp3 file into a bytes object
    audio_data = open(temp_file_name, 'rb').read()

    return audio_data

def check_word(user_input):
    global current_word_idx, main_contest_words

    if current_word_idx < len(main_contest_words):
        if user_input == main_contest_words[current_word_idx]:
            return True
        else:
            feedback = f"Incorrect. Correct answer: '{main_contest_words[current_word_idx]}'"
            return feedback
    return False

@app.route("/", methods=["GET", "POST"])
def index():
    global current_word_idx, main_contest_words, wrong_words, temp_file_name

    if request.method == "POST":
        start_index = int(request.form["start_index"])
        end_index = int(request.form["end_index"])
        main_contest_words = select_words(start_index, end_index, num_words=70)
        current_word_idx = 0
        wrong_words = []

        # Generate and play the pronunciation for the first word
        audio_data = generate_and_play_word(main_contest_words[current_word_idx])
        return render_template("contest.html", current_word_idx=current_word_idx, total_words=len(main_contest_words), feedback=None, audio_data=audio_data)

    return render_template("index.html")

@app.route("/contest", methods=["GET", "POST"])
def contest():
    global current_word_idx, main_contest_words, wrong_words, temp_file_name

    if request.method == "POST":
        user_input = request.form["user_input"]
        feedback = check_word(user_input)

        if feedback == True:
            current_word_idx += 1
            # Generate and play the pronunciation for the next word
            audio_data = generate_and_play_word(main_contest_words[current_word_idx])
            return render_template("contest.html", current_word_idx=current_word_idx, total_words=len(main_contest_words), feedback=feedback, audio_data=audio_data)
        else:
            wrong_words.append((main_contest_words[current_word_idx], user_input))

    if current_word_idx < len(main_contest_words):
        # Generate and play the pronunciation for the current word
        audio_data = generate_and_play_word(main_contest_words[current_word_idx])
        return render_template("contest.html", current_word_idx=current_word_idx, total_words=len(main_contest_words), feedback=None, audio_data=audio_data)
    else:
        return redirect(url_for("index"))

@app.route("/pronounce")
def pronounce_word():
    global current_word_idx, main_contest_words, temp_file_name
    audio_data = open(temp_file_name, 'rb').read()
    return send_file(io.BytesIO(audio_data), mimetype='audio/mpeg', as_attachment=True, download_name='pronunciation.mp3')

if __name__ == "__main__":
    app.run()
