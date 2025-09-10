import speech_handler
import command_processor

class VoiceAssistant:
    """
    Main class for coordinating the virtual assistant.
    It connects speech input, command processing, and execution.
    """

    def __init__(self, name="Taskar"):
        self.name = name
        self.speech = speech_handler.SpeechHandler()
        self.processor = command_processor.CommandProcessor()

    def greet_user(self):
        self.speech.speak(f"Hello! I am {self.name}. How can I help you today?")

    def run(self):
        """Main loop of the assistant"""
        self.greet_user()
        while True:
            query = self.speech.listen()
            if query:
                if "exit" in query or "quit" in query:
                    self.speech.speak("Goodbye! Have a nice day.")
                    break
                response = self.processor.handle_command(query)
                if response:
                    self.speech.speak(response)
