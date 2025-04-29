"""
Description: This script creates a chat application using Tkinter that interacts with the SUSTAIN API. 
The chat application allows users to send messages to SUSTAIN and receive optimized responses. 
The application also calculates the average token savings and CO2 emissions saved by using SUSTAIN.

"""
# Import required libraries
import os
import tkinter as tk
from tkinter import scrolledtext, PhotoImage, filedialog
from dotenv import load_dotenv
from sustain import SUSTAIN
from PIL import Image, ImageTk
import platform

# Load environment variables from .env file
load_dotenv()

# Add this before your ChatApp class definition
def create_rounded_rectangle(canvas, x1, y1, x2, y2, radius=25, **kwargs):
    """Create a rounded rectangle on a canvas."""
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

# Add the method to Canvas class
tk.Canvas.create_rounded_rectangle = create_rounded_rectangle

# Create a chat application using Tkinter
class ChatApp:
    def __init__(self, root, track_token_length):
        self.track_token_length = track_token_length
        self.root = root
        self.root.title("SUSTAIN Chat")
        # self.root.attributes("-fullscreen", True)
        self.root.geometry("800x800")
        self.root.iconbitmap("application/assets/icon_Scz_icon.ico")
        self.message_history = []

        # Detect the system the user has
        system = platform.system()

        try:
            base_path = os.path.dirname(os.path.abspath(__file__))

            if system == "Windows":
                icon_path = os.path.join(base_path, "application", "assets", "icon_Scz_icon.ico")
                if os.path.exists(icon_path):
                    self.root.iconbitmap(icon_path)
                    import ctypes
                    myappid = u'company.sustain.chat.1.0'
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
                else:
                    print("Windows icon not found at", icon_path)

            else:
                # macOS or Linux
                icon_path = os.path.join(base_path, "application", "assets", "icon_Scz_icon.ico")
                if os.path.exists(icon_path):
                    icon = tk.PhotoImage(file=icon_path)
                    self.root.iconphoto(True, icon)
                else:
                    print("macOS/Linux icon not found at", icon_path)

        except Exception as e:
            print("Icon load error:", e)

        # Initialize token savings
        self.total_percentage_saved = 0
        self.message_count = 0

        # Initialize dark mode setting
        self.is_dark_mode = False  # Set dark mode as the default

        # Create a top frame for the logo and info button
        self.top_frame = tk.Frame(root)
        self.top_frame.pack(fill=tk.X, pady=10)

        # Load and display the dark mode logo
        logo_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "assets/SUSTAINOriginalWhiteTransparentCropped.png"
            )
        )
        if os.path.exists(logo_path):
            original_logo = Image.open(logo_path)
            max_size = (200, 200)
            original_logo.thumbnail(max_size, Image.LANCZOS)
            self.logo = ImageTk.PhotoImage(original_logo)
        else:
            raise FileNotFoundError(f"Logo file not found at: {logo_path}")

        # Logo label with dark mode background
        self.logo_label = tk.Label(self.top_frame, image=self.logo, bg="#1e1e1e")
        self.logo_label.pack(side=tk.LEFT, padx=10)

        # Info button at the top-right corner
        self.info_button = tk.Button(
            self.top_frame,
            text='?',
            command=self.show_info,
            font=("Mangal_Pro", 14),
            width=3,
            bg="#3c3c3c",
            fg="white"
        )
        self.info_button.pack(side=tk.RIGHT, padx=20)

        # Create a chat area and entry field
        self.chat_area = scrolledtext.ScrolledText(
            root,
            wrap=tk.WORD,
            state='disabled',
            height=25,
            font=("Mangal_Pro", 16)
        )

        self.chat_area.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        self.entry = tk.Entry(root, font=("Mangal_Pro", 16))
        self.entry.pack(padx=20, pady=10, fill=tk.X, expand=True)
        self.entry.bind("<Return>", self.send_message)

        # Add a label to display token percentage saved
        self.token_savings_label = tk.Label(
            root,
            text="Average token savings: 0.00%. Thank you for going green!",
            fg="#318752",
            font=("Mangal_Pro", 16)
        )
        self.token_savings_label.pack(pady=10)

        # Create a menu bar
        self.menu_bar = tk.Menu(root)
        root.config(menu=self.menu_bar)

        # Add File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Save Chat", command=self.save_chat)
        self.file_menu.add_command(label="Clear Chat", command=self.clear_chat)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=root.quit)

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

        # Add View menu for dark/light mode toggle
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)
        self.view_menu.add_command(
            label="Toggle Dark/Light Mode",
            command=self.toggle_mode
        )

        # Apply dark mode settings by default
        self.apply_theme(self.is_dark_mode)

        # Initialize the SUSTAIN API
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key not found. Please set the OPENAI_API_KEY environment variable."
            )
        self.sustain = SUSTAIN(api_key=self.api_key)
        self.display_settings_message(
            "Welcome to SUSTAIN Chat! Ask me: \"What is SUSTAIN?\" to learn more."
        )

    def apply_theme(self, is_dark_mode):
        """Apply the selected theme (dark or light) to the application."""
        if is_dark_mode:
            # Dark mode settings
            bg_color, fg_color, button_bg, button_fg = "#1e1e1e", "white", "#3c3c3c", "white"
            info_button_bg = "#4CAD75"  # Green background for info button
            logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets/SUSTAINOriginalWhiteTransparentCropped.png"))
        else:
            # Light mode settings
            bg_color, fg_color, button_bg, button_fg = "#f5f5f5", "black", "#d9d9d9", "black"
            info_button_bg = "#4CAD75"  # Green background for info button
            logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets/SUSTAINOriginalBlackTransparentCropped.png"))

        # Apply theme to widgets
        self.root.configure(bg=bg_color)
        self.chat_area.configure(bg=bg_color, fg=fg_color, insertbackground=fg_color)
        self.entry.configure(bg=bg_color, fg=fg_color, insertbackground=fg_color)
        self.token_savings_label.configure(bg=bg_color, fg="#318752")
        self.top_frame.configure(bg=bg_color)
        self.info_button.configure(bg=info_button_bg, fg="#4CAD75")  # Green button with white text
        self.menu_bar.configure(bg=bg_color, fg=fg_color)
        self.file_menu.configure(bg=bg_color, fg=fg_color)
        self.tools_menu.configure(bg=bg_color, fg=fg_color)
        self.help_menu.configure(bg=bg_color, fg=fg_color)
        self.view_menu.configure(bg=bg_color, fg=fg_color)
        self.logo_label.configure(bg=bg_color)

        # Update the logo
        if os.path.exists(logo_path):
            original_logo = Image.open(logo_path)
            max_size = (200, 200)
            original_logo.thumbnail(max_size, Image.LANCZOS)
            self.logo = ImageTk.PhotoImage(original_logo)
            self.logo_label.configure(image=self.logo)
        else:
            self.display_settings_message(f"Logo file not found at: {logo_path}")

    def toggle_mode(self):
        """Toggle between dark and light mode."""
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme(self.is_dark_mode)

    # Function to send a message to SUSTAIN
    def send_message(self, event):
        user_input = self.entry.get()
        if user_input:
            self.message_history.append(user_input)
            self.display_message("You: " + user_input)

            # Check if user input is a math expression
            math_answer = self.sustain.answer_math(user_input)
            if math_answer is not None:
                # Display the result of the math expression directly
                self.display_message(f"SUSTAIN: Math detected! Result: {math_answer}")
                self.display_settings_message("You saved 100% tokens by using SUSTAIN's math optimizer!")
                self.entry.delete(0, tk.END)

                # Update token savings to 100% for math queries
                self.message_count += 1
                self.total_percentage_saved += 100  # Save 100% savings for math queries
                average_savings = self.total_percentage_saved / self.message_count
                self.token_savings_label.config(text=f"Average token savings: {average_savings:.2f}%. Thank you for going green!")

                return  # Exit early to prevent API call

            # Check if user input is a special command
            if user_input.strip().lower() == "what is sustain?":
                response = (
                    "I am SUSTAIN, an environmentally-friendly, token-optimized AI wrapper designed to reduce compute costs "
                    "and increase productivity. I filter out irrelevant words and phrases from prompts and limit responses to "
                    "essential outputs, minimizing the number of tokens used."
                )
                percentage_saved = 0
            else:
                response, percentage_saved = self.sustain.get_response(user_input)
            
            # Display the response from SUSTAIN
            self.display_message("\nSUSTAIN: " + response)
            if percentage_saved == 0:
                self.display_settings_message("With SUSTAIN, you saved 0.00% more tokens compared to traditional AI!\n")
            else:
                self.display_settings_message(f"With SUSTAIN, you saved {percentage_saved:.2f}% more tokens compared to traditional AI!\n")
            self.entry.delete(0, tk.END)

            # Update token savings
            self.message_count += 1
            self.total_percentage_saved += percentage_saved
            average_savings = self.total_percentage_saved / self.message_count
            self.token_savings_label.config(text=f"Average token savings: {average_savings:.2f}%. Thank you for going green!")

            self.track_token_length(user_input)

    # Function to display a message in the chat area
    def display_message(self, message):
        self.chat_area.config(state='normal')
        
        # Determine if this is a user or AI message
        if message.startswith("You: "):
            is_user = True
            bg_color = "#eaeaea"  # Light grey for user
            content = message[5:]  # Remove "You: " prefix
        elif message.startswith("\nSUSTAIN: ") or message.startswith("SUSTAIN: "):
            is_user = False
            bg_color = "#99d3ab"  # Light green for AI
            content = message.replace("\nSUSTAIN: ", "").replace("SUSTAIN: ", "")  # Remove prefix
        else:
            # Regular message without special formatting
            self.chat_area.insert(tk.END, message + "\n")
            self.chat_area.config(state='disabled')
            self.chat_area.yview(tk.END)
            return
        
        # Create frame for this message
        frame = tk.Frame(self.chat_area, bg=self.chat_area["bg"])
        self.chat_area.window_create(tk.END, window=frame)
        
        # Create a frame that will contain both the bubble and the label
        message_frame = tk.Frame(frame, bg=self.chat_area["bg"])
        
        # Calculate width based on content (min 100px, max 70% of chat area width)
        chat_width = self.chat_area.winfo_width() or 600  # Default if not yet rendered
        max_width = int(chat_width * 0.7)
        content_width = min(max(100, len(content) * 8), max_width)
        
        # Calculate height based on content
        line_length = content_width // 10  # Approximate chars per line
        num_lines = max(1, len(content) // line_length + content.count('\n') + 1)
        line_height = 24  # Approximate height per line
        canvas_height = num_lines * line_height + 20  # Add padding
        
        # Position the entire message frame to the appropriate side
        if is_user:
            message_frame.pack(side=tk.RIGHT, pady=5)
            frame.pack(fill=tk.X)  # Make the frame take full width
        else:
            message_frame.pack(side=tk.LEFT, pady=5)
            frame.pack(fill=tk.X)  # Make the frame take full width
        
        # Create label first
        if is_user:
            label = tk.Label(message_frame, font=("Arial", 8), fg="#666666", bg=self.chat_area["bg"])
            label.pack(side=tk.RIGHT, padx=2, anchor=tk.SE, pady=(0, 5))
        else:
            label = tk.Label(message_frame, font=("Arial", 8), fg="#666666", bg=self.chat_area["bg"])
            label.pack(side=tk.LEFT, padx=2, anchor=tk.SW, pady=(0, 5))
        
        # Create canvas after the label so it appears below
        canvas = tk.Canvas(
            message_frame, 
            width=content_width,
            height=canvas_height,
            bg=self.chat_area["bg"],
            highlightthickness=0
        )
        
        # Pack canvas to the appropriate side
        if is_user:
            canvas.pack(side=tk.RIGHT, padx=10)  # Add padding to the right side
        else:
            canvas.pack(side=tk.LEFT, padx=10)  # Add padding to the left side
    
        
        # Draw a proper rounded rectangle with curved corners only
        radius = 15  # Radius for corner curvature - adjust as needed
        
        # We need a better implementation of rounded rectangle that only rounds the corners
        # Left-top corner
        canvas.create_arc(0, 0, 2*radius, 2*radius, start=90, extent=90, fill=bg_color, outline="")
        # Right-top corner
        canvas.create_arc(content_width-2*radius, 0, content_width, 2*radius, start=0, extent=90, fill=bg_color, outline="")
        # Left-bottom corner
        canvas.create_arc(0, canvas_height-2*radius, 2*radius, canvas_height, start=180, extent=90, fill=bg_color, outline="")
        # Right-bottom corner
        canvas.create_arc(content_width-2*radius, canvas_height-2*radius, content_width, canvas_height, start=270, extent=90, fill=bg_color, outline="")
        
        # Top edge
        canvas.create_rectangle(radius, 0, content_width-radius, radius, fill=bg_color, outline="")
        # Left edge
        canvas.create_rectangle(0, radius, radius, canvas_height-radius, fill=bg_color, outline="")
        # Bottom edge
        canvas.create_rectangle(radius, canvas_height-radius, content_width-radius, canvas_height, fill=bg_color, outline="")
        # Right edge
        canvas.create_rectangle(content_width-radius, radius, content_width, canvas_height-radius, fill=bg_color, outline="")
        
        # Middle part
        canvas.create_rectangle(radius, radius, content_width-radius, canvas_height-radius, fill=bg_color, outline="")
        
            
        # Add text inside the bubble
        canvas.create_text(
            content_width/2, canvas_height/2,
            text=content, 
            width=content_width-20,
            font=("Mangal_Pro", 14), 
            fill="black",
            justify=tk.LEFT  # Always left-align text for readability
        )
        
        # Add a new line after the bubble
        self.chat_area.insert(tk.END, "\n\n")
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tk.END)
    
    # Add method to Canvas class for drawing rounded rectangles
    def create_rounded_rectangle(self, canvas, x1, y1, x2, y2, radius=25, **kwargs):
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

# Continue with class methods (properly indented)
    def display_settings_message(self, message):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, message + "\n", "grey")
        self.chat_area.tag_config("grey", foreground="grey")
        self.chat_area.config(state='disabled')
        self.chat_area.yview(tk.END)

    # Function to save the chat history to a file
    def save_chat(self):
        chat_history = self.chat_area.get("1.0", tk.END).strip()
        if chat_history:
            file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
            if file_path:
                with open(file_path, "w") as file:
                    file.write(chat_history)
                self.display_settings_message(f"Chat history saved to {file_path}")

    # Function to clear the chat history
    def clear_chat(self):
        self.chat_area.config(state='normal')
        self.chat_area.delete("1.0", tk.END)
        self.chat_area.config(state='disabled')
        self.display_settings_message("Chat history cleared.")

    # Function to calculate CO2 savings based on token savings
    def calculate_co2_savings(self):
        kwh_per_token_saved = 0.0001
        co2_per_kwh_saved = 0.7

        total_tokens_saved = 0
        for msg in self.message_history:
            original_tokens = self.sustain.count_tokens(msg)
            optimized_input = self.sustain.text_optimizer.optimize_text(msg)  # Fix: Use text_optimizer to call optimize_text
            optimized_tokens = self.sustain.count_tokens(optimized_input)
            tokens_saved = original_tokens - optimized_tokens
            total_tokens_saved += tokens_saved

            # Assuming the response is capped at 50 tokens
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
        """Show information about the chat application."""
        info_window = tk.Toplevel(self.root)
        info_window.title("Information")
        info_window.geometry("600x400")

        # Match the color theme of the current mode
        bg_color = "#1e1e1e" if self.is_dark_mode else "white"
        fg_color = "white" if self.is_dark_mode else "black"

        info_window.configure(bg=bg_color)

        # Scrollable text widget
        info_text = (
            "Welcome to SUSTAIN Chat!\n"
            "How to use:\n"
            "  1. Type your message in the text box at the bottom of the window.\n"
            "  2. Press Enter to send your message to SUSTAIN.\n"
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

        # Set UI for text widget
        text_widget = tk.Text(
            info_window, wrap=tk.WORD, font=("Courier", 12), padx=15, pady=10,
            bg=bg_color, fg=fg_color, relief=tk.FLAT
        )
        text_widget.insert(tk.END, info_text)
        text_widget.config(state='disabled')  # Make text read-only

        # Scrollbar configuration
        scrollbar = tk.Scrollbar(info_window, command=text_widget.yview)
        text_widget['yscrollcommand'] = scrollbar.set

        # Packing widgets
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Run the chat application
if __name__ == "__main__":
    root = tk.Tk()
    
    def dummy_track_token_length(user_input):
        pass
    
    app = ChatApp(root, dummy_track_token_length)
    root.mainloop()