from web3 import Web3
from web3 import HTTPProvider

import pprint

web3 = Web3 ( HTTPProvider ( "http://127.0.0.1:8545" ) )

for account in web3.eth.accounts:
    balance = web3.from_wei ( web3.eth.get_balance ( account ), "ether" )

    print ( f"BALANCE({account}) = {balance}" )

number_of_blocks = web3.eth.block_number

preety_printer = pprint.PrettyPrinter ( )

for i in range ( number_of_blocks + 1 ):
    block = web3.eth.get_block ( i, True )

    preety_printer.pprint ( dict ( block ) )

    for transaction in block.transactions:

        preety_printer.pprint ( dict ( transaction ) )