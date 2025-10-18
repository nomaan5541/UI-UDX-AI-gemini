import os
import tkinter as tk
from tkinter import messagebox
from dotenv import set_key, load_dotenv
from google import genai
import customtkinter as ctk

# --- Configuration ---
ENV_FILE = ".env"
USERS_FILE = "users.txt"
MODEL_NAME = "gemini-2.5-flash"
ctk.set_appearance_mode("Dark") 
ctk.set_default_color_theme("blue")

# --- User Management Functions ---

def load_users():
    """Loads usernames and passwords from a simple text file."""
    users = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        # Ensures it can handle only one comma separator
                        username, password = line.strip().split(',', 1) 
                        users[username] = password
                    except ValueError:
                        # Skip malformed lines if any
                        continue
    return users

def save_user(username, password):
    """Appends a new user to the users file."""
    with open(USERS_FILE, 'a') as f:
        f.write(f"{username},{password}\n")

def set_gemini_api_key(api_key):
    """Sets the API key in the .env file."""
    # Ensure the .env file exists
    if not os.path.exists(ENV_FILE):
        open(ENV_FILE, 'a').close()
    
    # Set the key, which will automatically update the .env file
    set_key(ENV_FILE, "GEMINI_API_KEY", api_key)
    print(f"API key successfully written to {ENV_FILE}")

# --- Main Application Class ---

class GeminiChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gemini AI Chat")
        self.geometry("800x600")
        
        # Configure grid for dynamic resizing
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.current_user = None
        self.chat_client = None
        self.chat_session = None

        self.show_login_page()

    # --- UI Switching Methods ---

    def clear_page(self):
        """Clears all widgets from the current view."""
        for widget in self.winfo_children():
            widget.destroy()

    def show_login_page(self):
        self.clear_page()
        self.page_frame = ctk.CTkFrame(self)
        self.page_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        # Configure frame for centering
        self.page_frame.grid_rowconfigure((0, 4), weight=1)
        self.page_frame.grid_columnconfigure((0, 2), weight=1)

        # Title
        ctk.CTkLabel(self.page_frame, text="AI LOG IN", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=1, pady=(20, 10), sticky="s")

        # Username Input
        self.login_username_entry = ctk.CTkEntry(self.page_frame, placeholder_text="Username", width=250)
        self.login_username_entry.grid(row=1, column=1, pady=10, padx=20, sticky="n")

        # Password Input
        self.login_password_entry = ctk.CTkEntry(self.page_frame, placeholder_text="Password", show="*", width=250)
        self.login_password_entry.grid(row=2, column=1, pady=10, padx=20)

        # Login Button
        ctk.CTkButton(self.page_frame, text="LOGIN", command=self.attempt_login, width=250).grid(row=3, column=1, pady=20, padx=20)

        # Switch to Register Button
        ctk.CTkButton(self.page_frame, text="Need an Account? Register", command=self.show_register_page, fg_color="transparent", text_color=("gray10", "gray80")).grid(row=4, column=1, pady=(0, 20), sticky="n")

    def show_register_page(self):
        self.clear_page()
        self.page_frame = ctk.CTkFrame(self)
        self.page_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # Configure frame for centering
        self.page_frame.grid_rowconfigure((0, 6), weight=1)
        self.page_frame.grid_columnconfigure((0, 2), weight=1)

        # Title
        ctk.CTkLabel(self.page_frame, text="AI REGISTRATION", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=1, pady=(20, 10), sticky="s")

        # Username Input
        self.reg_username_entry = ctk.CTkEntry(self.page_frame, placeholder_text="Username", width=250)
        self.reg_username_entry.grid(row=1, column=1, pady=10, padx=20, sticky="n")

        # Email Input
        self.reg_email_entry = ctk.CTkEntry(self.page_frame, placeholder_text="Email", width=250)
        self.reg_email_entry.grid(row=2, column=1, pady=10, padx=20)
        
        # API Key Input (Crucial)
        self.reg_apikey_entry = ctk.CTkEntry(self.page_frame, placeholder_text="Gemini API Key (Required)", width=250)
        self.reg_apikey_entry.grid(row=3, column=1, pady=10, padx=20)
        
        # Password Input
        self.reg_password_entry = ctk.CTkEntry(self.page_frame, placeholder_text="Password", show="*", width=250)
        self.reg_password_entry.grid(row=4, column=1, pady=10, padx=20)

        # Register Button
        ctk.CTkButton(self.page_frame, text="REGISTER & LOGIN", command=self.attempt_register, width=250).grid(row=5, column=1, pady=20, padx=20)

        # Switch to Login Button
        ctk.CTkButton(self.page_frame, text="Already have an account? Login", command=self.show_login_page, fg_color="transparent", text_color=("gray10", "gray80")).grid(row=6, column=1, pady=(0, 20), sticky="n")

    def show_chat_page(self):
        self.clear_page()
        
        # Configure layout for chat interface
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # --- Top Frame (Chat History) ---
        chat_history_frame = ctk.CTkFrame(self)
        chat_history_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="nsew")
        chat_history_frame.grid_columnconfigure(0, weight=1)
        chat_history_frame.grid_rowconfigure(0, weight=1)

        # FIX: Removed explicit font=("Consolas", 14) to resolve the scaling error (AttributeError)
        self.chat_textbox = ctk.CTkTextbox(chat_history_frame, state="disabled", wrap="word", corner_radius=10)
        self.chat_textbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # --- Bottom Frame (Input and Button) ---
        input_frame = ctk.CTkFrame(self)
        input_frame.grid(row=1, column=0, padx=10, pady=(5, 10), sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)

        self.input_entry = ctk.CTkEntry(input_frame, placeholder_text="Ask Gemini...", height=40)
        self.input_entry.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        self.input_entry.bind("<Return>", lambda event: self.send_message_thread()) # Bind Enter key

        self.send_button = ctk.CTkButton(input_frame, text="SEND", command=self.send_message_thread, height=40, width=100)
        self.send_button.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="e")
        
        # Initial greeting
        self.display_message("System", f"Welcome, {self.current_user}! Chat with {MODEL_NAME}.")


    # --- Authentication Logic ---

    def attempt_login(self):
        username = self.login_username_entry.get()
        password = self.login_password_entry.get()
        
        users = load_users()

        if username in users and users[username] == password:
            self.current_user = username
            
            # Since the API key is set during registration, we load it now
            load_dotenv()
            api_key = os.getenv("GEMINI_API_KEY")
            
            if not api_key:
                messagebox.showerror("Error", "API Key not found in .env. Please re-register.")
                self.show_register_page()
                return

            try:
                self.chat_client = genai.Client(api_key=api_key)
                self.chat_session = self.chat_client.chats.create(model=MODEL_NAME)
                self.show_chat_page()
            except Exception as e:
                messagebox.showerror("Connection Error", f"Failed to initialize Gemini API. Is your key correct? Error: {e}")
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    def attempt_register(self):
        username = self.reg_username_entry.get()
        email = self.reg_email_entry.get()
        api_key = self.reg_apikey_entry.get()
        password = self.reg_password_entry.get()

        if not (username and api_key and password):
            messagebox.showerror("Registration Failed", "Username, API Key, and Password are required.")
            return

        users = load_users()
        if username in users:
            messagebox.showerror("Registration Failed", "Username already exists.")
            return
        
        # 1. Save the API Key to .env
        set_gemini_api_key(api_key)
        
        # 2. Save the new user
        save_user(username, password)
        
        messagebox.showinfo("Success", "Registration complete! Logging you in...")
        
        # 3. Auto-login FIX: Must show the login page first to create the entries
        self.show_login_page() 
        
        # Now, the entries exist and can be safely manipulated.
        # Note: The 'delete' calls that caused the error are now safe because the widgets exist.
        self.login_username_entry.delete(0, tk.END)
        self.login_password_entry.delete(0, tk.END)
        self.login_username_entry.insert(0, username)
        self.login_password_entry.insert(0, password)
        
        self.attempt_login()


    # --- Chat Logic ---
    
    def display_message(self, sender, message):
        """Adds a message to the chat history textbox."""
        self.chat_textbox.configure(state="normal")
        if sender == "System":
            color = "#AAAAAA" # Grey for system
        elif sender == "You":
            color = "#00BFFF" # Deep blue for user
        else:
            color = "#33FF33" # Bright green for AI
        
        self.chat_textbox.insert(tk.END, f"{sender}: ", ("sender_tag",))
        self.chat_textbox.insert(tk.END, f"{message}\n\n")
        
        # FIX: The font attribute must be a CTkFont object (or omitted) 
        # to avoid the scaling error. Using CTkFont(weight="bold") is a safe way to style.
        try:
            self.chat_textbox.tag_config("sender_tag", foreground=color, font=ctk.CTkFont(weight="bold"))
        except AttributeError:
             # Fallback if the first fails (though it shouldn't now)
             self.chat_textbox.tag_config("sender_tag", foreground=color) 
        
        self.chat_textbox.configure(state="disabled")
        self.chat_textbox.see(tk.END) # Scroll to the bottom

    def send_message_thread(self):
        """Handles sending the message and updating the UI."""
        user_message = self.input_entry.get().strip()
        self.input_entry.delete(0, tk.END)

        if not user_message:
            return

        self.display_message("You", user_message)
        self.send_button.configure(state="disabled", text="THINKING...")

        # Use self.after for simple scheduling (not a real thread, but avoids freezing for fast responses)
        self.after(100, lambda: self.process_ai_response(user_message))

    def process_ai_response(self, user_message):
        try:
            # Send message to the Gemini chat session
            response = self.chat_session.send_message(user_message)
            ai_response = response.text
        except Exception as e:
            ai_response = f"Error: Could not get a response from Gemini. {e}"

        self.display_message("Gemini", ai_response)
        self.send_button.configure(state="normal", text="SEND")

# --- Run the Application ---
if __name__ == "__main__":
    app = GeminiChatApp()
    app.mainloop()