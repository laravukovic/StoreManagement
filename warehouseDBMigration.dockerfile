FROM python:3

RUN mkdir -p /opt/src/warehouseMigrations

WORKDIR /opt/src/warehouseMigrations

COPY application/owner/migrate.py ./migrate.py
COPY application/owner/configuration.py ./configuration.py
COPY application/owner/models.py ./models.py
COPY application/owner/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENTRYPOINT ["python", "./migrate.py"]