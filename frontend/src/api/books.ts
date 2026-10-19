import type { Book } from "../types";

/**
 * GET /search
 * gets the Google Books results from the search query
 */
 export async function getSearchResults(searchQuery: string) {
    const params = new URLSearchParams({ q: searchQuery });
    const response = await fetch(`http://127.0.0.1:8000/search?${params}`);

    if (!response.ok) {
        throw new Error(`Get search results request failed: ${response.status}`);
    }

    return await response.json();
 }

/**
 * GET /library
 * gets the user's books that were added/rated
 */
export async function getBooks() {
    const response = await fetch("http://127.0.0.1:8000/library");

    if (!response.ok) {
        throw new Error(`Get library books request failed: ${response.status}`);
    }

    const data = await response.json();
    return data;
}

/**
 * POST /library
 * adds a book to a user's library and includes their rating of the book
 */
export async function addBook(
    rating: number, 
    book: Book
) {
    const params = new URLSearchParams({ rating: String(rating) });
    const response = await fetch(`http://127.0.0.1:8000/library?${params}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(book),
    });

    if (!response.ok) {
        throw new Error(`Adding book failed: ${response.status}`);
    }

    return await response.json();
}

/**
 * GET /recommendations
 * gets recommended books based on the user's taste vector
 */
export async function getRecommendations(user_id: number) {
    const params = new URLSearchParams({ user_id: String(user_id) });
    const response = await fetch(`http://127.0.0.1:8000/recommendations?${params}`);

    if (!response.ok) {
        throw new Error(`Get recommendations request failed: ${response.status}`);
    }

    const data = await response.json();
    return data;
}