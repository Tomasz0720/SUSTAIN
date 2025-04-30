import speech_recognition as sr
import pyttsx3
import os
import logging
from dotenv import load_dotenv
from sustain import SUSTAIN
import spacy


# Configure logging
log_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../sustain.log'))
logging.basicConfig(filename=log_file_path, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

class VoiceAssistant:
    def __init__(self):
        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        
        # Initialize text-to-speech engine
        self.engine = pyttsx3.init()
        
        # Get API key from environment variables
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logging.error("API key not found. Please set the OPENAI_API_KEY environment variable.")
            raise ValueError("API key not found. Please set the OPENAI_API_KEY environment variable.")
            
        # Initialize SUSTAIN
        self.sustain = SUSTAIN(self.api_key)
        
        # Initialize spaCy for token tracking
        self.nlp = spacy.load("en_core_web_sm")
        
        # Tracking stats
        self.total_tokens_saved = 0
        self.total_queries = 0
    
    def track_token_length(self, message):
        """Track token length using spaCy (from main.py)"""
        doc = self.nlp(message)
        return len(doc)
    
    def speak(self, text):
        """Convert text to speech"""
        print(f"SUSTAIN: {text}")
        self.engine.say(text)
        self.engine.runAndWait()
    
    def listen(self):
        """Listen for user input"""
        try:
            print("Listening...")
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                
            print("Processing...")
            user_input = self.recognizer.recognize_google(audio)
            print(f"User: {user_input}")
            return user_input
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            self.speak("Sorry, I couldn't connect to the speech recognition service.")
            return None
        except sr.UnknownValueError:
            print("Speech not recognized. Please try again.")
            self.speak("I didn't catch that. Could you please try again?")
            return None
    
    def process_query(self, query):
        """Process a user query using SUSTAIN"""
        if not query:
            return
            
        # Check for exit command
        if query.lower() in ["exit", "quit", "goodbye", "bye"]:
            self.engine.say("Goodbye!")
            return False
            
        # Check if query is a math expression
        math_result = self.sustain.answer_math(query)
        if math_result is not None:
            self.speak(f"Math result: {math_result}")
            self.total_tokens_saved += self.track_token_length(query)
            self.total_queries += 1
            print("Math optimization: 100% tokens saved")
            return True
            
        # Get response from SUSTAIN
        response, percentage_saved = self.sustain.get_response(query)
        self.speak(response)
        
        # Track token savings
        tokens_used = self.track_token_length(query)
        tokens_saved = tokens_used * (percentage_saved / 100)
        self.total_tokens_saved += tokens_saved
        self.total_queries += 1
        
        print(f"Query processed - Token savings: {percentage_saved:.2f}%")
        return True
    
    def run(self):
        """Run the voice assistant"""
        self.engine.say("Hello! I'm SUSTAIN Voice. How can I help you?")
        
        running = True
        while running:
            query = self.listen()
            if query:
                result = self.process_query(query)
                if result is False:
                    running = False
                    
        # Show statistics before exiting
        if self.total_queries > 0:
            avg_savings = self.total_tokens_saved / self.total_queries
            print(f"\nSession Statistics:")
            print(f"Queries processed: {self.total_queries}")
            print(f"Average token savings: {avg_savings:.2f}")
            print("Thank you for using SUSTAIN Voice Assistant!")

# Main function to run the voice assistant
def main():
    try:
        assistant = VoiceAssistant()
        assistant.run()
    except Exception as e:
        logging.error(f"Error in voice assistant: {str(e)}")
        print(f"Error: {str(e)}")

# Run the main function
if __name__ == "__main__":
    main()