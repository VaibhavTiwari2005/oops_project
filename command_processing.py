import datetime
import wikipedia
import system_controller

class CommandProcessor:
    """
    Processes user queries and decides what action to take.
    """

    def __init__(self):
        self.system = system_controller.SystemController()

    def handle_command(self, query):
        query = query.lower().strip()

        if "time" in query:
            return f"The current time is {datetime.datetime.now().strftime('%H:%M')}"

        elif "date" in query:
            return f"Today's date is {datetime.datetime.now().strftime('%d %B %Y')}"

        elif "wikipedia" in query:
            try:
                topic = query.replace("wikipedia", "").strip()
                info = wikipedia.summary(topic, sentences=2)
                return f"According to Wikipedia: {info}"
            except Exception as e:
                return f"Sorry, I couldn't fetch that information. ({str(e)})"

        elif "open" in query:
            app_name = query.replace("open", "").strip()
            return self.system.open_application(app_name)

        else:
            return "Sorry, I don't know that yet."
