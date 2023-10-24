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

INSERT_BOOK = (
    "INSERT INTO books (title, author) VALUES (%s, %s) RETURNING id, title, author;"
)

DELETE_BOOK = """DELETE FROM books WHERE id = %s;"""

UPDATE_BOOK = """UPDATE books SET title = %s, author = %s WHERE id = %s;"""


load_dotenv()

app = Flask(__name__)

url = os.getenv("DATABASE_URL")


def create_response(
    data=None, status_error=False, messageError=None, message=None, status_code=500
):
    response = {"statusError": status_error}

    if data:
        response["data"] = data

    if messageError:
        response["messageError"] = "Erro na requisição: " + str(messageError)

    if message:
        response["message"] = message

    return jsonify(response), status_code


@app.route("/api/books", methods=["GET"])
def getBooks():
    try:
        connection = psycopg2.connect(url)

        with connection:
            with connection.cursor() as cursor:
                cursor.execute(SELECT_ALL_BOOKS)
                books = cursor.fetchall()

        books_list = []

        for book in books:
            book_dict = {"id": book[0], "title": book[1], "author": book[2]}
            books_list.append(book_dict)

        return create_response(
            data=books_list, message="Requisição OK", status_code=200
        )
    except Exception as e:
        return create_response(status_error=True, messageError=e)


@app.route("/api/books/<int:book_id>", methods=["GET"])
def getBookById(book_id):
    try:
        connection = psycopg2.connect(url)

        with connection:
            with connection.cursor() as cursor:
                cursor.execute(SELECT_BOOK_BY_ID, (book_id,))
                book = cursor.fetchone()

        connection.close()

        if book is None:
            return create_response(
                status_error=True,
                message=f"Livro com ID {book_id} não encontrado.",
                status_code=404,
            )

        book_dict = {"id": book[0], "title": book[1], "author": book[2]}

        return create_response(data=book_dict, message="Requisição OK", status_code=200)
    except Exception as e:
        return create_response(status_error=True, messageError=e)


@app.route("/api/books", methods=["POST"])
def addBook():
    try:
        data = request.get_json()

        title = data["title"]
        author = data["author"]

        connection = psycopg2.connect(url)

        with connection:
            with connection.cursor() as cursor:
                cursor.execute(INSERT_BOOK, (title, author))

                data = cursor.fetchall()[0]

                id = data[0]
                titleInserted = data[1]
                authorInserted = data[2]

        connection.close()

        bookInserted = {"id": id, "title": titleInserted, "author": authorInserted}

        return create_response(
            data=bookInserted, message=f"Book {titleInserted} created.", status_code=201
        )
    except Exception as e:
        return create_response(status_error=True, messageError=e)


@app.route("/api/books/<int:book_id>", methods=["PUT"])
def editBook(book_id):
    try:
        data = request.get_json()

        title = data.get("title")
        author = data.get("author")

        if title is None or author is None:
            return create_response(
                status_error=True,
                message="Forneça titulo e autor para edição.",
                status_code=400,
            )

        connection = psycopg2.connect(url)

        with connection:
            with connection.cursor() as cursor:
                cursor.execute(SELECT_BOOK_BY_ID, (book_id,))

                existing_book = cursor.fetchone()

                if existing_book is None:
                    return create_response(
                        status_error=True,
                        message=f"Livro com ID {book_id} não encontrado.",
                        status_code=404,
                    )

                if author is not None and title is not None:
                    cursor.execute(
                        UPDATE_BOOK,
                        (title, author, book_id),
                    )

        connection.close()

        return create_response(
            message=f"Livro com ID {book_id} foi atualizado com sucesso.",
            status_code=200,
        )
    except Exception as e:
        return create_response(status_error=True, messageError=e)


@app.route("/api/books/<int:book_id>", methods=["DELETE"])
def deleteBook(book_id):
    try:
        connection = psycopg2.connect(url)

        with connection:
            with connection.cursor() as cursor:
                cursor.execute(SELECT_BOOK_BY_ID, (book_id,))

                existing_book = cursor.fetchone()

                if existing_book is None:
                    connection.close()

                    return create_response(
                        status_error=True,
                        message=f"Livro com ID {book_id} não encontrado.",
                        status_code=404,
                    )

                cursor.execute(DELETE_BOOK, (book_id,))

        connection.close()

        return create_response(
            message=f"Livro com ID {book_id} foi excluído com sucesso.", status_code=200
        )
    except Exception as e:
        return create_response(status_error=True, messageError=e)
