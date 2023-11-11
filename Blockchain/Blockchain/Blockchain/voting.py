from web3 import Web3
from web3 import HTTPProvider
from web3 import Account
from web3.exceptions import ContractLogicError
from web3.exceptions import ContractCustomError

import secrets
import json
import random

web3 = Web3 ( HTTPProvider ( "http://127.0.0.1:8545" ) )

def read_file ( path ):
    with open ( path, "r" ) as file:
        return file.read ( )

keys = json.loads ( read_file ( "keys.json" ) )

address     = web3.to_checksum_address ( keys["address"] )
private_key = Account.decrypt ( keys, "iepblockchain" ).hex ( )

bytecode = read_file ( "./solidity/output/Voting.bin" )
abi      = read_file ( "./solidity/output/Voting.abi" )

candidates = [
    "Pera Peric", 
    "Mika Mikic"
]

contract = web3.eth.contract ( bytecode = bytecode, abi = abi )

transaction = contract.constructor ( candidates ).build_transaction ({
    "from": address,
    "nonce": web3.eth.get_transaction_count ( address ),
    "gasPrice": 21000
})

signed_transaction = web3.eth.account.sign_transaction ( transaction, private_key )
transaction_hash   = web3.eth.send_raw_transaction ( signed_transaction.rawTransaction )
receipt            = web3.eth.wait_for_transaction_receipt ( transaction_hash )

contract = web3.eth.contract ( address = receipt.contractAddress, abi = abi )

for account in web3.eth.accounts[:-1]:
    number = random.randint ( 0, len ( candidates ) - 1 )
    transaction_hash = contract.functions.vote ( number ).transact ({
        "from": account
    })

print ( contract.functions.get_results ( ).call ( ) )

try:
    contract.functions.vote ( 10 ).transact ({
        "from": web3.eth.accounts[-1]
    })
except ContractLogicError as error:
    print ( error )