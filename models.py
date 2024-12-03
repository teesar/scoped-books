from sqlalchemy import Boolean, Float, Numeric, ForeignKey, Integer, String, DECIMAL, DateTime
from sqlalchemy.orm import mapped_column, relationship
from db import db

class Book(db.Model):
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    title = mapped_column(String)
    price = mapped_column(DECIMAL(10, 2))
    available = mapped_column(Integer, default=0)
    rating = mapped_column(Integer)
    upc = mapped_column(String, unique=True)
    url = mapped_column(String)
    category_id = mapped_column(Integer, ForeignKey("category.id"))
    category = relationship("Category", back_populates="books")
    rentals = relationship("BookRental", back_populates="book")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "price": self.price,
            "available": self.available,
            "rating": self.rating,
            "upc": self.upc,
            "url": self.url,
            "category": self.category.name,
        }
    
class Category(db.Model):
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String, unique=True)
    books = relationship("Book", back_populates="category")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name
        }

class User(db.Model):
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    name = mapped_column(String)
    rented = relationship("BookRental", back_populates="user")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name
        }

class BookRental(db.Model):
    id = mapped_column(Integer, primary_key=True)
    user_id = mapped_column(Integer, ForeignKey("user.id"))
    book_id = mapped_column(Integer, ForeignKey("book.id"))
    rented = mapped_column(DateTime(timezone=True), nullable=False)
    returned = mapped_column(DateTime(timezone=True), nullable=True)
    user = relationship("User", back_populates="rented")
    book = relationship("Book", back_populates="rentals")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user.id,
            "book_id": self.book.id,
            "rented": self.rented,
            "returned": self.returned,
        }

