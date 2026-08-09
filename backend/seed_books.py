import os
import httpx
from dotenv import load_dotenv
from schemas.books import Books
from openai import OpenAI
import time
from supabase import Client
from supabase_client import get_supabase

load_dotenv()

GOOGLE_BOOKS_API_KEY = os.environ["GOOGLE_BOOKS_API_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
open_ai_client = OpenAI()

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

def embed_books():
    supabase = get_supabase()
    collection_length = len(collection)

    for i in range(0, collection_length, 20):
        batch = collection[i : i + 20]
        descriptions = []
        
        for book in batch:
            descriptions.append(book.description)

        try:
            generate_embedding = open_ai_client.embeddings.create(input=descriptions, model="text-embedding-3-small")
        except Exception as e:
            print(e)
            time.sleep(2)
            continue

        embedded_books = []
        for index, book in enumerate(batch, start=0):
            book_model = book.model_dump()
            book_model["embedding"] = generate_embedding.data[index].embedding
            embedded_books.append(book_model)

        supabase.table("books").insert(embedded_books).execute()
        time.sleep(2)

if __name__ == "__main__":
    get_books()
    embed_books()