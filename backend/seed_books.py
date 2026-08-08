import os
import httpx
from dotenv import load_dotenv
from schemas.books import Books
from openai import OpenAI
import time

load_dotenv()

GOOGLE_BOOKS_API_KEY = os.environ["GOOGLE_BOOKS_API_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

collection = []
seen_ids = set()
genres = [
    "Fantasy",
    "Science Fiction",
    "Mystery",
    "Romance",
    "Horror",
    "Historical Fiction",
    "Thriller",
    "Literary Fiction",
    "Young Adult Fiction",
    "Biography & Autobiography",
    "History",
    "Psychology",
    "Self-Help",
    "Science",
    "Philosophy",
]

def get_books():
    for genre in genres:
        start = 0 # starting position in collection
        max = 40

        while start <= 80:
            params = {
                "q": f"subject:{genre}",
                "startIndex": start,
                "maxResults": max,
                "key": GOOGLE_BOOKS_API_KEY
            }

            try:
                response = httpx.get("https://www.googleapis.com/books/v1/volumes", params=params)
                response.raise_for_status() 
            except Exception as e:
                print(e)
                time.sleep(2)
                continue
                
            data = response.json()
            books = data.get("items", [])

            for item in books:
                volume_info = item.get("volumeInfo", {})
                google_books_id = item.get("id", None)
                description = volume_info.get("description", None)
                if google_books_id in seen_ids:
                    continue

                if description is None:
                    continue

                record = Books(
                    google_books_id = google_books_id,
                    title = volume_info.get("title", None),
                    author = volume_info.get("authors", []),
                    description = description,
                    cover_url = volume_info.get("imageLinks", {}).get("thumbnail", None)
                )

                collection.append(record)
                seen_ids.add(google_books_id)
            start += 40
            time.sleep(2)

            # TODO: embedding calls
            # TODO: insert to database

if __name__ == "__main__":
    get_books()
    print(len(collection))