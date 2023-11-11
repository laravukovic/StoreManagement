
from web3 import Web3
from web3 import HTTPProvider
from web3 import Account

import secrets
import json

web3 = Web3 ( HTTPProvider ( "http://127.0.0.1:8545" ) )

### A key pair can be created either using a python script, or
### generatig a key file thats encrypted with a passphrase using a 
### wallet app (like etherwallet)

# private_key = "0x" + secrets.token_hex ( 32 )
# account = Account.from_key ( private_key )
# address = account.address
# 
# print ( address )
# print ( private_key )

keys = None
with open ( "keys.json", "r" ) as file:
    keys = json.loads ( file.read ( ) )

address     = web3.to_checksum_address ( keys["address"] )
private_key = Account.decrypt ( keys, "iepblockchain" ).hex ( )

print ( address )
print ( web3.eth.get_balance ( address ) )

to_account = web3.eth.accounts[0]

transaction = {
    "to": to_account,
    "value": 10000,
    "nonce": web3.eth.get_transaction_count ( address ),
    "gasPrice": 1
}

gas_estimate       = web3.eth.estimate_gas ( transaction )
transaction["gas"] = gas_estimate

signed_transaction = web3.eth.account.sign_transaction ( transaction, private_key )

transaction_hash = web3.eth.send_raw_transaction ( signed_transaction.rawTransaction )

receipt = web3.eth.wait_for_transaction_receipt ( transaction_hash )

print ( receipt )