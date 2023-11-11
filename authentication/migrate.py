from flask import Flask
from configuration import Configuration
from flask_migrate import Migrate, init, migrate, upgrade, stamp
from models import database, Role, UserRole, User
from sqlalchemy_utils import create_database, database_exists
import os

application = Flask(__name__)
application.config.from_object(Configuration)

migrateObject = Migrate(application, database)

done = False
while (not done):
    try:
        if (not database_exists(application.config["SQLALCHEMY_DATABASE_URI"])):
            create_database(application.config["SQLALCHEMY_DATABASE_URI"])

        database.init_app(application)

        with application.app_context() as context:
            try:
                if (not os.path.isdir("migrations")):
                    init()
            except Exception as exception:
                print(exception)

            stamp()
            migrate(message = "Authentication migration")
            upgrade()

            ownerRoleExists = Role.query.filter(Role.name == "vlasnik").first()
            buyerRoleExists = Role.query.filter(Role.name == "kupac").first()
            deliveryRoleExists = Role.query.filter(Role.name == "kurir").first()

            if (not ownerRoleExists):
                ownerRole = Role(name = "vlasnik")
                database.session.add(ownerRole)
                database.session.commit()

            if (not buyerRoleExists):
                userRole = Role(name = "kupac")
                database.session.add(userRole)
                database.session.commit()

            if (not deliveryRoleExists):
                userRole = Role(name = "kurir")
                database.session.add(userRole)
                database.session.commit()

            ownerExists = User.query.filter(User.email == "onlymoney@gmail.com").first()

            if (not ownerExists):
                owner = User(
                    forename = "Scrooge",
                    surname = "McDuck",
                    email = "onlymoney@gmail.com",
                    password = "evenmoremoney",
                )

                database.session.add(owner)
                database.session.commit()

                userRole = UserRole(
                    userId = owner.id,
                    roleId = ownerRole.id
                )

                database.session.add(userRole)
                database.session.commit()

            done = True
    except Exception as exception:
        print(exception)