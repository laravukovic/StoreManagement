from datetime import datetime
from operator import and_
from flask import Flask, request, Response, jsonify
from configuration import Configuration
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, get_jwt_identity, verify_jwt_in_request
from models import database, Product, Category, ProductCategory, Order, OrderStatus, OrderProduct, Status, Contract
from sqlalchemy import func
from rightAccess import roleCheck
import csv
import io
import json
from web3 import Web3
from web3 import Account
import logging

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)

# Web3 connection
web3 = Web3(Web3.HTTPProvider("http://ganache-cli:8545"))

# # Set the logging level
# application.logger.setLevel(logging.DEBUG)
#
# # Create a file handler to save log messages to a file
# file_handler = logging.FileHandler('app.log')
# file_handler.setLevel(logging.DEBUG)
#
# # Create a formatter to define the log message format
# formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# file_handler.setFormatter(formatter)
#
# # Add the file handler to the app's logger
# application.logger.addHandler(file_handler)

def read_file ( path ):
    with open ( path, "r" ) as file:
        return file.read ( )

@application.route("/search", methods=["GET"])
@roleCheck (role = "kupac")
def search():
    name = request.args.get("name")
    category = request.args.get("category")

    products = []
    categories = []
    if (name and category):
        products = Product.query.join(ProductCategory).join(Category).filter(and_(Category.name.like(f"%{category}%"), Product.name.like(f"%{name}%")))
    elif (name and category == None):
        products = Product.query.filter(Product.name.like(f"%{name}%"))
    elif (name == None and category):
        products = Product.query.join(ProductCategory).join(Category).filter(Category.name.like(f"%{category}%"))
    else:
        products = Product.query.all()

    search_products = []
    for product in products:
        product_categories = []
        for product_cat in product.categories:
            product_categories.append(product_cat.name)
            if product_cat.name not in categories:
                categories.append(product_cat.name)
        search_products.append({
            "categories": product_categories,
            "id": product.id,
            "name": product.name,
            "price": product.price
        })
    return Response(json.dumps({"categories": categories, "products": search_products}), status = 200)

@application.route("/order", methods=["POST"])
@roleCheck (role = "kupac")
def order():
    requests = request.json.get("requests", "")
    address = request.json.get("address", "")

    if len(requests) == 0:
        return Response(json.dumps({"message": "Field requests is missing."}), status = 400)

    rowNumber = 0
    for r in requests:
        id = r.get("id", "")
        if id == "":
            return Response(json.dumps({"message": f"Product id is missing for request number {rowNumber}."}), status = 400)
        number = r.get("quantity", "")
        if number== "":
            return Response(json.dumps({"message": f"Product quantity is missing for request number {rowNumber}."}), status = 400)
        try:
            id = int(id)
        except ValueError:
            return Response(json.dumps({"message": f"Invalid product id for request number {rowNumber}."}), status = 400)
        if(int(id) <0):
            return Response(json.dumps({"message": f"Invalid product id for request number {rowNumber}."}), status = 400)
        try:
            number = int(number)
        except ValueError:
            return Response(json.dumps({"message": f"Invalid product quantity for request number {rowNumber}."}), status = 400)
        if(int(number) <=0 ):
            return Response(json.dumps({"message": f"Invalid product quantity for request number {rowNumber}."}), status = 400)

        product = Product.query.filter(Product.id == id).first()
        if product is None:
            return Response(json.dumps({"message": f"Invalid product for request number {rowNumber}."}), status = 400)
        rowNumber += 1

    if len(address) == 0:
        return Response(json.dumps({"message": "Field address is missing."}), status = 400)

    try:
        if(not web3.is_address(address)):
            return Response(json.dumps({"message": "Invalid address."}), status = 400)
    except ValueError:
        return Response(json.dumps({"message": "Invalid address."}), status = 400)

    order = Order(total = 0, time = datetime.now().isoformat(), email = get_jwt_identity())
    database.session.add(order)
    database.session.commit()

    for r in requests:
        product = Product.query.filter(Product.id == r['id']).first()
        order.total += float(product.price) * float(r['quantity'])
        order_product = OrderProduct(productId = r["id"], orderId = order.id, quantity = r["quantity"])

        database.session.add(order_product)
        database.session.commit()

    status = OrderStatus(orderId = order.id, statusId = 1)
    database.session.add(status)
    database.session.commit()

    # Compile the contract
    bytecode = read_file("./Contract.bin")
    abi = read_file("./Contract.abi")
    contract = web3.eth.contract(bytecode = bytecode, abi = abi)

    tx_hash = contract.constructor(address).transact({"from": web3.eth.accounts[0]})
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    contract_address = tx_receipt["contractAddress"]

    db_contract = Contract(orderId = order.id, address = contract_address)
    database.session.add(db_contract)
    database.session.commit()

    return Response(json.dumps({"id": order.id}), status = 200)

@application.route("/status", methods=["GET"])
@roleCheck (role = "kupac")
def status():
    user = get_jwt_identity()
    orders = Order.query.filter(Order.email == user).all()

    orders_result = []
    for order in orders:
        products_result = []
        for product in order.products:
            categories_result = []
            for category in product.categories:
                categories_result.append(category.name)
            product_order = OrderProduct.query.join(Order).filter(and_(Order.id == order.id, OrderProduct.productId == product.id)).first()
            products_result.append({
                "categories" : categories_result,
                "name" : product.name,
                "price" : product.price,
                "quantity" : product_order.quantity
            })

        o = OrderStatus.query.filter(OrderStatus.orderId == order.id).first()
        s = Status.query.filter(Status.id == o.statusId).first()

        orders_result.append({
            "products": products_result,
            "price": order.total,
            "status": s.name,
            "timestamp": str(order.time)
        })

    return jsonify(orders = orders_result)

@application.route("/delivered", methods=["POST"])
@roleCheck (role = "kupac")
def delivered():
    id = request.json.get("id", "")
    keys = request.json.get("keys", "")
    passphrase = request.json.get("passphrase", "")

    if id == "":
        return Response(json.dumps({"message": "Missing order id."}), status = 400)
    try:
        id = int(id)
    except ValueError:
        return Response(json.dumps({"message": "Invalid order id."}), status = 400)
    if(int(id) <0):
        return Response(json.dumps({"message": "Invalid order id."}), status = 400)
    order = Order.query.filter(Order.id == id).first()
    if order is None:
        return Response(json.dumps({"message": "Invalid order id."}), status = 400)
    o = OrderStatus.query.filter(OrderStatus.orderId == id).first()
    s = Status.query.filter(Status.id == o.statusId).first()
    if s.name != "PENDING":
        return Response(json.dumps({"message": "Invalid order id."}), status = 400)
    if keys == "":
        return Response(json.dumps({"message": "Missing keys."}), status = 400)
    if passphrase == "":
        return Response(json.dumps({"message": "Missing passphrase."}), status = 400)
    if len(passphrase) == 0:
        return Response(json.dumps({"message": "Missing passphrase."}), status = 400)
    if isinstance(keys, dict):
        a = keys["address"]
    else:
        try:
            keys_dict = json.loads(keys)
            a = keys_dict["address"]
        except json.JSONDecodeError as e:
            return Response(json.dumps({"message": "Invalid customer account."}), status=400)
    try:
        address = web3.to_checksum_address(a)
        private_key = Account.decrypt(keys, passphrase).hex()
    except ValueError:
        return Response(json.dumps({"message": "Invalid credentials."}), status = 400)
    contractDB = Contract.query.filter(Contract.orderId == id).first()
    abi = read_file("./Contract.abi")
    contract = web3.eth.contract(address = contractDB.address, abi = abi)
    try:
        if(not web3.is_address(address)):
            return Response(json.dumps({"message": "Invalid customer account."}), status = 400)
    except ValueError:
        return Response(json.dumps({"message": "Invalid customer account."}), status = 400)
    customer = contract.functions.getCustomerAddress().call()
    customer_address = web3.to_checksum_address(customer)
    if customer_address != address:
        return Response(json.dumps({"message": "Invalid customer account."}), status = 400)
    totalAmount = contract.functions.totalAmount().call()
    if totalAmount <= 0:
        return Response(json.dumps({"message": "Transfer not complete."}), status = 400)
    if s.name != "PENDING":
        return Response(json.dumps({"message": "Delivery not complete."}), status = 400)

    contract.functions.distributeFunds().transact({"from": address})

    o.statusId = 3
    database.session.commit()

    return Response(status = 200)

@application.route("/pay", methods = ["POST"])
@roleCheck (role = "kupac")
def pay():
    id = request.json.get("id", "")
    keys = request.json.get("keys", "")
    passphrase = request.json.get("passphrase", "")

    if id == "":
        return Response(json.dumps({"message": "Missing order id."}), status = 400)
    try:
        id = int(id)
    except ValueError:
        return Response(json.dumps({"message": "Invalid order id."}), status = 400)
    if(int(id) <0):
        return Response(json.dumps({"message": "Invalid order id."}), status = 400)
    order = Order.query.filter(Order.id == id).first()
    if order is None:
        return Response(json.dumps({"message": "Invalid order id."}), status = 400)
    if keys == "":
        return Response(json.dumps({"message": "Missing keys."}), status = 400)
    if passphrase == "":
        return Response(json.dumps({"message": "Missing passphrase."}), status = 400)
    if len(passphrase) == 0:
        return Response(json.dumps({"message": "Missing passphrase."}), status = 400)
    if isinstance(keys, dict):
        a = keys["address"]
    else:
        keys_dict = json.loads(keys)
        a = keys_dict["address"]
    try:
        address = web3.to_checksum_address(a)
        private_key = Account.decrypt(keys, passphrase).hex()
    except ValueError:
        return Response(json.dumps({"message": "Invalid credentials."}), status = 400)
    contractDB = Contract.query.filter(Contract.orderId == id).first()
    abi = read_file("./Contract.abi")
    contract = web3.eth.contract(address = contractDB.address, abi = abi)
    if(order.total > web3.eth.get_balance(address)):
        return Response(json.dumps({"message": "Insufficient funds."}), status = 400)
    totalAmount = contract.functions.totalAmount().call()
    if totalAmount > 0:
        return Response(json.dumps({"message": "Transfer already complete."}), status = 400)

    value_in_wei = web3.to_wei(order.total, "wei")
    contract.functions.transferFunds().transact({"from": address, "value": value_in_wei})

    # o = OrderStatus.query.filter(OrderStatus.orderId == id).first()
    # o.statusId = 3
    # database.session.commit()

    return Response(status = 200)

@application.route("/", methods = ["GET"])
def index():
    return "Hello customer!"

if (__name__ == "__main__"):
    database.init_app(application)
    application.run(debug = True, host = "0.0.0.0", port = 5002)