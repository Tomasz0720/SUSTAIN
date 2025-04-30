# Import required libraries
import os
import tkinter as tk
from tkinter import scrolledtext, PhotoImage, filedialog
from dotenv import load_dotenv
from sustain import SUSTAIN
from PIL import Image, ImageTk
import platform
import datetime

# Load environment variables from .env file
load_dotenv()

class ChatApp:
    def __init__(self, root, track_token_length):
        self.track_token_length = track_token_length
        self.root = root
        self.voice_active = False
        self.root.title("SUSTAIN Chat")
        self.root.geometry("900x700")
        
        # Try to set the app icon
        try:
            base_path = os.path.dirname(os.path.abspath(__file__))
            system = platform.system()
            
            if system == "Windows":
                icon_path = os.path.join(base_path, "application", "assets", "icon_Scz_icon.ico")
                if os.path.exists(icon_path):
                    self.root.iconbitmap(icon_path)
                    import ctypes
                    myappid = u'company.sustain.chat.1.0'
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            else:
                # macOS or Linux
                icon_path = os.path.join(base_path, "application", "assets", "icon_Scz_icon.ico")
                if os.path.exists(icon_path):
                    icon = tk.PhotoImage(file=icon_path)
                    self.root.iconphoto(True, icon)
        except Exception as e:
            print("Icon load error:", e)
        
        self.message_history = []
        
        # Color scheme
        self.colors = {
            "dark_bg": "#1e1e1e",            # Dark background
            "dark_secondary": "#2d2d2d",     # Slightly lighter dark for contrast
            "light_bg": "#f5f5f5",           # Light background
            "light_secondary": "#ffffff",    # White for light mode elements
            "user_bubble": "#e9e9eb",        # iMessage gray bubbles
            "ai_bubble": "#4CAD75",          # SUSTAIN green bubbles
            "accent": "#4CAD75",             # SUSTAIN green accent
            "dark_text": "#ffffff",          # Text in dark mode
            "light_text": "#000000",         # Text in light mode
            "info_text": "#8e8e93",          # Gray for info messages
        }

        # Initialize dark mode setting
        self.is_dark_mode = True
        
        # Create main structure
        self.create_layout()
        
        # Initialize token savings
        self.total_percentage_saved = 0
        self.message_count = 0
        
        # Apply theme
        self.apply_theme(self.is_dark_mode)
        
        # Initialize the SUSTAIN API
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key not found. Please set the OPENAI_API_KEY environment variable."
            )
        self.sustain = SUSTAIN(api_key=self.api_key)
        
        # Welcome message
        self.display_settings_message(
            "Welcome to SUSTAIN Chat! Ask me: \"What is SUSTAIN?\" to learn more."
        )
    
    def create_layout(self):
        """Create the layout for the chat application"""
        # Header with logo and controls
        self.header_frame = tk.Frame(self.root)
        self.header_frame.pack(fill=tk.X, padx=20, pady=(10, 5))
        
        # Logo
        try:
            logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 
                "assets/SUSTAIN_BLACK.png"))
            if os.path.exists(logo_path):
                original_logo = Image.open(logo_path)
                max_size = (180, 60)
                original_logo.thumbnail(max_size, Image.LANCZOS)
                self.logo = ImageTk.PhotoImage(original_logo)
                self.logo_label = tk.Label(self.header_frame, image=self.logo)
                self.logo_label.pack(side=tk.LEFT)
            else:
                self.logo_label = tk.Label(self.header_frame, text="SUSTAIN")
                self.logo_label.pack(side=tk.LEFT)
        except Exception as e:
            print(f"Logo load error: {e}")
            self.logo_label = tk.Label(self.header_frame, text="SUSTAIN")
            self.logo_label.pack(side=tk.LEFT)
        
        # Right-aligned controls in header
        self.controls_frame = tk.Frame(self.header_frame)
        self.controls_frame.pack(side=tk.RIGHT)
        
        # Info button
        self.info_button = tk.Button(
            self.controls_frame,
            text="?",
            command=self.show_info,
            font=("Arial", 10, "bold"),
            width=2,
            bd=0,
            padx=10,
            pady=5
        )
        self.info_button.pack(side=tk.RIGHT, padx=5)
        
        # Theme toggle button
        self.theme_button = tk.Button(
            self.controls_frame,
            text="☀/⏾",
            command=self.toggle_mode,
            font=("Arial", 10, "bold"),
            width=2,
            bd=0,
            padx=10,
            pady=5
        )
        self.theme_button.pack(side=tk.RIGHT, padx=5)
        
        # Chat area (middle) with scrollbar
        self.chat_container = tk.Frame(self.root)
        self.chat_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Create canvas with scrollbar for the chat
        self.chat_canvas = tk.Canvas(self.chat_container)
        self.chat_scrollbar = tk.Scrollbar(
            self.chat_container, 
            orient=tk.VERTICAL, 
            command=self.chat_canvas.yview
        )
        self.chat_canvas.configure(yscrollcommand=self.chat_scrollbar.set)
        
        # Place canvas and scrollbar
        self.chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Create a frame inside the canvas to hold messages
        self.messages_frame = tk.Frame(self.chat_canvas)
        self.chat_window = self.chat_canvas.create_window(
            (0, 0), 
            window=self.messages_frame, 
            anchor=tk.NW,
            width=self.chat_canvas.winfo_width()
        )
        
        # Configure canvas scrolling behavior
        def configure_canvas(event):
            # Update the width to fill the window
            self.chat_canvas.itemconfig(
                self.chat_window,
                width=event.width
            )
            
        self.chat_canvas.bind('<Configure>', configure_canvas)
        
        # Make sure scrolling shows all content
        def on_frame_configure(event):
            self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
            
        self.messages_frame.bind('<Configure>', on_frame_configure)
        
        # Input area (bottom)
        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Entry field with rounded border
        self.entry_frame = tk.Frame(
            self.input_frame,
            highlightthickness=1,
            bd=0
        )
        self.entry_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.entry = tk.Entry(
            self.entry_frame,
            font=("Arial", 14),
            bd=0,
            highlightthickness=0
        )
        self.entry.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.entry.bind("<Return>", self.send_message)
        
        # Voice button
        self.voice_button = tk.Button(
            self.input_frame,
            text="Voice",
            command=self.toggle_voice_mode,
            font=("Arial", 12, "bold"),
            bd=0,
            padx=15,
            pady=8,
            highlightthickness=0
        )
        self.voice_button.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Send button
        self.send_button = tk.Button(
            self.input_frame,
            text="Send",
            command=lambda: self.send_message(None),
            font=("Arial", 12, "bold"),
            bd=0,
            padx=15,
            pady=8,
            highlightthickness=0
        )
        self.send_button.pack(side=tk.RIGHT)
        
        # Stats area with token savings info
        self.stats_frame = tk.Frame(self.root)
        self.stats_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.token_savings_label = tk.Label(
            self.stats_frame,
            text="Average token savings: 0.00%. Thank you for going green!",
            font=("Arial", 10)
        )
        self.token_savings_label.pack(pady=5)

    def update_logo(self, logo_path):
        """Update the logo with the specified path"""
        try:
            full_logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), logo_path))
            if os.path.exists(full_logo_path):
                original_logo = Image.open(full_logo_path)
                max_size = (180, 60)
                original_logo.thumbnail(max_size, Image.LANCZOS)
                self.logo = ImageTk.PhotoImage(original_logo)
                self.logo_label.configure(image=self.logo)
            else:
                print(f"Logo file not found: {full_logo_path}")
        except Exception as e:
            print(f"Error updating logo: {e}")
    
    def setup_menu(self):
        """Set up the application menu bar"""
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # Add File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Save Chat", command=self.save_chat)
        self.file_menu.add_command(label="Clear Chat", command=self.clear_chat)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.root.quit)

        # Add Tools menu
        self.tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Tools", menu=self.tools_menu)
        self.tools_menu.add_command(
            label="Calculate CO2 Savings",
            command=self.calculate_co2_savings
        )

        # Add Help menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)
        self.help_menu.add_command(label="Info", command=self.show_info)

        # Add View menu
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)
        self.view_menu.add_command(
            label="Toggle Dark/Light Mode",
            command=self.toggle_mode
        )
    
    def create_rounded_rect(self, canvas, x1, y1, x2, y2, radius=15, **kwargs):
        """Create a rounded rectangle on a canvas"""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2 - radius,
            x1, y1 + radius
        ]
        return canvas.create_polygon(points, smooth=True, **kwargs)
        
    def apply_theme(self, is_dark_mode):
        """Apply the selected theme (dark or light) to the application"""
        if is_dark_mode:
            # Dark mode colors
            bg_color = self.colors["dark_bg"]
            secondary_bg = self.colors["dark_secondary"]
            text_color = self.colors["dark_text"]
            button_bg = self.colors["accent"]
            button_fg = "white"
            logo_path = "assets/SUSTAIN_VOICE_WHITE.png" if hasattr(self, 'voice_active') and self.voice_active else "assets/SUSTAIN_WHITE.png"
            entry_highlight = "#444444"
        else:
            # Light mode colors
            bg_color = self.colors["light_bg"]
            secondary_bg = self.colors["light_secondary"]
            text_color = self.colors["light_text"]
            button_bg = self.colors["accent"]
            button_fg = "white"
            logo_path = "assets/SUSTAIN_VOICE_BLACK.png" if hasattr(self, 'voice_active') and self.voice_active else "assets/SUSTAIN_BLACK.png"
            entry_highlight = "#dddddd"

        # Apply theme to main frames
        self.root.configure(bg=bg_color)
        self.header_frame.configure(bg=bg_color)
        self.chat_container.configure(bg=bg_color)
        self.chat_canvas.configure(bg=bg_color)
        self.messages_frame.configure(bg=bg_color)
        self.input_frame.configure(bg=bg_color)
        self.stats_frame.configure(bg=bg_color)
        
        # Apply theme to widgets
        self.logo_label.configure(bg=bg_color)
        self.info_button.configure(bg=button_bg, fg=button_fg)
        self.theme_button.configure(bg=button_bg, fg=button_fg)
        self.entry_frame.configure(bg=secondary_bg, highlightbackground=entry_highlight)
        self.entry.configure(bg=secondary_bg, fg=text_color, insertbackground=text_color)
        self.send_button.configure(bg=button_bg, fg=button_fg)
        self.token_savings_label.configure(bg=bg_color, fg=self.colors["accent"])

        self.send_button.configure(bg=button_bg, fg=button_fg)
        self.voice_button.configure(bg=button_bg, fg=button_fg)  # Add this line
        self.token_savings_label.configure(bg=bg_color, fg=self.colors["accent"])
        
        # Try to update the logo
        try:
            full_logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), logo_path))
            if os.path.exists(full_logo_path):
                original_logo = Image.open(full_logo_path)
                max_size = (180, 60)
                original_logo.thumbnail(max_size, Image.LANCZOS)
                self.logo = ImageTk.PhotoImage(original_logo)
                self.logo_label.configure(image=self.logo)
        except Exception as e:
            print(f"Logo update error: {e}")
    
    def toggle_mode(self):
        """Toggle between dark and light mode"""
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme(self.is_dark_mode)
        
    def create_message_bubble(self, content, is_user=True):
        """Create a message bubble in the chat area with straight edges and curved corners"""
        # Create a frame for this message
        message_frame = tk.Frame(self.messages_frame, bg=self.messages_frame["bg"])
        message_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Determine bubble style
        if is_user:
            bubble_color = self.colors["user_bubble"]
            text_color = "black"
            anchor_side = tk.RIGHT
            bubble_width = min(len(content) * 8 + 20, 400)  # Dynamic width based on content
        else:
            bubble_color = self.colors["ai_bubble"]
            text_color = "white"
            anchor_side = tk.LEFT
            bubble_width = min(len(content) * 8 + 20, 500)  # AI messages can be wider
        
        # Create an inner frame for the bubble (to enable right/left alignment)
        align_frame = tk.Frame(message_frame, bg=self.messages_frame["bg"])
        align_frame.pack(side=anchor_side)
        
        # Calculate height based on text length and width
        line_count = max(1, len(content) // 40) + content.count('\n') + 1
        bubble_height = max(line_count * 20, 40)  # At least 40px height
        
        # Create a canvas for the bubble
        bubble_canvas = tk.Canvas(
            align_frame, 
            width=bubble_width,
            height=bubble_height,
            bg=self.messages_frame["bg"],
            highlightthickness=0
        )
        bubble_canvas.pack(padx=5)
        
        # Draw a true rounded rectangle with curved corners only
        radius = 15  # Corner radius
        
        # Draw the four corners using arcs
        # Top-left corner
        bubble_canvas.create_arc(0, 0, 2*radius, 2*radius, 
                        start=90, extent=90, fill=bubble_color, outline="")
        
        # Top-right corner
        bubble_canvas.create_arc(bubble_width-2*radius, 0, bubble_width, 2*radius, 
                        start=0, extent=90, fill=bubble_color, outline="")
        
        # Bottom-left corner
        bubble_canvas.create_arc(0, bubble_height-2*radius, 2*radius, bubble_height, 
                        start=180, extent=90, fill=bubble_color, outline="")
        
        # Bottom-right corner
        bubble_canvas.create_arc(bubble_width-2*radius, bubble_height-2*radius, 
                        bubble_width, bubble_height, 
                        start=270, extent=90, fill=bubble_color, outline="")
        
        # Draw the straight edges
        # Top edge
        bubble_canvas.create_rectangle(radius, 0, bubble_width-radius, radius,
                            fill=bubble_color, outline="")
        
        # Left edge
        bubble_canvas.create_rectangle(0, radius, radius, bubble_height-radius,
                            fill=bubble_color, outline="")
        
        # Bottom edge
        bubble_canvas.create_rectangle(radius, bubble_height-radius, 
                            bubble_width-radius, bubble_height,
                            fill=bubble_color, outline="")
        
        # Right edge
        bubble_canvas.create_rectangle(bubble_width-radius, radius, 
                            bubble_width, bubble_height-radius,
                            fill=bubble_color, outline="")
        
        # Center rectangle
        bubble_canvas.create_rectangle(radius, radius, 
                            bubble_width-radius, bubble_height-radius,
                            fill=bubble_color, outline="")
        
        # Add the message text
        bubble_canvas.create_text(
            bubble_width/2,
            bubble_height/2,
            text=content,
            width=bubble_width-20,  # Padding inside bubble
            fill=text_color,
            font=("Arial", 12),
            justify=tk.LEFT
        )
        
        # Add timestamp below bubble
        timestamp = datetime.datetime.now().strftime("%H:%M")
        time_label = tk.Label(
            align_frame,
            text=timestamp,
            font=("Arial", 8),
            fg=self.colors["info_text"],
            bg=self.messages_frame["bg"]
        )
        time_label.pack(side=tk.RIGHT if is_user else tk.LEFT, padx=5)
        
        # Make sure we can see the new message
        self.messages_frame.update_idletasks()
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
        self.chat_canvas.yview_moveto(1.0)  # Scroll to bottom


    # VOICE STUFF HERE!!!!
    def handle_voice_input(self):
        """Handle voice input using the voice assistant in a continuous loop"""
        try:
            import speech_recognition as sr
            import threading
            import pyttsx3

            # Initialize the TTS engine
            engine = pyttsx3.init()
            
            # Create a flag for controlling the voice loop
            self.voice_active = True

            self.voice_button.config(text="Stop Voice", bg="#ff6b6b")

            def voice_conversation_loop():
                # Display initial message
                self.display_settings_message("Voice mode activated. Speak to chat with SUSTAIN. Say 'stop voice' to exit voice mode.")
                engine.say("Hello, I'm SUSTAIN Voice, How can I help you today?")
                engine.runAndWait()

                # Initialize recognizer
                recognizer = sr.Recognizer()
                recognizer.pause_threshold = 1.5
                recognizer.energy_threshold = 300

                def listen_for_speech():
                    while self.voice_active:
                        try:
                            # Visual indicator that voice is listening
                            self.display_settings_message("Listening...")
                            
                            # Listen for input
                            with sr.Microphone() as source:
                                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                                audio = recognizer.listen(source, timeout=5, phrase_time_limit=None)

                            try:
                                # Process speech to text
                                user_input = recognizer.recognize_google(audio)

                                if user_input and len(user_input.strip()) > 0:
                                    return user_input
                                
                            except sr.UnknownValueError:
                                continue

                        except Exception as e:
                            self.display_settings_message(f"Listening error: {str(e)}")
                            self.root.after(500, lambda: None)
                    
                    return None
                
                # Keep the conversation going until stopped
                while self.voice_active:
                    # Listen continuously until speech is detected
                    user_input = listen_for_speech()
                    
                    # Check if we've exited the listening loop because voice mode was deactivated
                    if not self.voice_active or user_input is None:
                        break
                    
                    # Check for exit command
                    if user_input.lower() in ["stop voice", "exit voice", "end voice"]:
                        self.voice_active = False
                        self.display_settings_message("Voice mode deactivated.")
                        engine.say("Voice mode deactivated")
                        engine.runAndWait()
                        break
                    
                    # Put the recognized text in the entry field
                    self.entry.delete(0, tk.END)
                    self.entry.insert(0, user_input)
                    
                    # Display what was recognized
                    self.display_settings_message(f"I heard: {user_input}")
                    
                    # Send the message and get response
                    self.send_message(None)
                    
                    # Brief pause before starting to listen again
                    self.root.after(1000, lambda: None)

            # Start the voice conversation loop in a thread
            voice_thread = threading.Thread(target=voice_conversation_loop)
            voice_thread.daemon = True  # Thread will close when main program exits
            voice_thread.start()
                            
                        
            # Set up a check to update the button back when voice mode is deactivated
            def check_voice_status():
                if not self.voice_active:
                    self.voice_button.config(text="Voice", bg=self.colors["accent"])
                else:
                    self.root.after(500, check_voice_status)
            
            check_voice_status()

        
        except ImportError:
            self.display_settings_message("Speech recognition libraries not installed. Please install them manually.")
            self.display_settings_message("Run: pip install SpeechRecognition pyaudio")
        except Exception as e:
            self.display_settings_message(f"Error initializing voice mode: {str(e)}")


    def toggle_voice_mode(self):
        """Toggle voice mode on/off"""
        if not hasattr(self, 'voice_active') or not self.voice_active:
            # Start voice mode
            self.handle_voice_input()
            logo_path = "assets/SUSTAIN_VOICE_WHITE.png" if self.is_dark_mode else "assets/SUSTAIN_VOICE_BLACK.png"
            self.update_logo(logo_path)
        else:
            # Stop voice mode
            self.voice_active = False
            self.voice_button.config(text="Voice", bg=self.colors["accent"])
            self.display_settings_message("Voice mode deactivated.") 

            logo_path = "assets/SUSTAIN_WHITE.png" if self.is_dark_mode else "assets/SUSTAIN_BLACK.png"
            self.update_logo(logo_path)

    def display_settings_message(self, message):
        """Display a system/settings message in the chat area"""
        # Create a frame for the info message
        info_frame = tk.Frame(self.messages_frame, bg=self.messages_frame["bg"])
        info_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # Add the info text with proper styling
        info_label = tk.Label(
            info_frame,
            text=message,
            font=("Arial", 10),
            fg=self.colors["info_text"],
            bg=self.messages_frame["bg"],
            wraplength=500,
            justify=tk.CENTER
        )
        info_label.pack(pady=5)
        
        # Update scrolling
        self.messages_frame.update_idletasks()
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
        self.chat_canvas.yview_moveto(1.0)
    
    def send_message(self, event):
        """Process and send the user's message"""
        user_input = self.entry.get().strip()
        if not user_input:
            return
            
        # Remember this message
        self.message_history.append(user_input)
        
        # Display the user message
        self.create_message_bubble(user_input, is_user=True)
        self.entry.delete(0, tk.END)  # Clear input field
        
        # Check if user input is a math expression
        math_answer = self.sustain.answer_math(user_input)
        if math_answer is not None:
            response_text = f"Math detected! Result: {math_answer}"

            # Display the result of the math expression directly
            self.create_message_bubble(f"Math detected! Result: {math_answer}", is_user=False)
            self.display_settings_message("You saved 100% tokens by using SUSTAIN's math optimizer!")
            
            # Update token savings to 100% for math queries
            self.message_count += 1
            self.total_percentage_saved += 100  # Save 100% savings for math queries
            average_savings = self.total_percentage_saved / self.message_count
            self.token_savings_label.config(
                text=f"Average token savings: {average_savings:.2f}%. Thank you for going green!"
            )

            if hasattr(self, 'voice_active') and self.voice_active:
                try:
                    import pyttsx3
                    engine = pyttsx3.init()
                    engine.say(response_text)
                    engine.runAndWait()
                except Exception as e:
                    print(f"Error speaking: {e}")
            
            self.track_token_length(user_input)
            return  # Exit early to prevent API call

        # Check if user input is the special "what is sustain" command
        if user_input.strip().lower() == "what is sustain?":
            response = (
                "I am SUSTAIN, an environmentally-friendly, token-optimized AI wrapper designed to reduce compute costs "
                "and increase productivity. I filter out irrelevant words and phrases from prompts and limit responses to "
                "essential outputs, minimizing the number of tokens used."
            )
            percentage_saved = 0
        else:
            # Get response from the SUSTAIN API
            response, percentage_saved = self.sustain.get_response(user_input)
        
        # Display the AI response
        self.create_message_bubble(response, is_user=False)

        if hasattr(self, 'voice_active') and self.voice_active:
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.say(response)
                engine.runAndWait()
            except Exception as e:
                print(f"Error speaking {e}")
        
        # Show token savings info
        if percentage_saved == 0:
            self.display_settings_message("With SUSTAIN, you saved 0.00% more tokens compared to traditional AI!")
        else:
            self.display_settings_message(f"With SUSTAIN, you saved {percentage_saved:.2f}% more tokens compared to traditional AI!")
        
        # Update token savings statistics
        self.message_count += 1
        self.total_percentage_saved += percentage_saved
        average_savings = self.total_percentage_saved / self.message_count
        self.token_savings_label.config(
            text=f"Average token savings: {average_savings:.2f}%. Thank you for going green!"
        )
        
        # Track token length
        self.track_token_length(user_input)
            
    def save_chat(self):
        """Save the chat history to a file"""
        if not self.message_history:
            self.display_settings_message("No chat history to save.")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, "w") as file:
                    # Create a formatted chat history
                    responses = []
                    for i, msg in enumerate(self.message_history):
                        file.write(f"You: {msg}\n\n")
                        if i < len(responses):
                            file.write(f"SUSTAIN: {responses[i]}\n\n")
                
                self.display_settings_message(f"Chat history saved to {file_path}")
            except Exception as e:
                self.display_settings_message(f"Error saving chat: {e}")
    
    def clear_chat(self):
        """Clear the chat history"""
        # Clear all message widgets
        for widget in self.messages_frame.winfo_children():
            widget.destroy()
            
        # Reset message history and stats
        self.message_history = []
        self.total_percentage_saved = 0
        self.message_count = 0
        self.token_savings_label.config(
            text="Average token savings: 0.00%. Thank you for going green!"
        )
        
        # Show welcome message again
        self.display_settings_message("Chat history cleared.")
        self.display_settings_message(
            "Welcome to SUSTAIN Chat! Ask me: \"What is SUSTAIN?\" to learn more."
        )
    
    def calculate_co2_savings(self):
        """Calculate and display estimated CO2 savings"""
        kwh_per_token_saved = 0.0001
        co2_per_kwh_saved = 0.7

        total_tokens_saved = 0
        for msg in self.message_history:
            original_tokens = self.sustain.count_tokens(msg)
            optimized_input = self.sustain.text_optimizer.optimize_text(msg)
            optimized_tokens = self.sustain.count_tokens(optimized_input)
            tokens_saved = original_tokens - optimized_tokens
            total_tokens_saved += tokens_saved

            # Assuming response savings as in original code
            response_tokens = 50
            total_tokens_saved += response_tokens

        total_kwh_saved = total_tokens_saved * kwh_per_token_saved * 365
        total_co2_saved = (total_kwh_saved * co2_per_kwh_saved) / 1_000

        # Display the CO2 savings message
        message = (
            f"If you continue using SUSTAIN at this pace for a year, you will have saved approximately {total_kwh_saved:.4f} "
            f"kWh of power, reducing {total_co2_saved:.4f} metric tons of CO2 emissions! Thank you for making a difference!"
        )
        self.display_settings_message(message)
    
    def show_info(self):
        """Show the info/about dialog"""
        info_window = tk.Toplevel(self.root)
        info_window.title("About SUSTAIN Chat")
        info_window.geometry("600x400")
        
        # Apply the current theme colors
        bg_color = self.colors["dark_bg"] if self.is_dark_mode else self.colors["light_bg"]
        fg_color = self.colors["dark_text"] if self.is_dark_mode else self.colors["light_text"]
        
        info_window.configure(bg=bg_color)
        
        # Title at the top
        title_label = tk.Label(
            info_window,
            text="SUSTAIN Chat",
            font=("Arial", 18, "bold"),
            bg=bg_color,
            fg=self.colors["accent"]
        )
        title_label.pack(pady=(20, 15))
        
        # Content frame
        content_frame = tk.Frame(info_window, bg=bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Scrollable info text
        info_text = tk.Text(
            content_frame,
            wrap=tk.WORD,
            font=("Arial", 12),
            bg=bg_color,
            fg=fg_color,
            padx=15,
            pady=10,
            relief=tk.FLAT,
            highlightthickness=0
        )
        
        # Add the info content
        info_text.insert(tk.END, 
            "Welcome to SUSTAIN Chat!\n\n"
            "How to use:\n"
            "  1. Type your message in the text box at the bottom of the window.\n"
            "  2. Press Enter or click the Send button to send your message.\n"
            "  3. SUSTAIN will respond with an optimized message.\n\n"

            "FAQs:\n"
            "What is a token?\n"
            "  A token is a unit of text that the AI processes. Tokens can be as short as one character or as long as one word.\n\n"

            "Ethics Policy:\n"
            "  We follow OpenAI's ethics policy, ensuring that our AI is used responsibly and ethically. "
            "We prioritize user privacy and data security.\n\n"

            "What we cut out and why:\n"
            "  We remove unnecessary words and phrases to optimize the text and reduce the number of tokens used. "
            "This helps in reducing compute costs and environmental impact."
        )
        
        # Make text read-only
        info_text.config(state='disabled')
        
        # Add scrollbar
        scrollbar = tk.Scrollbar(content_frame, command=info_text.yview)
        info_text.configure(yscrollcommand=scrollbar.set)
        
        # Pack text and scrollbar
        info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Close button
        close_button = tk.Button(
            info_window,
            text="Close",
            command=info_window.destroy,
            bg=self.colors["accent"],
            fg="white",
            font=("Arial", 12),
            padx=20,
            pady=5,
            bd=0,
            relief=tk.FLAT
        )
        close_button.pack(pady=15)

# Run the chat application
if __name__ == "__main__":
    root = tk.Tk()
    
    def dummy_track_token_length(user_input):
        pass
    
    app = ChatApp(root, dummy_track_token_length)
    root.mainloop()