from flask import Flask, render_template, request, jsonify
from models import Category, Book, User, BookRental
# from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy.orm import DeclarativeBase
from pathlib import Path
from db import db
from sqlalchemy import select, or_
from datetime import datetime, timedelta

# flask app initiation, setting database file to database.db, putting it in directory data
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.instance_path = Path("data").resolve()
db.init_app(app)

# route for home
@app.route("/")
def home():
    return render_template("home.html")

# route for showing all users
@app.route("/users")
def users():
    statement = db.select(User).order_by(User.id)
    results = db.session.execute(statement).scalars()
    return render_template("users.html", results=results)

# route for showing all categories
@app.route("/categories")
def categories():
    statement = db.select(Category).order_by(Category.name)
    results = db.session.execute(statement).scalars()
    return render_template("categories.html", results=results)

# route for showing individual category
@app.route("/categories/<string:name>")
def category_detail(name):
    statement = db.select(Book).where(Book.category.has(Category.name.ilike(name)))
    results = db.session.execute(statement).scalars()
    if not results:
        return "CATEGORY NOT FOUND!", 404
    return render_template("category_detail.html", results=results, heading=name)

# route for showing all books
@app.route("/books")
def books():
    statement = db.select(Book).order_by(Book.title)
    results = db.session.execute(statement).scalars()
    return render_template("books.html", results=results)

# route for showing individual book
@app.route("/book/<int:id>")
def book(id):
    statement = db.select(Book).where(Book.id == id)
    result = db.session.execute(statement).scalar()
    if not result:
        return f"BOOK ID:{id} NOT FOUND!", 404
    return render_template("book.html", result=result)

# route for showing individual user
@app.route("/user/<int:id>")
def user(id):
    statement = db.select(User).where(User.id == id)
    result = db.session.execute(statement).scalar()
    if not result:
        return f"USER ID:{id} NOT FOUND!", 404
    return render_template("user.html", result=result)

# route for showing available books
@app.route("/available")
def available():
    statement = db.select(BookRental.book_id).where(BookRental.returned == None)
    rented_book_ids = [id for id in db.session.execute(statement).scalars()]
    available_books_stmt = db.select(Book).where(Book.id.notin_(rented_book_ids)).order_by(Book.title)
    books = db.session.execute(available_books_stmt).scalars().all()
    return render_template("available.html", books=books)

# route for showing rented books
@app.route("/rented")
def rented():
    statement = db.select(BookRental).where(BookRental.returned == None)
    results = db.session.execute(statement).scalars()
    return render_template("rented.html", results=results)

# api - get all books
@app.route("/api/books")
def get_books():
    statement = db.select(Book)
    books= db.session.execute(statement).scalars()
    book_list = []
    for book in books:
        book_list.append(book.to_dict())
    return jsonify(book_list)

# api - get all users 
@app.route("/api/users")
def get_users():
    statement = db.select(User)
    users = db.session.execute(statement).scalars()
    user_list = []
    for user in users:
        user_list.append(user.to_dict())
    return jsonify(user_list)

# api - get all categories
@app.route("/api/categories")
def get_categories():
    statement = db.select(Category)
    categories = db.session.execute(statement).scalars()
    category_list = []
    for category in categories:
        category_list.append(category.to_dict())
    return jsonify(category_list)

# api - get book
@app.route("/api/books/<int:id>")
def get_book(id):
    statement = db.select(Book).where(Book.id == id)
    book = db.session.execute(statement).scalar()
    if not book:
        return f"BOOK ID:{id} NOT FOUND!", 404
    book = book.to_dict()
    return jsonify(book)

# api - add rental
@app.route("/api/books/<int:id>/rent", methods=["POST"])
def rent_book(id):
    data = request.get_json()
    user = data.get("user_id")
    statement = db.select(Book).where(Book.id == id)
    book = db.session.execute(statement).scalar()
    rented= datetime.now()
    if not rented:
        return "That book doesn't exist", 400
    new_rental = BookRental(user_id = user, book_id = book.id, rented = rented)
    db.session.add(new_rental)
    db.session.commit()
    return jsonify(new_rental.to_dict())

# api - add book
@app.route("/api/books", methods=["POST"])
def create_book():
    # get json from the request
    data = request.get_json()
    # set fields that the json must contain, then iterate and check each exists, return error if not
    required_fields = ["available", "category", "price", "rating", "title", "upc", "url"]
    for field in required_fields:
        if field not in data:
            return "Missing field", 400
        
    available = data.get("available")
    category = data.get("category")
    category_statement = db.select(Category).where(Category.name == category)
    category_check = db.session.execute(category_statement).scalar()
    # if category doesn't exist then add it to the database - flush to add to session but not commit yet
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
    # return error if someone tries to add a book with a upc already in the database
    if upc_check:
        return "A book with that UPC already exists", 400
    
    # slightly convoluted type/value checks
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

# alternative type checks
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

    # returning the object we added as json data to the actor that initiated the process for verification
    return jsonify(book.to_dict())

if __name__ == "__main__":
    app.run(debug=True, port=8888)