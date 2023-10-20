import os
import psycopg2
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from datetime import datetime, timezone

CREATE_BOOKS_TABLE = """CREATE TABLE IF NOT EXISTS books (
                        id SERIAL PRIMARY KEY,
                        title TEXT,
                        author TEXT);"""

SELECT_ALL_BOOKS = """SELECT * FROM books;"""

SELECT_BOOK_BY_ID = """SELECT * FROM books WHERE id = %s;"""

INSERT_BOOK = "INSERT INTO books (title, author) VALUES (%s, %s) RETURNING id;"

DELETE_BOOK = """DELETE FROM books WHERE id = %s;"""


load_dotenv()

app = Flask(__name__)

url = os.getenv("DATABASE_URL")


@app.route("/api/books", methods=["GET"])
def getBooks():
    connection = psycopg2.connect(url)

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(SELECT_ALL_BOOKS)
            books = cursor.fetchall()

    connection.close()

    books_list = []
    for book in books:
        book_dict = {"id": book[0], "title": book[1], "author": book[2]}
        books_list.append(book_dict)

    return jsonify(books_list), 200


@app.route("/api/books/<int:book_id>", methods=["GET"])
def getBookById(book_id):
    connection = psycopg2.connect(url)

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(SELECT_BOOK_BY_ID, (book_id,))
            book = cursor.fetchone()

    connection.close()

    if book is None:
        return {"error": f"Livro com ID {book_id} não encontrado."}, 404

    book_dict = {"id": book[0], "title": book[1], "author": book[2]}

    return jsonify(book_dict)


@app.route("/api/books", methods=["POST"])
def addBook():
    data = request.get_json()

    title = data["title"]
    author = data["author"]

    connection = psycopg2.connect(url)

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_BOOKS_TABLE)
            cursor.execute(INSERT_BOOK, (title, author))
            id = cursor.fetchone()[0]

    connection.close()

    return {"id": id, "message": f"Book {title} created."}, 201


@app.route("/api/books/<int:book_id>", methods=["PUT"])
def editBook(book_id):
    data = request.get_json()

    title = data.get("title")
    author = data.get("author")

    if title is None and author is None:
        return {"error": "Nenhum dado de livro fornecido para edição."}, 400

    connection = psycopg2.connect(url)

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(SELECT_BOOK_BY_ID, (book_id,))

            existing_book = cursor.fetchone()

            if existing_book is None:
                return {"error": f"Livro com ID {book_id} não encontrado."}, 404

            if title:
                cursor.execute(
                    "UPDATE books SET title = %s WHERE id = %s;", (title, book_id)
                )
            if author is not None and title is not None:
                cursor.execute(
                    "UPDATE books SET title = %s, author = %s WHERE id = %s;",
                    (title, author, book_id),
                )

    connection.close()

    return {"message": f"Livro com ID {book_id} foi atualizado com sucesso."}


@app.route("/api/books/<int:book_id>", methods=["DELETE"])
def deleteBook(book_id):
    connection = psycopg2.connect(url)

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(DELETE_BOOK, (book_id,))

            existing_book = cursor.fetchone()

            if existing_book is None:
                connection.close()
                return {"error": f"Livro com ID {book_id} não encontrado."}, 404

            cursor.execute(DELETE_BOOK, (book_id,))

    connection.close()

    return {"message": f"Livro com ID {book_id} foi excluído com sucesso."}
