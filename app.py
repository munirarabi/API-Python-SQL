import os
import psycopg2
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
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

DELETE_BOOKS = """DELETE FROM books WHERE id IN %s;"""

UPDATE_BOOK = """UPDATE books SET title = %s, author = %s WHERE id = %s;"""

CREATE_PROCEDURE_DELETE_ALL_BOOKS = """CREATE OR REPLACE FUNCTION spDeleteAllBooks()
RETURNS void AS $$
BEGIN
    DELETE FROM books;
END;
$$ LANGUAGE plpgsql;
"""


load_dotenv()

app = Flask(__name__)

CORS(app)

url = os.getenv("DATABASE_URL")


def dataResponse(
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

        if not books_list:
            return dataResponse(
                data=0,
                message="Nenhum livro cadastrado.",
                status_code=200,
            )

        return dataResponse(data=books_list, message="Requisição OK", status_code=200)
    except Exception as e:
        return dataResponse(status_error=True, messageError=e)


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
            return dataResponse(
                status_error=True,
                message=f"Livro com ID {book_id} não encontrado.",
                status_code=404,
            )

        book_dict = {"id": book[0], "title": book[1], "author": book[2]}

        return dataResponse(data=book_dict, message="Requisição OK", status_code=200)
    except Exception as e:
        return dataResponse(status_error=True, messageError=e)


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

        return dataResponse(
            data=bookInserted, message=f"Book {titleInserted} created.", status_code=201
        )
    except Exception as e:
        return dataResponse(status_error=True, messageError=e)


@app.route("/api/books/<int:book_id>", methods=["PUT"])
def editBook(book_id):
    try:
        data = request.get_json()

        title = data.get("title")
        author = data.get("author")

        if title is None or author is None:
            return dataResponse(
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
                    return dataResponse(
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

        return dataResponse(
            message=f"Livro com ID {book_id} foi atualizado com sucesso.",
            status_code=200,
        )
    except Exception as e:
        return dataResponse(status_error=True, messageError=e)


@app.route("/api/books/<int:book_id>", methods=["DELETE"])
def deleteBook(book_id):
    try:
        connection = psycopg2.connect(url)

        with connection:
            with connection.cursor() as cursor:
                cursor.execute(SELECT_BOOK_BY_ID, (book_id,))

                existing_book = cursor.fetchone()

                if existing_book is None:
                    return dataResponse(
                        status_error=True,
                        message=f"Livro com ID {book_id} não encontrado.",
                        status_code=404,
                    )

                cursor.execute(DELETE_BOOK, (book_id,))

        connection.close()

        return dataResponse(
            message=f"Livro com ID {book_id} foi excluído com sucesso.", status_code=200
        )
    except Exception as e:
        return dataResponse(status_error=True, messageError=e)


@app.route("/api/books/delete", methods=["DELETE"])
def deleteBooks():
    try:
        data = request.get_json()

        if "book_ids" not in data:
            return dataResponse(
                status_error=True,
                message="Os IDs dos livros a serem excluídos devem ser fornecidos.",
                status_code=400,
            )

        book_ids = data["book_ids"]

        if not book_ids:
            return dataResponse(
                status_error=True,
                message="A lista de IDs de livros a serem excluídos está vazia.",
                status_code=400,
            )

        connection = psycopg2.connect(url)

        with connection:
            with connection.cursor() as cursor:
                cursor.execute(DELETE_BOOKS, (tuple(book_ids),))

        connection.close()

        return dataResponse(
            message=f"{len(book_ids)} livros foram excluídos com sucesso.",
            status_code=200,
        )
    except Exception as e:
        return dataResponse(status_error=True, messageError=e)


@app.route("/api/books/delete-all-books", methods=["DELETE"])
def deleteAllBooks():
    try:
        connection = psycopg2.connect(url)

        with connection:
            with connection.cursor() as cursor:
                cursor.callproc("spDeleteAllBooks")

        connection.close()

        return dataResponse(
            message="Todos os livros foram excluídos com sucesso.", status_code=200
        )
    except Exception as e:
        return dataResponse(status_error=True, messageError=e)
