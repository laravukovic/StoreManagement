from flask import Flask
from flask_migrate import Migrate, migrate, init, upgrade, stamp
from configuration import Configuration
from models import database, Status
from sqlalchemy_utils import database_exists, create_database
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
            migrate(message = "Warehouse migration")
            upgrade()

            createdStatusExists = Status.query.filter(Status.name == "CREATED").first()
            pendingStatusExists = Status.query.filter(Status.name == "PENDING").first()
            completeStatusExists = Status.query.filter(Status.name == "COMPLETE").first()

            if (not createdStatusExists):
                status = Status(name = "CREATED")
                database.session.add(status)
                database.session.commit()

            if (not pendingStatusExists):
                status = Status(name = "PENDING")
                database.session.add(status)
                database.session.commit()

            if (not completeStatusExists):
                status = Status(name = "COMPLETE")
                database.session.add(status)
                database.session.commit()


            done = True
    except Exception as exception:
        print(exception)