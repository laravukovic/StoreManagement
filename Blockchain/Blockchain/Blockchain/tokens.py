from web3 import Web3
from web3 import HTTPProvider
from web3 import Account

import secrets
import json

web3 = Web3 ( HTTPProvider ( "http://127.0.0.1:8545" ) )

def read_file ( path ):
    with open ( path, "r" ) as file:
        return file.read ( )

keys = json.loads ( read_file ( "keys.json" ) )

address     = web3.to_checksum_address ( keys["address"] )
private_key = Account.decrypt ( keys, "iepblockchain" ).hex ( )

bytecode = read_file ( "./solidity/output/Tokens.bin" )
abi      = read_file ( "./solidity/output/Tokens.abi" )

contract = web3.eth.contract ( bytecode = bytecode, abi = abi )

transaction = contract.constructor ( address ).build_transaction ({
    "from": address,
    "nonce": web3.eth.get_transaction_count ( address ),
    "gasPrice": 21000
})

signed_transaction = web3.eth.account.sign_transaction ( transaction, private_key )
transaction_hash   = web3.eth.send_raw_transaction ( signed_transaction.rawTransaction )
receipt            = web3.eth.wait_for_transaction_receipt ( transaction_hash )
print ( receipt.contractAddress )

contract = web3.eth.contract ( address = receipt.contractAddress, abi = abi )

customer = web3.eth.accounts[0]

print ( "My balance " + str ( web3.eth.get_balance ( address ) ) )
print ( "Customer balance " + str ( web3.eth.get_balance ( customer ) ) )
print ( "Customer tokens: " + str ( contract.functions.getToken ( customer ).call ( ) ) )

contract.functions.buyToken ( ).transact ({
    "from": customer,
    "value": web3.to_wei ( 1, "ether" )
})

print ( "My balance " + str ( web3.eth.get_balance ( address ) ) )
print ( "Customer balance " + str ( web3.eth.get_balance ( customer ) ) )
print ( "Customer tokens: " + str ( contract.functions.getToken ( customer ).call ( ) ) )