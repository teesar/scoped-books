from db import db
from models import Category, Book, User, BookRental
from app import app
import csv
from sqlalchemy import select
import sys
argv = sys.argv
from datetime import datetime, timedelta
from random import random, randint as rndm, choice

# type and acceptable value checks
is_positive_number = lambda num: isinstance(num, (int, float)) and num >= 0
is_non_empty_string = lambda s: isinstance(s, str) and len(s) > 0
is_valid_rating = lambda num: isinstance(num, int) and 1 <= num <= 5

# import users from data/users.csv
def import_users():
    with app.app_context():
        with open("data/users.csv", "r") as file:
            users = csv.DictReader(file)
            for user in users:
                user_obj = User(**user)
                db.session.add(user_obj)
            try:
                db.session.commit()
            except:
                print("Error adding user data")

# import books from data/books.csv
def import_books():
    with app.app_context():
        with open("data/books.csv", "r") as file:
            books = csv.DictReader(file)
            for book in books:
                upc = book.get("upc")
                statement = db.select(Book.upc).where(Book.upc == upc)
                existing_upc = db.session.execute(statement).scalar()
                # if book exists then skip this record
                if existing_upc:
                    print("existing")
                    continue
                title = book.get("title")
                price = book.get("price")
                available = book.get("available")
                rating = book.get("rating")
                url = book.get("url")
                category = book.get("category")
                # convert data types from csv strings 
                try:
                    price = float(price)
                    available = int(available)
                    rating = int(rating)
                except:
                    print("Error: The record you attempted to add failed the type conversion.")
                    print(price, available, rating)
                    continue
                # type and acceptable value check implementation
                if is_positive_number(price) and is_valid_rating(rating) and is_non_empty_string(upc) and is_non_empty_string(title) and is_non_empty_string(url) and is_positive_number(available) and is_non_empty_string(category):
                    pass
                else:
                    print(title, price, upc, rating, category, url)
                    print("Error: The record you attempted to add failed the type and acceptable value check.")
                    continue

                # check if category exists, create it if it doesn't
                statement = db.select(Category).where(Category.name == category)
                category_obj = db.session.execute(statement).scalar()
                if not category_obj:
                    category_obj = Category(name=category)
                    # db.session.add(category_obj)
                    
                
                book_obj = Book(title=title, price=price, upc=upc, available=available, rating=rating, url=url, category=category_obj)
                db.session.add(book_obj)
                try:
                    db.session.commit()
                except:
                    print("Error adding book data")

#  import book rentals from data/bookrentals.csv
def import_rentals():
    with app.app_context():
        with open("data/bookrentals.csv", "r") as file:
            rentals = csv.DictReader(file)
            for rental in rentals:
                book_upc = rental.get("book_upc")
                user_name = rental.get("user_name")
                statement = db.select(User.id).where(User.name == user_name)
                existing_user = db.session.execute(statement).scalar()
                # if user doesn't exist then continue to next iteration of loop
                if not existing_user:
                    continue
                rented = rental.get("rented")
                returned = rental.get("returned")
                # if upc doesn't exist then skip this record
                statement = db.select(Book).where(Book.upc == book_upc)
                existing_book = db.session.execute(statement).scalar()
                if not existing_book:
                    continue
                # compare time/date format in rentals if there are issues
                # will automatically show year-month-day hour:minute if i align command to csv order
                # if csv shows 30/12/2018 05:55:31 - then adjust to "%d/%m/%Y %H:%M:%S"
                if is_non_empty_string(rented):
                    rented_obj = datetime.strptime(rented, "%Y-%m-%d %H:%M")
                if is_non_empty_string(returned):    
                    returned_obj = datetime.strptime(returned, "%Y-%m-%d %H:%M")
                else:
                    returned_obj = None
                # type/acceptable value check for upc and user name before adding rental
                if is_non_empty_string(book_upc) and is_non_empty_string(user_name):
                    book_rental = BookRental(book_id=existing_book.id, user_id=existing_user, rented=rented_obj, returned=returned_obj)
                    db.session.add(book_rental)
            try:
                db.session.commit()
            except:
                print("Error adding rental data.")

def drop_tables():
    with app.app_context():
        db.drop_all()

def create_tables():
    with app.app_context():
        db.create_all()
              
if __name__ == "__main__":
    if len(argv) > 1:
        if argv[1].lower() == "drop":
            drop_tables()
        elif argv[1].lower() == "create":
            create_tables()
        elif argv[1].lower() == "import":
            import_users()
            import_books()
            import_rentals()
        elif argv[1].lower() == "boom":
            drop_tables()
            create_tables()
            import_users()
            import_books()
            import_rentals()




