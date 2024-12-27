import customtkinter as ctk
import json
import os
import threading
import time
from datetime import datetime
from tkinter import filedialog
from plyer import notification
from typing import Dict, List, Optional
import random
from quotes_database import QUOTES_DATABASE

class QuoteService:
    def __init__(self):
        self.quotes = QUOTES_DATABASE
        self._generate_tags()

    def _generate_tags(self):
        """Generate unique tags from the quotes database"""
        self.tags = sorted(list(set(
            tag for quote in self.quotes 
            for tag in quote["tags"]
        )))

    def get_random_quote(self, tag: str = None) -> Optional[Dict]:
        """Get a random quote, optionally filtered by tag"""
        matching_quotes = [
            q for q in self.quotes 
            if not tag or tag in q["tags"]
        ]
        return random.choice(matching_quotes) if matching_quotes else None

    def get_tags(self) -> List[str]:
        """Get all available tags"""
        return self.tags

    def search_quotes(self, query: str) -> List[Dict]:
        """Search quotes by content or author"""
        query = query.lower()
        return [
            q for q in self.quotes
            if query in q["content"].lower() or 
               query in q["author"].lower() or
               any(query in tag.lower() for tag in q["tags"])
        ]

class StorageManager:
    def __init__(self):
        self.data_dir = os.path.join(os.path.expanduser("~"), ".motivation_app")
        self.favorites_file = os.path.join(self.data_dir, "favorites.json")
        self.history_file = os.path.join(self.data_dir, "history.json")
        self._init_storage()

    def _init_storage(self):
        os.makedirs(self.data_dir, exist_ok=True)
        for file in [self.favorites_file, self.history_file]:
            if not os.path.exists(file):
                with open(file, 'w') as f:
                    json.dump([], f)

    def add_favorite(self, quote: Dict):
        favorites = self.get_favorites()
        if quote not in favorites:
            favorites.append(quote)
            with open(self.favorites_file, 'w') as f:
                json.dump(favorites, f)

    def get_favorites(self) -> List[Dict]:
        with open(self.favorites_file, 'r') as f:
            return json.load(f)

    def add_to_history(self, quote: Dict):
        history = self.get_history()
        quote["viewed_at"] = datetime.now().isoformat()
        history.append(quote)
        with open(self.history_file, 'w') as f:
            json.dump(history, f)

    def get_history(self) -> List[Dict]:
        with open(self.history_file, 'r') as f:
            return json.load(f)

    def export_favorites(self, filepath: str):
        favorites = self.get_favorites()
        with open(filepath, 'w') as f:
            for quote in favorites:
                f.write(f'"{quote["content"]}" - {quote["author"]}\n')

class NotificationManager:
    def __init__(self):
        self.notification_time = datetime.strptime("09:00", "%H:%M").time()
        self.is_running = False
        self.thread = None
        self.quote_service = QuoteService()

    def set_notification_time(self, hour: int, minute: int):
        self.notification_time = datetime.strptime(
            f"{hour:02d}:{minute:02d}", 
            "%H:%M"
        ).time()

    def show_notification(self):
        quote = self.quote_service.get_random_quote()
        if quote:
            notification.notify(
                title="Daily Motivation",
                message=f'"{quote["content"]}" - {quote["author"]}',
                timeout=10
            )

    def _notification_loop(self):
        while self.is_running:
            now = datetime.now().time()
            if (now.hour == self.notification_time.hour and 
                now.minute == self.notification_time.minute):
                self.show_notification()
                time.sleep(60)
            time.sleep(30)

    def start_notifications(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._notification_loop)
            self.thread.daemon = True
            self.thread.start()

    def stop_notifications(self):
        self.is_running = False
        if self.thread:
            self.thread.join()

class MotivationApp:
    def __init__(self):
        self.quote_service = QuoteService()
        self.notification_manager = NotificationManager()
        self.storage_manager = StorageManager()
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        self.window = ctk.CTk()
        self.window.title("Daily Motivation")
        self.window.geometry("700x400")
        
        self.tags = [""] + self.quote_service.get_tags()
        self.current_quote = None
        
        self.setup_ui()

    def setup_ui(self):
        main_container = ctk.CTkTabview(self.window)
        main_container.pack(pady=20, padx=20, fill="both", expand=True)
        
        main_container.add("Daily Quote")
        main_container.add("Search")
        main_container.add("Favorites")
        main_container.add("History")
        main_container.add("Settings")
        
        self.setup_daily_quote_tab(main_container.tab("Daily Quote"))
        self.setup_search_tab(main_container.tab("Search"))
        self.setup_favorites_tab(main_container.tab("Favorites"))
        self.setup_history_tab(main_container.tab("History"))
        self.setup_settings_tab(main_container.tab("Settings"))

    def setup_daily_quote_tab(self, parent):
        category_frame = ctk.CTkFrame(parent)
        category_frame.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkLabel(category_frame, text="Category:").pack(side="left", padx=5)
        self.category_var = ctk.StringVar(value="")
        category_dropdown = ctk.CTkOptionMenu(
            category_frame,
            values=self.tags,
            variable=self.category_var,
            command=lambda _: self.update_quote()
        )
        category_dropdown.pack(side="left", padx=5)
        
        quote_frame = ctk.CTkFrame(parent)
        quote_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        self.quote_text = ctk.CTkTextbox(quote_frame, height=150)
        self.quote_text.pack(pady=10, padx=10, fill="both", expand=True)
        self.quote_text.configure(state="disabled")
        
        buttons_frame = ctk.CTkFrame(quote_frame)
        buttons_frame.pack(pady=10, fill="x")
        
        ctk.CTkButton(
            buttons_frame,
            text="New Quote",
            command=self.update_quote
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            buttons_frame,
            text="Add to Favorites",
            command=self.add_to_favorites
        ).pack(side="left", padx=5)

    def setup_search_tab(self, parent):
        search_frame = ctk.CTkFrame(parent)
        search_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search quotes...")
        search_entry.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkButton(
            search_frame,
            text="Search",
            command=lambda: self.search_quotes(search_entry.get())
        ).pack(pady=5)
        
        self.search_results = ctk.CTkTextbox(search_frame)
        self.search_results.pack(pady=10, padx=10, fill="both", expand=True)
        self.search_results.configure(state="disabled")

    def setup_favorites_tab(self, parent):
        favorites_frame = ctk.CTkFrame(parent)
        favorites_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        self.favorites_text = ctk.CTkTextbox(favorites_frame)
        self.favorites_text.pack(pady=10, padx=10, fill="both", expand=True)
        self.favorites_text.configure(state="disabled")
        
        ctk.CTkButton(
            favorites_frame,
            text="Export Favorites",
            command=self.export_favorites
        ).pack(pady=10)
        
        self.update_favorites_display()

    def setup_history_tab(self, parent):
        history_frame = ctk.CTkFrame(parent)
        history_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        self.history_text = ctk.CTkTextbox(history_frame)
        self.history_text.pack(pady=10, padx=10, fill="both", expand=True)
        self.history_text.configure(state="disabled")
        
        self.update_history_display()

    def setup_settings_tab(self, parent):
        settings_frame = ctk.CTkFrame(parent)
        settings_frame.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkLabel(settings_frame, text="Notification Time (24h):").pack(pady=5)
        
        time_entry = ctk.CTkEntry(settings_frame, placeholder_text="HH:MM")
        time_entry.pack(pady=5)
        
        def set_notification():
            try:
                hour, minute = map(int, time_entry.get().split(":"))
                self.notification_manager.set_notification_time(hour, minute)
                self.notification_manager.start_notifications()
                self.show_message("Success", "Notification time set successfully!")
            except ValueError:
                self.show_error("Please enter time in HH:MM format")
        
        ctk.CTkButton(
            settings_frame,
            text="Set Daily Notification",
            command=set_notification
        ).pack(pady=10)

    def update_quote(self):
        quote_data = self.quote_service.get_random_quote(self.category_var.get())
        if quote_data:
            self.current_quote = quote_data
            self.quote_text.configure(state="normal")
            self.quote_text.delete("1.0", "end")
            self.quote_text.insert("1.0", f'"{quote_data["content"]}"\n\n- {quote_data["author"]}')
            self.quote_text.configure(state="disabled")
            self.storage_manager.add_to_history(quote_data)
            self.update_history_display()
        else:
            self.show_error("Failed to fetch quote. Please try again.")

    def add_to_favorites(self):
        if self.current_quote:
            self.storage_manager.add_favorite(self.current_quote)
            self.update_favorites_display()
            self.show_message("Success", "Quote added to favorites!")

    def search_quotes(self, query: str):
        results = self.quote_service.search_quotes(query)
        self.search_results.configure(state="normal")
        self.search_results.delete("1.0", "end")
        if results:
            for quote in results:
                self.search_results.insert("end", f'"{quote["content"]}"\n- {quote["author"]}\n\n')
        else:
            self.search_results.insert("end", "No results found.")
        self.search_results.configure(state="disabled")

    def update_favorites_display(self):
        favorites = self.storage_manager.get_favorites()
        self.favorites_text.configure(state="normal")
        self.favorites_text.delete("1.0", "end")
        for quote in favorites:
            self.favorites_text.insert("end", f'"{quote["content"]}"\n- {quote["author"]}\n\n')
        self.favorites_text.configure(state="disabled")

    def update_history_display(self):
        history = self.storage_manager.get_history()
        self.history_text.configure(state="normal")
        self.history_text.delete("1.0", "end")
        for quote in history:
            viewed_at = datetime.fromisoformat(quote["viewed_at"]).strftime("%Y-%m-%d %H:%M")
            self.history_text.insert("end", f'[{viewed_at}]\n"{quote["content"]}"\n- {quote["author"]}\n\n')
        self.history_text.configure(state="disabled")

    def export_favorites(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            title="Export Favorites"
        )
        if filepath:
            self.storage_manager.export_favorites(filepath)
            self.show_message("Success", "Favorites exported successfully!")

    def show_error(self, message: str):
        self.show_message("Error", message)

    def show_message(self, title: str, message: str):
        dialog = ctk.CTkToplevel(self.window)
        dialog.title(title)
        dialog.geometry("300x150")
        
        ctk.CTkLabel(dialog, text=message).pack(pady=20)
        ctk.CTkButton(dialog, text="OK", command=dialog.destroy).pack(pady=10)
    
    def run(self):
        self.update_quote()
        self.window.mainloop()
        
    def cleanup(self):
        self.notification_manager.stop_notifications()

if __name__ == "__main__":
    app = MotivationApp()
    try:
        app.run()
    finally:
        app.cleanup()