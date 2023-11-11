from flask import Flask, request, Response, jsonify
from models import User, database, UserRole
from configuration import Configuration
from sqlalchemy import and_
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, get_jwt_identity, verify_jwt_in_request
from rightAccess import roleCheck
import re

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)

def passwordCheck(password):
    if (len(password) < 8):
        return False
    # if ((re.search("[0-9]", password) is None) or (re.search("[a-z]",password) is None)) or (re.search("[A-Z]", password) is None):
    #     return False
    return True

@application.route("/register_customer", methods = ["POST"])
def registerCustomer():
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0
    foreameEmpty = len(forename) == 0
    surnameEmpty = len(surname) == 0

    if (foreameEmpty):
        return jsonify(message = "Field forename is missing."), 400
    if (surnameEmpty):
        return jsonify(message = "Field surname is missing."), 400
    if (emailEmpty):
        return jsonify(message = "Field email is missing."), 400
    if (passwordEmpty):
        return jsonify(message = "Field password is missing."), 400

    emailRegex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if (not re.fullmatch(emailRegex, email)):
        return jsonify(message = "Invalid email."), 400

    if (not passwordCheck(password)):
        return jsonify(message = "Invalid password."), 400

    user = User.query.filter(User.email == email).first()
    if (user):
        return jsonify(message = "Email already exists."), 400

    user = User(forename = forename, surname = surname, email = email, password = password)
    database.session.add(user)
    database.session.commit()

    userRole = UserRole(userId = user.id, roleId = 2)

    database.session.add(userRole)
    database.session.commit()

    return Response(status = 200)

@application.route("/register_courier", methods = ["POST"])
def registerCourier():
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0
    foreameEmpty = len(forename) == 0
    surnameEmpty = len(surname) == 0

    if (foreameEmpty):
        return jsonify(message = "Field forename is missing."), 400
    if (surnameEmpty):
        return jsonify(message = "Field surname is missing."), 400
    if (emailEmpty):
        return jsonify(message = "Field email is missing."), 400
    if (passwordEmpty):
        return jsonify(message = "Field password is missing."), 400

    emailRegex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if (not re.fullmatch(emailRegex, email)):
        return jsonify(message = "Invalid email."), 400

    if (not passwordCheck(password)):
        return jsonify(message = "Invalid password."), 400

    user = User.query.filter(User.email == email).first()
    if (user):
        return jsonify(message = "Email already exists."), 400

    user = User(forename = forename, surname = surname, email = email, password = password)
    database.session.add(user)
    database.session.commit()

    userRole = UserRole(userId = user.id, roleId = 3)

    database.session.add(userRole)
    database.session.commit()

    return Response(status = 200)

@application.route("/login", methods = ["POST"])
def login():
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    emailEmpty = len(email) == 0
    passwordEmpty = len(password) == 0

    if (emailEmpty):
        return jsonify(message = "Field email is missing."), 400
    if (passwordEmpty):
        return jsonify(message = "Field password is missing."), 400

    emailRegex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if (not re.fullmatch(emailRegex, email)):
        return jsonify(message = "Invalid email."), 400

    user = User.query.filter(and_(User.email == email, User.password == password)).first()

    if (not user):
        return jsonify(message = "Invalid credentials."), 400

    additionalClaims = {
        "forename": user.forename,
        "surname": user.surname,
        "email": user.email,
        "password": user.password,
        "roles": [str(role) for role in user.roles]
    }

    accessToken = create_access_token(identity = user.email, additional_claims = additionalClaims)
    # refreshToken = create_refresh_token(identity = user.email, additional_claims = additionalClaims)

    return jsonify(accessToken = accessToken)

@application.route("/check", methods = ["POST"])
@jwt_required()
def check():
    return "Token is valid!"

# @application.route("/refresh", methods = ["POST"])
# @jwt_required(refresh = True)
# def refresh():
#     identity = get_jwt_identity()
#     refreshClaims = get_jwt()
#
#     additionalClaims = {
#         "forename": refreshClaims["forename"],
#         "surname": refreshClaims["surname"],
#         "email": refreshClaims["email"],
#         "password": refreshClaims["password"],
#         "isCustomer": refreshClaims["isCustomer"],
#         "roles": refreshClaims["roles"]
#     }
#
#     return jsonify(accessToken = create_access_token(identity = identity, additional_claims = additionalClaims)), 200

@application.route("/delete", methods = ["POST"])
def deleteUser():

    verify_jwt_in_request()
    claims = get_jwt()

    email = claims["email"]

    user = User.query.filter(User.email == email).first()

    if (not user):
        return jsonify(message = "Unknown user."), 400

    UserRole.query.filter(UserRole.userId == user.id).delete()
    User.query.filter(User.email == email).delete()

    database.session.commit()

    return Response(status = 200)

    # emailEmpty = len(email) == 0
    #
    # if (emailEmpty):
    #     return jsonify(message = "Field email is missing."), 400
    #
    # emailRegex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    # if (not re.fullmatch(emailRegex, email)):
    #     return jsonify(message = "Invalid email."), 400

@application.route("/", methods = ["GET"])
def index():
    return "Hello authentication!"

if (__name__ == "__main__"):
    database.init_app(application)
    application.run(debug = True, host = "0.0.0.0", port = 5000)