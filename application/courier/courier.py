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
import web3
from web3 import Web3
from web3 import Account

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)

web3 = Web3(Web3.HTTPProvider("http://ganache-cli:8545"))

def read_file ( path ):
    with open ( path, "r" ) as file:
        return file.read ( )

keys = None
with open ( "vlasnik.json", "r" ) as file:
    keys = json.loads ( file.read ( ) )

@application.route("/orders_to_deliver", methods = ["GET"])
@roleCheck (role = "kurir")
def ordersToDeliver():
    orders = Order.query.join(OrderStatus, Order.id == OrderStatus.orderId).join(Status, OrderStatus.statusId == Status.id).filter(Status.name == "CREATED").group_by(Order.id).with_entities(Order.id, Order.email).all()

    orders_result = []
    for order in orders:
        orders_result.append({
            "id": order.id,
            "email": order.email
        })

    return Response(json.dumps({"orders" : orders_result}), status = 200)

@application.route("/pick_up_order", methods = ["POST"])
@roleCheck (role = "kurir")
def pickUpOrder():
    id = request.json.get("id", "")
    address = request.json.get("address", "")

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
    if s.name != "CREATED":
        return Response(json.dumps({"message": "Invalid order id."}), status = 400)
    if address == "":
        return Response(json.dumps({"message": "Missing address."}), status = 400)
    try:
        if(not web3.is_address(address)):
            return Response(json.dumps({"message": "Invalid address."}), status = 400)
    except ValueError:
        return Response(json.dumps({"message": "Invalid address."}), status = 400)
    contractDB = Contract.query.filter(Contract.orderId == id).first()
    abi = read_file("./Contract.abi")
    contract = web3.eth.contract(address = contractDB.address, abi = abi)
    totalAmount = contract.functions.totalAmount().call()
    if totalAmount <= 0:
        return Response(json.dumps({"message": "Transfer not complete."}), status = 400)

    owner_address = web3.to_checksum_address("0x4b43B80F92ebfd069647B4695Bef5cff4c595ce1")
    contract.functions.setCourier(address).transact({'from': owner_address})

    o.statusId = 2
    database.session.commit()

    return Response(status = 200)

@application.route("/", methods = ["GET"])
def index():
    return "Hello courier!"

if (__name__ == "__main__"):
    database.init_app(application)
    application.run(debug = True, host = "0.0.0.0", port = 5003)