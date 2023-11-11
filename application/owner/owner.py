from flask import Flask, request, Response, jsonify
from configuration import Configuration
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, get_jwt_identity
from models import database, Product, Category, ProductCategory, OrderProduct, Order, OrderStatus, Status
from sqlalchemy import func, case
from rightAccess import roleCheck
import csv
import io
import json
from sqlalchemy import and_

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)

@application.route("/update", methods = ["POST"])
@roleCheck(role = "vlasnik")
def update():
    try:
        file = request.files["file"]
    except KeyError:
        return jsonify(message = "Field file is missing."), 400

    content = file.stream.read().decode("utf-8")
    stream = io.StringIO(content)
    reader = csv.reader(stream)

    products = []
    rowNumber = 0
    for row in reader:
        if (len(row) != 3):
            return jsonify(message = f"Incorrect number of values on line {rowNumber}."), 400

        categoriesDelimiter = row[0]
        categories = categoriesDelimiter.split("|")
        name = row[1]
        price = row[2]

        try:
            price = float(price)
        except Exception:
            return jsonify(message = f"Incorrect price on line {rowNumber}."), 400
        if (price <= 0):
            return jsonify(message = f"Incorrect price on line {rowNumber}."), 400

        product = Product.query.filter(Product.name == name).first()
        if (product):
            return jsonify(message = f"Product {name} already exists."), 400

        product_data = {
            "categories": categories,
            "name": name,
            "price": price,
        }
        products.append(product_data)

        rowNumber += 1

    for product_data in products:
        p = Product(
            name = product_data['name'],
            price = product_data['price'],
        )

        for category_name in product_data['categories']:
            category = Category.query.filter_by(name = category_name).first()
            if not category:
                category = Category(name=category_name)
                database.session.add(category)
                database.session.commit()

            p.categories.append(category)

        database.session.add(p)
        database.session.commit()

    return Response(status = 200)

@application.route("/product_statistics", methods = ["GET"])
@roleCheck(role = "vlasnik")
def productStatistics():
    statistics = []
    complete = "COMPLETE"
    pending = "PENDING"
    created = "CREATED"

    result = OrderProduct.query.outerjoin(Order, OrderProduct.orderId == Order.id).outerjoin(OrderStatus, Order.id == OrderStatus.orderId).outerjoin(Status, Status.id == OrderStatus.statusId).with_entities(OrderProduct.productId,func.sum(case([(Status.name.like(f"%{complete}%"), OrderProduct.quantity)], else_=0)),func.sum(case([(Status.name.like(f"%{pending}%")  | Status.name.like(f"%{created}%"), OrderProduct.quantity)], else_=0))).group_by(OrderProduct.productId).all()
    for product in result:
        statistics.append({
            "name": Product.query.filter_by(id = product[0]).first().name,
            "sold": int(product[1]),
            "waiting": int(product[2])
        })

    return Response(json.dumps({"statistics" : statistics}), status = 200)

@application.route("/category_statistics", methods = ["GET"])
@roleCheck(role = "vlasnik")
def categoryStatistics():
    statistics = []

    # total_requested = func.coalesce(func.sum(OrderProduct.quantity), 0)
    # categories = Category.query.outerjoin(ProductCategory, Category.id == ProductCategory.categoryId).outerjoin(OrderProduct, ProductCategory.productId == OrderProduct.productId).group_by(Category.id).order_by(total_requested.desc()).order_by(Category.name).with_entities(Category.name).all()

    categories = Category.query.outerjoin(ProductCategory, Category.id == ProductCategory.categoryId).outerjoin(OrderProduct, ProductCategory.productId == OrderProduct.productId).outerjoin(Order, OrderProduct.orderId == Order.id).outerjoin(OrderStatus, Order.id == OrderStatus.orderId).outerjoin(Status, Status.id == OrderStatus.statusId).group_by(Category.id).with_entities(Category.name,func.sum(case([(Status.name == 'complete', OrderProduct.quantity)], else_=0))).order_by(func.sum(case([(Status.name == 'complete', OrderProduct.quantity)], else_=0)).desc()).order_by(Category.name).all()

    for category in categories:
        statistics.append(category[0])
    return Response(json.dumps({"statistics" : statistics}), status = 200)

@application.route("/", methods = ["GET"])
def index():
    return "Hello owner!"

if (__name__ == "__main__"):
    database.init_app(application)
    application.run(debug = True, host = "0.0.0.0", port = 5001)