import requests
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QTextEdit, QLineEdit, QSizePolicy
from PyQt5.QtGui import QIcon, QFont, QPainterPath, QRegion
from PyQt5.QtCore import Qt, QRectF
from llama_cpp import Llama
from playsound import playsound
import tempfile
import os

def generate_audio_elevenlabs(text):
    url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"
    headers = {
        "accept": "audio/mpeg",
        "xi-api-key": "X",
        "Content-Type": "application/json"
    }
    params = {"optimize_streaming_latency": 1}

    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0,
            "similarity_boost": 0
        }
    }

    response = requests.post(url, headers=headers, params=params, data=json.dumps(data))

    if response.status_code == 200:
        return response.content
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

# Specify the GPU device ID (use 0 if you only have one GPU)
gpu_device_id = 0

llm = Llama(model_path=r"D:\Games\model\mistral-7b-instruct-v0.1.Q5_K_S.gguf")

# Initialize chat history
chat_history = [
    {"role": "system", "content": "Assistant"},
    {"role": "user", "content": "hello"}
]

# Function to process user input and update chat history
def process_user_input(user_input):
    global chat_history
    # Add user input to chat history
    chat_history.append({"role": "user", "content": user_input})
    # Use the updated chat history for chat completion
    llm_response = llm.create_chat_completion(messages=chat_history)
    # Extract the system content from the llm_response
    system_content = llm_response["choices"][0]["message"]["content"]
    # Add system response to chat history
    chat_history.append({"role": "system", "content": system_content})
    # Return system content for further processing
    return system_content

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle('Amelia')
        self.setWindowIcon(QIcon('path/to/your/icon.png'))
        self.setGeometry(100, 20, 400, 500)

        # Your color and style settings
        user_text_color = "#FFFFFF"
        user_secondary_start_color = "#202128"

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
        self.input_text.setPlaceholderText('Send a message')  
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

        # Process user input and get the system content
        system_content = process_user_input(user_input)

        # Call the generate_audio_elevenlabs function to get the audio content for the system output
        audio_content = generate_audio_elevenlabs(system_content)

        # Save the audio content to a temporary file
        temp_file_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
        with open(temp_file_path, "wb") as f:
            f.write(audio_content)

        # Play the resulting audio file for the Llama model output
        playsound(temp_file_path)

        # Remove the temporary file after playing
        os.remove(temp_file_path)

        self.conversation_text.append(f"<b>Assistant:</b> {system_content}")
        self.conversation_text.repaint()

if __name__ == "__main__":
    app = QApplication([])
    window = ChatWindow()
    window.show()
    app.exec_()
