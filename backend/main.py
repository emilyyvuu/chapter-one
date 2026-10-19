import os
import httpx
import numpy as np
import json
from fastapi import FastAPI, HTTPException
from supabase import Client
from supabase_client import get_supabase
from dotenv import load_dotenv
from schemas.books import Books
from openai import OpenAI
import asyncio
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

GOOGLE_BOOKS_API_KEY = os.environ["GOOGLE_BOOKS_API_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
 
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    max_attempts = 5
    response = None

    async with httpx.AsyncClient() as client:
        for attempt in range(max_attempts):
            try:
                response = await client.get(
                    "https://www.googleapis.com/books/v1/volumes", params=params
                )
                response.raise_for_status()
                break  # success, leave the loop
            except httpx.HTTPStatusError as e:
                # Only retry rate limits / outages.
                if e.response.status_code not in (429, 503):
                    raise HTTPException(status_code=502, detail="Book search failed")
            except httpx.RequestError:
                pass 

            response = None  # this attempt failed
            if attempt < max_attempts - 1:
                await asyncio.sleep(attempt + 1)  # wait 1s, 2s, 3s

    if response is None:
        raise HTTPException(status_code=503, detail="Book search is temporarily unavailable")

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
    # check that a book hasn't been added yet
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
        book_model["author"] = ", ".join(book.author)
        book_model["embedding"] = generate_embedding.data[0].embedding
        response = supabase.table("books").insert(book_model).execute()
        book_check_id = response.data[0]["id"]

    rating_response = supabase.table("ratings").insert({
        "book_id": book_check_id,
        "rating": rating,
        "user_id": 1 # TODO: replace userid placeholder here
    }).execute()

    return rating_response.data

@app.get("/recommendations")
def get_recommendations(user_id: int):
    supabase = get_supabase()

    # get embeddings of all books the user rated >= 4
    response = supabase.table("ratings").select("books!inner(embedding)").gte("rating", 4).eq("user_id", 1).execute() # TODO: replace userid placeholder here
    if not response.data:
        # if there are no rated books, give no recommendations
        return []

    # create taste vector, average of the embeddings of the rated books returned from the response
    embedding_list = [json.loads(item["books"]["embedding"]) for item in response.data]
    taste_vector = np.mean(embedding_list, axis=0)

    # get the list of excluded books (books that the user rated that shouldn't be included in the 
    # recommendations returned)
    excluded_books = supabase.table("ratings").select("book_id").eq("user_id", 1).execute() # TODO: replace userid placeholder here
    get_excluded_ids = [book["book_id"] for book in excluded_books.data]

    get_matched_books = supabase.rpc("match_books", { "query_embedding": taste_vector.tolist(), "exclude_ids": get_excluded_ids, "match_count": 20 } ).execute()
    return get_matched_books.data