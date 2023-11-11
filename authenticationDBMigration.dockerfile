FROM python:3

RUN mkdir -p /opt/src/authenticationMigrations

WORKDIR /opt/src/authenticationMigrations

COPY authentication/migrate.py ./migrate.py
COPY authentication/configuration.py ./configuration.py
COPY authentication/models.py ./models.py
COPY authentication/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENTRYPOINT ["python", "./migrate.py"]