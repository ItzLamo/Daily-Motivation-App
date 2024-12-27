# Daily Motivation App

A Python app that provides daily motivational quotes, lets you search, save to favorites, and view history. It also sends daily notifications with a random quote.

## Features
- Get daily motivational quotes.
- Search for quotes by text, author, or tag.
- Save quotes to favorites.
- View your quote history.
- Set a custom time for daily notifications.

## Requirements
- Python 3.x
- `customtkinter` for the GUI.
- `plyer` for notifications.

Install the required libraries:

```bash
pip install customtkinter plyer
```

## Usage

1. Clone the repository.
2. Make sure the `quotes_database.py` file is in the same directory.
3. Run the app:

```bash
python main.py
```

## File Structure
```
.
├── main.py                # Main app file
├── quotes_database.py     # Quotes data
└── .motivation_app/       # App data (favorites & history)
    ├── favorites.json     # User's favorite quotes
    └── history.json       # User's viewed quotes
```
