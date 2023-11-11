FROM python:3

RUN mkdir -p /opt/src/owner

WORKDIR /opt/src/owner

COPY application/owner/owner.py ./owner.py
COPY application/owner/configuration.py ./configuration.py
COPY application/owner/models.py ./models.py
COPY application/owner/requirements.txt ./requirements.txt
COPY application/owner/rightAccess.py ./rightAccess.py

RUN pip install -r ./requirements.txt

ENTRYPOINT ["python", "./owner.py"]