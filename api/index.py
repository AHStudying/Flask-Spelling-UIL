from flask import Flask, render_template, request, redirect, url_for, send_file
import random
from gtts import gTTS
import os
import tempfile
import io
import time  # Import the time module

app = Flask(__name__)

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Load word list
def load_word_list(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return [line.strip() for line in file]

word_list = load_word_list("words.txt")

current_word_idx = 0
main_contest_words = []
wrong_words = []

# Select words for the contest
def select_words(start_index, end_index, num_words=70):
    if 1 <= start_index <= end_index <= len(word_list):
        selected_words = word_list[start_index - 1:end_index]
        random.shuffle(selected_words)
        return selected_words[:num_words]
    else:
        return []

# Generate and play word pronunciation
def generate_and_play_word(word):
    tts = gTTS(text=word, lang='en')
    current_time = int(time.time())
    temp_file = tempfile.NamedTemporaryFile(suffix=f"_{word}_{current_time}.mp3", delete=False)
    temp_file.close()
    tts.save(temp_file.name)

    audio_data = open(temp_file.name, 'rb').read()

    try:
        os.remove(temp_file.name)
    except PermissionError:
        pass

    return audio_data

# Check user input against the correct word
def check_word(user_input):
    global current_word_idx, main_contest_words

    if current_word_idx < len(main_contest_words):
        if user_input == main_contest_words[current_word_idx]:
            return True
        else:
            feedback = f"Incorrect. Correct answer: '{main_contest_words[current_word_idx]}'"
            return feedback
    return False

# Route for the home page
@app.route("/", methods=["GET", "POST"])
def index():
    global current_word_idx, main_contest_words, wrong_words

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

# Inside the /contest route
@app.route("/contest", methods=["GET", "POST"])
def contest():
    global current_word_idx, main_contest_words, wrong_words

    if request.method == "POST":
        user_input = request.form["user_input"]
        feedback = check_word(user_input)

        if feedback == True:
            # User spelled the word correctly, generate new audio for the next word
            current_word_idx += 1

            if current_word_idx < len(main_contest_words):
                # Generate and play the pronunciation for the next word
                audio_data = generate_and_play_word(main_contest_words[current_word_idx])

                # Add a timestamp to the URL to prevent caching
                timestamp = int(time.time())
                audio_url = f"/pronounce?timestamp={timestamp}"

                return render_template("contest.html", current_word_idx=current_word_idx, total_words=len(main_contest_words), feedback=feedback, audio_data=audio_data, audio_url=audio_url)

        else:
            wrong_words.append((main_contest_words[current_word_idx], user_input))

        if current_word_idx < len(main_contest_words):
            # Generate and play the pronunciation for the next word
            audio_data = generate_and_play_word(main_contest_words[current_word_idx])

            # Add a timestamp to the URL to prevent caching
            timestamp = int(time.time())
            audio_url = f"/pronounce?timestamp={timestamp}"

            return render_template("contest.html", current_word_idx=current_word_idx, total_words=len(main_contest_words), feedback=feedback, audio_data=audio_data, audio_url=audio_url)
        else:
            return redirect(url_for("index"))

    if current_word_idx < len(main_contest_words):
        # Generate and play the pronunciation for the current word
        audio_data = generate_and_play_word(main_contest_words[current_word_idx])

        # Add a timestamp to the URL to prevent caching
        timestamp = int(time.time())
        audio_url = f"/pronounce?timestamp={timestamp}"

        return render_template("contest.html", current_word_idx=current_word_idx, total_words=len(main_contest_words), feedback=None, audio_data=audio_data, audio_url=audio_url)
    else:
        return redirect(url_for("index"))

@app.route("/pronounce")
def pronounce_word():
    global current_word_idx, main_contest_words

    if current_word_idx < len(main_contest_words):
        word = main_contest_words[current_word_idx]
        audio_data = generate_and_play_word(word)
        timestamp = int(time.time())
        return send_file(io.BytesIO(audio_data), mimetype='audio/mpeg', as_attachment=True, download_name=f'pronunciation_{timestamp}.mp3')
    else:
        return send_file(io.BytesIO(b""), mimetype='audio/mpeg', as_attachment=True, download_name='pronunciation_placeholder.mp3')

if __name__ == "__main__":
    app.run(debug=True) 
