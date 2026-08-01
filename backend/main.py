import os
import httpx
from fastapi import FastAPI, HTTPException
from supabase import Client
from supabase_client import get_supabase
from dotenv import load_dotenv
from schemas.books import Books
from openai import OpenAI

load_dotenv()

GOOGLE_BOOKS_API_KEY = os.environ["GOOGLE_BOOKS_API_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
 
app = FastAPI()
open_ai_client = OpenAI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

# Search for a specific book in Google Books and return results
@app.get("/search")
async def search_book(q: str):
    params = {
        "q": q,
        "key": GOOGLE_BOOKS_API_KEY
    }
    async with httpx.AsyncClient() as client:
        response = await client.get("https://www.googleapis.com/books/v1/volumes", params=params)
        response.raise_for_status()  

    data = response.json()
    items = data.get("items", [])
    book_list = []

    for item in items:
        volume_info = item.get("volumeInfo", {})
        record = Books(
            google_books_id = item.get("id", None),
            title = volume_info.get("title", None),
            author = volume_info.get("authors", []),
            description = volume_info.get("description", None),
            cover_url = volume_info.get("imageLinks", {}).get("thumbnail", None)
        )

        book_list.append(record)

    return book_list

# Get the user's library (the books the user added + rated)
@app.get("/library")
def get_library():
    supabase = get_supabase()
    response = supabase.table("ratings").select("*, books(*)").execute()
    return response.data

# Add a book to the user's library and provide a rating
@app.post("/library")
def add_book(book: Books, rating: int):
    supabase = get_supabase()
    book_check = (
        supabase.table("books")
        .select("id")
        .eq("google_books_id", book.google_books_id)
        .execute()
    )

    if book_check.data:
        book_check_id = book_check.data[0]["id"]
    else:
        embedding_input = book.description

        if embedding_input is None:
            embedding_input =  " ".join(book.author + [book.title])

        generate_embedding = open_ai_client.embeddings.create(
                                input=embedding_input, 
                                model="text-embedding-3-small"
                            )
        book_model = book.model_dump()
        book_model["embedding"] = generate_embedding.data[0].embedding
        response = supabase.table("books").insert(book_model).execute()
        book_check_id = response.data[0]["id"]

    rating_response = supabase.table("ratings").insert({
        "book_id": book_check_id,
        "rating": rating,
        "user_id": 1
    }).execute()

    return rating_response.data
