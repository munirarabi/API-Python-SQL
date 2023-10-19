import os
import psycopg2
from dotenv import load_dotenv
from flask import Flask, request
from datetime import datetime, timezone

CREATE_ROOMS_TABLE = (
    "CREATE TABLE IF NOT EXISTS rooms (id SERIAL PRIMARY KEY, name TEXT);"
)
CREATE_TEMPS_TABLE = """CREATE TABLE IF NOT EXISTS temperatures (room_id INTEGER, temperature REAL, 
                        date TIMESTAMP, FOREIGN KEY(room_id) REFERENCES rooms(id) ON DELETE CASCADE);"""

INSERT_ROOM_RETURN_ID = "INSERT INTO rooms (name) VALUES (%s) RETURNING id;"
INSERT_TEMP = (
    "INSERT INTO temperatures (room_id, temperature, date) VALUES (%s, %s, %s);"
)

GLOBAL_NUMBER_OF_DAYS = """SELECT AVG(temperature) as average FROM temperatures;"""
GLOBAL_AVG = """SELECT AVG(temperature) as average FROM temperatures;"""

load_dotenv()

app = Flask(__name__)
url = os.getenv("DATABASE_URL")


@app.post("/api/room")
def create_room():
    data = request.get_json()
    name = data["name"]
    connection = psycopg2.connect(url)
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_ROOMS_TABLE)
            cursor.execute(INSERT_ROOM_RETURN_ID, (name,))
            room_id = cursor.fetchone()[0]

    connection.close()

    return {"id": room_id, "message": f"Room {name} created."}, 201


@app.post("/api/temperature")
def add_temp():
    data = request.get_json()
    temperature = data["temperature"]
    room_id = data["room"]
    try:
        date = datetime.strptime(data["dae"], "%m-%d-%Y %H:%M:%S")
    except KeyError:
        date = datetime.now(timezone.utc)

    connection = psycopg2.connect(url)

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_TEMPS_TABLE)
            cursor.execute(INSERT_TEMP, (room_id, temperature, date))

    connection.close()

    return {"message": "Temperature added."}, 201


@app.get("/api/average")
def get_global_avg():

    connection = psycopg2.connect(url)

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(GLOBAL_AVG)
            average = cursor.fetchone()[0]
            cursor.execute(GLOBAL_NUMBER_OF_DAYS)
            days = cursor.fetchone()[0]

    connection.close()

    return {"average": round(average, 2), "days": days}


# app = Flask(__name__)

# books = [
#     {"id": 1, "title": "Livro 1", "author": "author 1"},
#     {"id": 2, "title": "Livro 2", "author": "author 2"},
#     {"id": 3, "title": "Livro 3", "author": "Autor 3"},
# ]


# @app.route("/books", methods=["GET"])
# def getBooks():
#     return jsonify(books)


# @app.route("/books/<int:id>", methods=["GET"])
# def getBooksById(id):
#     for book in books:
#         if book.get("id") == id:
#             return jsonify(book)

#     abort(404)


# @app.route("/books/<int:id>", methods=["PUT"])
# def editBookById(id):
#     book_edit = request.get_json()
#     for index, book in enumerate(books):
#         if book.get("id") == id:
#             books[index].update(book_edit)
#             return jsonify(books[index])


# @app.route("/books", methods=["POST"])
# def addBook():
#     newBook = request.get_json()
#     books.append(newBook)

#     return jsonify(books)


# @app.route("/books/<int:id>", methods=["DELETE"])
# def removeBook(id):
#     for index, book in enumerate(books):
#         if book.get("id") == id:
#             del books[index]
#             return jsonify(books)


# app.run(port=5000, host="localhost", debug=True)
