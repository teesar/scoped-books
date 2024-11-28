from flask import Flask, render_template, request, jsonify
from models import Category, Book, User, BookRental
# from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy.orm import DeclarativeBase
from pathlib import Path
from db import db
from sqlalchemy import select
from datetime import datetime, timedelta

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.instance_path = Path("data").resolve()
db.init_app(app)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/users")
def users():
    statement = db.select(User).order_by(User.name)
    results = db.session.execute(statement).scalars()
    return render_template("users.html", results=results)

@app.route("/categories")
def categories():
    statement = db.select(Category).order_by(Category.name)
    results = db.session.execute(statement).scalars()
    return render_template("categories.html", results=results)

@app.route("/categories/<string:name>")
def category_detail(name):
    statement = db.select(Book).where(Book.category.has(Category.name.ilike(name)))
    results = db.session.execute(statement).scalars()
    if not results:
        return "CATEGORY NOT FOUND!", 404
    return render_template("category_detail.html", results=results, heading=name)

@app.route("/books")
def books():
    statement = db.select(Book).order_by(Book.title)
    results = db.session.execute(statement).scalars()
    return render_template("books.html", results=results)

@app.route("/book/<int:id>")
def book(id):
    statement = db.select(Book).where(Book.id == id)
    result = db.session.execute(statement).scalar()
    if not result:
        return f"BOOK ID:{id} NOT FOUND!", 404
    return render_template("book.html", result=result)

@app.route("/user/<int:id>")
def user(id):
    statement = db.select(User).where(User.id == id)
    result = db.session.execute(statement).scalar()
    if not result:
        return f"USER ID:{id} NOT FOUND!", 404
    return render_template("user.html", result=result)

@app.route("/available")
def available():    
    statement = db.select(Book).where(Book.available > 0)
    books = db.session.execute(statement).scalars()
    return render_template("available.html", books=books)

@app.route("/rented")
def rented():
    statement = db.select(BookRental).where(BookRental.returned == None)
    results = db.session.execute(statement).scalars()
    return render_template("rented.html", results=results)

@app.route("/api/books")
def get_books():
    statement = db.select(Book)
    books= db.session.execute(statement).scalars()
    book_list = []
    for book in books:
        book_list.append(book.to_dict())
    return jsonify(book_list)

@app.route("/api/books/<int:id>")
def get_book(id):
    statement = db.select(Book).where(Book.id == id)
    book = db.session.execute(statement).scalar()
    if not book:
        return f"BOOK ID:{id} NOT FOUND!", 404
    book = book.to_dict()
    return jsonify(book)

@app.route("/api/books/<int:id>/rent", methods=["POST"])
def rent_book(id):
    data = request.get_json()
    copy = data.get("copy")
    user = data.get("user_id")
    statement = db.select(Book).where(Book.id == id)
    book = db.session.execute(statement).scalar()
    rented= datetime.now()
    expected = rented + timedelta(days=7)
    if not rented:
        return "That book doesn't exist", 400
    new_rental = BookRental(user_id = user, book_id = book.id, rented = rented, expected = expected, copy_id=copy)
    db.session.add(new_rental)
    db.session.commit()
    return jsonify(new_rental.to_dict())


@app.route("/api/books", methods=["POST"])
def create_book():
    data = request.get_json()
    required_fields = ["available", "category", "price", "rating", "title", "upc", "url"]
    for field in required_fields:
        if field not in data:
            return "Missing field", 400

    available = data.get("available")
    category = data.get("category")
    category_statement = db.select(Category).where(Category.name == category)
    category_check = db.session.execute(category_statement).scalar()
    if not category_check:
        new_category = Category(name=category)
        db.session.add(new_category)
        db.session.flush()
    category_id_statement = db.select(Category.id).where(Category.name == category)
    category_id = db.session.execute(category_id_statement).scalar()

    price = data.get("price")
    rating = data.get("rating")
    title = data.get("title")
    upc = data.get("upc")
    url = data.get("url")
    upc_statement = db.select(Book).where(Book.upc == upc)
    upc_check = db.session.execute(upc_statement).scalar()
    if upc_check:
        return "A book with that UPC already exists", 400

    if available <= 0 or type(available) != int:
        return "Available must be a positive integer", 400
    if type(price) != float or price <= 0:
        return "Price must be a positive float", 400
    if type(rating) != int or 1 > rating > 5:
        return "Rating must be an integer between 1 and 5", 400
    if type(title) != str or title == "":
        return "Title must be a non-empty string", 400
    if type(category) != str or category == "":
        return "Category must be a non-empty string", 400
    if type(upc) != str or upc == "":
        return "UPC must be a non-empty string", 400
    if type(url) != str or url == "":
        return "URL must be a non-empty string", 400

    # is_positive_number = lambda num: isinstance(num, (int, float)) and num >= 0
    # is_non_empty_string = lambda s: isinstance(s, str) and len(s) > 0
    # is_valid_rating = lambda num: isinstance(num, int) and 1 <= num <= 5
    # if is_positive_number(available) and is_positive_number(price) and is_non_empty_string(title) and is_valid_rating(rating) and is_non_empty_string(category) and is_non_empty_string(upc) and is_non_empty_string(url):
    #     pass
    # else:
    #     return "Invalid value", 400

    book = Book(available=available, category_id=category_id, price=price, rating=rating, title=title, upc=upc, url=url)
    db.session.add(book)
    db.session.commit()

    return jsonify(book.to_dict())






if __name__ == "__main__":
    app.run(debug=True, port=8888)