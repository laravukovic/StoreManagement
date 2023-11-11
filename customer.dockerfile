FROM python:3

RUN mkdir -p /opt/src/customer

WORKDIR /opt/src/customer

COPY application/customer/customer.py ./customer.py
COPY application/customer/configuration.py ./configuration.py
COPY application/customer/models.py ./models.py
COPY application/customer/requirements.txt ./requirements.txt
COPY application/customer/rightAccess.py ./rightAccess.py
COPY application/solidity/output/Contract.abi ./Contract.abi
COPY application/solidity/output/Contract.bin ./Contract.bin


RUN pip install -r ./requirements.txt

ENTRYPOINT ["python", "./customer.py"]