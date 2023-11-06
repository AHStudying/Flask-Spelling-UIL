from flask import Flask, render_template, request, redirect, url_for
import random
from gtts import gTTS
import os
import pygame
import tempfile
import time
import pyttsx3
import threading

app = Flask(__name__)

def load_word_list(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return [line.strip() for line in file]

word_list = load_word_list("words.txt")

current_word_idx = 0
pronounced = False
wrong_words = []

pygame.mixer.init()

def select_words(start_index, end_index, num_words=70):
    if 1 <= start_index <= end_index <= len(word_list):
        selected_words = word_list[start_index - 1:end_index]
        random.shuffle(selected_words)
        return selected_words[:num_words]
    else:
        return []

def play_word(current_word):
    tts = gTTS(text=current_word, lang='en')
    temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    temp_file.close()
    tts.save(temp_file.name)
    pygame.mixer.music.load(temp_file.name)
    pygame.mixer.music.play()
    time.sleep(2)
    try:
        os.remove(temp_file.name)
    except PermissionError:
        pass

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

        return redirect(url_for("contest"))

    return render_template("index.html")

@app.route("/contest", methods=["GET", "POST"])
def contest():
    global current_word_idx, pronounced

    if request.method == "POST":
        user_input = request.form["user_input"]
        feedback = check_word(user_input)

        if feedback == True:
            wrong_words.clear()
            current_word_idx += 1
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

@app.route("/pronounce")
def pronounce_word():
    global pronounced
    if not pronounced:
        play_word(main_contest_words[current_word_idx])
    return "Pronounced"

@app.route("/alt_pronunciation")
def alt_pronunciation():
    global current_word_idx

    alt_text = main_contest_words[current_word_idx]

    def tts_thread(text):
        engine = pyttsx3.init()
        engine.setProperty("rate", 150)
        engine.setProperty("voice", "com.apple.speech.synthesis.voice.Agnes")
        engine.say(text)
        engine.runAndWait()
        engine.stop()

    threading.Thread(target=tts_thread, args=(alt_text,)).start()

    return "Alt Pronunciation"