FROM python:3

RUN mkdir -p /opt/src/courier

WORKDIR /opt/src/courier

COPY application/courier/courier.py ./courier.py
COPY application/courier/configuration.py ./configuration.py
COPY application/courier/models.py ./models.py
COPY application/courier/requirements.txt ./requirements.txt
COPY application/courier/rightAccess.py ./rightAccess.py
COPY application/solidity/output/Contract.abi ./Contract.abi
COPY application/solidity/output/Contract.bin ./Contract.bin
COPY application/wallets/vlasnik.json ./vlasnik.json

RUN pip install -r ./requirements.txt

ENTRYPOINT ["python", "./courier.py"]