from flask import Flask, render_template, request, redirect, url_for, send_file
import random
from gtts import gTTS
import os
import tempfile
import io
import time

app = Flask(__name__)

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Load word list
def load_word_list(filename):
    directory_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(directory_path, filename)
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return [line.strip() for line in file]
    except FileNotFoundError:
        print(f"File '{filename}' not found in '{directory_path}'.")
        return []
    except IOError as e:
        print(f"Error reading file '{filename}': {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

current_word_idx = 0
main_contest_words = []
wrong_words = []

# Select words for the contest
def select_words(word_list, start_index, end_index, num_words=70):
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
        correct_words = [word.strip() for word in main_contest_words[current_word_idx].split(",")]
        
        user_inputs = [input.strip() for input in user_input.split(",")]

        if all(input in correct_words for input in user_inputs):
            return True
        else:
            feedback = f"Incorrect. Correct answer: '{', '.join(correct_words)}'"
            return feedback
    return False

# Route for the home page
@app.route("/", methods=["GET", "POST"])
def index():
    global current_word_idx, main_contest_words, wrong_words

    file_names = ["2024.txt", "2023.txt", "2022.txt", "2021.txt", "2020.txt", "2019.txt"]

    if request.method == "POST":
        filename = request.form["filename"]
        start_index = int(request.form["start_index"])
        end_index = int(request.form["end_index"])
        word_list = load_word_list(filename)

        if not word_list:
            return render_template("index.html", file_names=file_names, error_message=f"Failed to load word list from '{filename}'.")

        main_contest_words = select_words(word_list, start_index, end_index, num_words=70)
        
        if not main_contest_words:
            return render_template("index.html", file_names=file_names, error_message=f"Failed to select words from '{filename}'. Please check your indices.")

        current_word_idx = 0
        wrong_words = []

        audio_data = generate_and_play_word(main_contest_words[current_word_idx])
        return render_template("contest.html", current_word_idx=current_word_idx, total_words=len(main_contest_words), feedback=None, audio_data=audio_data, file_names=file_names)

    return render_template("index.html", file_names=file_names)

# Inside the /contest route
@app.route("/contest", methods=["GET", "POST"])
def contest():
    global current_word_idx, main_contest_words, wrong_words

    if request.method == "POST":
        user_input = request.form["user_input"]
        feedback = check_word(user_input)

        if feedback == True:
            current_word_idx += 1

            if current_word_idx < len(main_contest_words):
                audio_data = generate_and_play_word(main_contest_words[current_word_idx])
                timestamp = int(time.time())
                audio_url = f"/pronounce?timestamp={timestamp}"

                return render_template("contest.html", current_word_idx=current_word_idx, total_words=len(main_contest_words), feedback=feedback, audio_data=audio_data, audio_url=audio_url)

        else:
            wrong_words.append((main_contest_words[current_word_idx], user_input))

        if current_word_idx < len(main_contest_words):
            audio_data = generate_and_play_word(main_contest_words[current_word_idx])
            timestamp = int(time.time())
            audio_url = f"/pronounce?timestamp={timestamp}"

            return render_template("contest.html", current_word_idx=current_word_idx, total_words=len(main_contest_words), feedback=feedback, audio_data=audio_data, audio_url=audio_url)
        else:
            return redirect(url_for("index"))

    if current_word_idx < len(main_contest_words):
        audio_data = generate_and_play_word(main_contest_words[current_word_idx])
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
        unique_id = int(time.time())
        return send_file(io.BytesIO(audio_data), mimetype='audio/mpeg', as_attachment=True, download_name=f'pronunciation_{unique_id}.mp3')
    else:
        return send_file(io.BytesIO(b""), mimetype='audio/mpeg', as_attachment=True, download_name='pronunciation_placeholder.mp3')

if __name__ == "__main__":
    app.run(debug=True)
