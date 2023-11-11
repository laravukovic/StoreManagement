from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy()


class ProductCategory(database.Model):
    __tablename__ = "productcategory"
    id = database.Column(database.Integer, primary_key = True)
    productId = database.Column(database.Integer, database.ForeignKey("products.id", ondelete = "CASCADE"), nullable = False)
    categoryId = database.Column(database.Integer, database.ForeignKey("categories.id", ondelete = "CASCADE"), nullable = False)


class OrderProduct(database.Model):
    __tablename__ = "orderproduct"
    id = database.Column(database.Integer, primary_key = True)
    orderId = database.Column(database.Integer, database.ForeignKey("orders.id", ondelete = "CASCADE"), nullable = False)
    productId = database.Column(database.Integer, database.ForeignKey("products.id", ondelete = "CASCADE"), nullable = False)
    quantity = database.Column(database.Integer, nullable = False)


class Product(database.Model):
    __tablename__ = "products"
    id = database.Column(database.Integer, primary_key = True)
    name = database.Column(database.String(256), nullable = False)
    price = database.Column(database.Float, nullable = False)

    categories = database.relationship("Category", secondary = ProductCategory.__table__, back_populates = "products")
    orders = database.relationship("Order", secondary = OrderProduct.__table__, back_populates = "products")


class Category(database.Model):
    __tablename__ = "categories"
    id = database.Column(database.Integer, primary_key = True)
    name = database.Column(database.String(256), nullable = False)

    products = database.relationship("Product", secondary = ProductCategory.__table__, back_populates = "categories")

class OrderStatus(database.Model):
    __tablename__ = "orderstatus"

    id = database.Column(database.Integer, primary_key = True)
    orderId = database.Column(database.Integer, database.ForeignKey("orders.id", onupdate = "CASCADE", ondelete = "CASCADE"), nullable = False)
    statusId = database.Column(database.Integer, database.ForeignKey("status.id", onupdate = "CASCADE", ondelete = "CASCADE"), nullable = False)


class Status(database.Model):
    __tablename__ = "status"

    id = database.Column(database.Integer, primary_key = True)
    name = database.Column(database.String(256), nullable = False, unique = True)

    orders = database.relationship("Order", secondary = OrderStatus.__table__, back_populates = "status")


class Order(database.Model):
    __tablename__ = "orders"

    id = database.Column(database.Integer, primary_key = True)
    email = database.Column(database.String(256), nullable = False)
    total = database.Column(database.Float, nullable = False)
    time = database.Column(database.TIMESTAMP, nullable = False)

    status = database.relationship("Status", secondary=OrderStatus.__table__, back_populates = "orders")
    products = database.relationship("Product", secondary = OrderProduct.__table__, back_populates = "orders")


class Contract(database.Model):
    __tablename__ = "contracts"

    id = database.Column(database.Integer, primary_key = True)
    orderId = database.Column(database.Integer, database.ForeignKey("orders.id", onupdate = "CASCADE", ondelete = "CASCADE"), nullable = False)
    address = database.Column(database.String(256), nullable = False)
