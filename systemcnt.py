import speech_recognition as sr
import pyttsx3

class SpeechHandler:
    """
    Handles speech recognition and text-to-speech.
    """

    def __init__(self):
        self.listener = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 160)  # speed of speech
        self.engine.setProperty("volume", 0.9)
        self.name = "Taskar"   # Assistant's name

    def listen(self):
        """Convert user speech into text"""
        try:
            with sr.Microphone() as source:
                print(f"{self.name} is listening...")
                voice = self.listener.listen(source, timeout=5, phrase_time_limit=8)
                command = self.listener.recognize_google(voice).lower()
                print(f"User said: {command}")
                return command
        except Exception:
            print(f"{self.name} could not understand audio")
            return None

    def speak(self, text):
        """Convert text to speech"""
        print(f"{self.name}: {text}")
        self.engine.say(text)
        self.engine.runAndWait()
