import sys
import requests
import pyautogui
import os
import numpy as np
import keyboard
import json
import time
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
import tempfile
import elevenlabs as streaming 
from datetime import datetime
import textwrap
import webbrowser
import urllib.parse
from threading import Thread
import io

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QTextEdit, QLineEdit, QVBoxLayout, QWidget, QSizePolicy, QPushButton
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPainterPath, QRegion
from PyQt5.QtCore import Qt, QRectF

import openai

openai.api_key = "PLACE_OPEN_AI_API_HERE"

def generate_text(prompt, chat_history=None):
    if chat_history is None:
        chat_history = []

    chat_history.append({"role": "user", "content": prompt})

    messages = [
        {"role": "system", "content": "You are Amelia. Be affirmative and intelligent, Respond to User always be interesting and in character but never use more than 3 words.(If input from user is a direct instruction not a question, always respond with 'Job done' only.)"},
        *chat_history
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    generated_text = response.choices[-1].message.content

    chat_history.append({"role": "assistant", "content": generated_text})

    return generated_text

def generate_text_unrestricted(prompt, chat_history=None, max_line_width=45):
    if chat_history is None:
        chat_history = []

    chat_history.append({"role": "user", "content": prompt})

    messages = [
        {"role": "system", "content": "You are Amelia. Be an affirmative and intelligent story writer, Try not to generate unecessarily long content"},
        *chat_history
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=messages
    )

    generated_text = response.choices[-1].message.content

    # Wrap text at the specified maximum line width
    generated_text = "\n".join(textwrap.wrap(generated_text, width=max_line_width))

    chat_history.append({"role": "assistant", "content": generated_text})

    return generated_text

def record_speech(duration, sample_rate=16000):
    print("Recording...")
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
    sd.wait()
    return recording

def save_wav(audio_data, filename, sample_rate):
    sf.write(filename, audio_data, sample_rate)

def speech_to_text(audiofile):
    rec = sr.Recognizer()
    with sr.AudioFile(audiofile) as source:
        audio = rec.record(source)

    try:
        text = rec.recognize_google(audio)
    except sr.UnknownValueError:
        text = ""
    return text

def generate_audio(text, streaming=True):
    url = "https://api.elevenlabs.io/v1/text-to-speech/PLACE_YOUR_VOICE_ID_HERE"

    headers = {
        "accept": "audio/mpeg;charset=UTF-8",
        "xi-api-key": "PLACE_YOUR_ELEVENLABS_API_HERE",
        "Content-Type": "application/json"
    }
    params = {"optimize_streaming_latency": 1 }

    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.48,
            "similarity_boost": 0.88,
            "voice_id": "PLACE_YOUR_VOICE_ID_HERE"
        }
    }

    response = requests.post(url, headers=headers, params=params, data=json.dumps(data))

    if response.status_code == 200:
        return response.content
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def play(audio):
    with io.BytesIO(audio) as audio_file:
        with sf.SoundFile(audio_file, 'rb') as file:
            channels = file.channels
            samplerate = file.samplerate
            audio_data = file.read(dtype='float32')
            sd.play(audio_data, samplerate)
            sd.wait()

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle('Cyberpunk Chat')
        self.setWindowIcon(QIcon('path/to/your/icon.png'))
        self.setGeometry(100, 20, 400, 500)

        user_primary_start_color = "#3f0e3e"
        user_primary_end_color = "#93278f"
        user_secondary_start_color = "#202128"
        user_secondary_end_color = "#202128"
        user_text_color = "#FFFFFF"
        user_background_color = "#000000"
        user_glow_color = "#93278f"

        self.setStyleSheet("background-color: rgba(0, 0, 0, 245);")

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 0, 10, 10)
        layout.setSpacing(5)

        # Set rounded border
        path = QPainterPath()
        corner_radius = 10
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        path.addRoundedRect(rect, corner_radius, corner_radius)
        mask_region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(mask_region)

        self.title_label = QLabel('Amelia', central_widget)
        self.title_label.setStyleSheet('color: %s; font-size: 48px; font-weight: bold; padding: 5px; background-color: transparent;' % (user_text_color))
        font = QFont("Times New Roman", 48, QFont.Bold)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label, alignment=Qt.AlignTop | Qt.AlignHCenter)

        self.conversation_text = QTextEdit()
        self.conversation_text.setStyleSheet('background-color: %s; color: %s; font-size: 20px; border-radius: 5px; padding: 10px;' % (user_secondary_start_color, user_text_color))
        self.conversation_text.setFont(QFont('Roboto', 12))
        layout.addWidget(self.conversation_text, 1)

        layout.addSpacing(4)

        self.input_text = QLineEdit()
        self.input_text.setPlaceholderText('Send a message')  # Add this line to set the placeholder text
        self.input_text.setStyleSheet('background-color: %s; color: %s; font-size: 20px; border-radius: 5px; padding: 10px;' % (user_secondary_start_color, user_text_color))
        self.input_text.setFont(QFont('Roboto', 14))
        layout.addWidget(self.input_text)

        self.conversation_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.conversation_text.setMinimumHeight(int(self.height() * 0.7))

        self.setWindowOpacity(0.98)
        layout.addWidget(self.input_text)

        self.input_text.returnPressed.connect(self.send_text)

    def send_text(self):
        user_input = self.input_text.text().strip()
        self.input_text.clear()

        if user_input:
            self.conversation_text.append(f"<b>User:</b> {user_input}")
            self.conversation_text.repaint()

            perform_action(self, user_input)

            generated_text = generate_text(user_input)

            audio = generate_audio(generated_text, streaming=True)
            play(audio)

            self.conversation_text.append(f"<b>Assistant:</b> {generated_text}")
            self.conversation_text.repaint()

def perform_action(window, text):
    text_lower = text.lower()

    if "open browser" in text_lower:
        webbrowser.open("https://www.phind.com/")
    if "open youtube" in text_lower:
        webbrowser.open("https://www.youtube.com/")
    if "open google" in text_lower:
        webbrowser.open("https://www.google.com/")
    if "open twitter" in text_lower:
        webbrowser.open("https://twitter.com/twitter")
    if "open Chat-GPT" in text_lower:
        webbrowser.open("https://chat.openai.com/")
    if "search" in text_lower:
        query = text_lower.replace("search", "").strip()
        query_encoded = urllib.parse.quote_plus(query)
        webbrowser.open(f"https://www.phind.com/search?q={query_encoded}&source=searchbox")
    if "google" in text_lower:
        query = text_lower.replace("google", "").strip()
        query_encoded = urllib.parse.quote_plus(query)
        webbrowser.open(f"https://www.google.com/search?q={query_encoded}")
    if "open text file and write" in text_lower:
        # Extract the user_text_to_write
        user_text_to_write = text_lower.replace("open text file and write", "").strip()

        # Generate text using Chat GPT based on the user's command without word restriction
        generated_text_content = generate_text_unrestricted(user_text_to_write)

        # Create a unique filename using the current timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"text_file_{timestamp}.txt"

        # Open the text editor
        subprocess.call(['open', '-a', 'TextEdit'])
        time.sleep(1)  # Wait for the text editor to open

        # Type the generated text content into the text file
        subprocess.call(['osascript', '-e', f'tell application "System Events" to keystroke "{generated_text_content}"'])

        # Save the typed text to a new file
        # Adjust the path and filename as per your requirement
        subprocess.call(['osascript', '-e', f'tell application "TextEdit" to save document 1 in "<file_path>/<file_name>"'])

        print(f"Text file '{file_name}' created and text written: '{generated_text_content}'")


    
def speech_to_text_and_synthesis():
    while True:
        try:
            # Record speech for 5 seconds
            record_duration = 5
            sample_rate = 16000
            audio_data = record_speech(record_duration, sample_rate)
            audiofile = "speech_recording.wav"
            save_wav(audio_data, audiofile, sample_rate)

            # Calculate the maximum amplitude
            max_amplitude = np.max(np.abs(audio_data))

            # If the max amplitude is below a threshold, skip further processing
            amplitude_threshold = 0.01  # Adjust this value based on your desired sensitivity
            if max_amplitude < amplitude_threshold:
                print("Low amplitude sound, skipping text generation and synthesis")
                continue

            # Convert recorded speech to text
            input_text = speech_to_text(audiofile)
            print("Input Text: ", input_text)

            # If the input_text is empty, skip further processing
            if not input_text.strip():
                print("No text detected, skipping text generation and synthesis")
                continue

            # Generate new text using OpenAI API
            generated_text = generate_text(input_text)

            print("Generated_text: ", generated_text)

            # Synthesize the generated text using Eleven Labs API
            audio = generate_audio(generated_text, streaming=True)

            # Play the synthesized audio
            play(audio)

            # Add a delay of 1 second before recording speech again
            time.sleep(1)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print("An error occurred: ", str(e))
            continue

app = QApplication(sys.argv)
window = ChatWindow()
window.show()
sys.exit(app.exec_())
