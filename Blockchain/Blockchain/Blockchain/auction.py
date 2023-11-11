from web3 import Web3
from web3 import HTTPProvider
from web3 import Account
from web3.exceptions import ContractLogicError
from web3.exceptions import ContractCustomError

import json
import threading
import time
import random

web3 = Web3 ( HTTPProvider ( "http://127.0.0.1:8545" ) )

def read_file ( path ):
    with open ( path, "r" ) as file:
        return file.read ( )

bytecode = read_file ( "./solidity/output/Auction.bin" )
abi      = read_file ( "./solidity/output/Auction.abi" )

contract = web3.eth.contract ( bytecode = bytecode, abi = abi )

owner       = web3.eth.accounts[0]
contestants = web3.eth.accounts[1:]

transaction_hash = contract.constructor ( "Simple auction", 5 ).transact ({
    "from": owner,
})

receipt = web3.eth.wait_for_transaction_receipt ( transaction_hash )

contract = web3.eth.contract ( address = receipt.contractAddress, abi = abi )

def event_loop ( event_filter, poll_interval, stopped ):
    while ( not stopped ( ) ):
        for event in event_filter.get_new_entries ( ):
            print ( event )

        # time.sleep ( poll_interval )

stop    = False
stopped = lambda: stop

highest_bid_incresed_event_filter = contract.events\
                                            .HighestBidIncreased\
                                            .create_filter ( fromBlock = "latest" )
auction_end_event_filter = contract.events\
                                    .AuctionEnd\
                                    .create_filter ( fromBlock = "latest" )

highest_bid_increased_thread = threading.Thread ( 
    target = event_loop, 
    args = ( highest_bid_incresed_event_filter, 1, stopped ) 
)
auction_end_thread = threading.Thread ( 
    target = event_loop, 
    args = ( auction_end_event_filter, 1, stopped ) 
)

highest_bid_increased_thread.start ( );
auction_end_thread.start ( )

number_of_bids = random.randint ( 10, 100 )
for i in range ( number_of_bids ):
    contestant = random.choice ( contestants )
    value      = random.randrange ( 10, 100 )
    try:
        transaction_hash = contract.functions.bid ( ).transact ({
            "from": contestant,
            "value": value
        })
    except ContractLogicError as error:
        print ( error )

contract.functions.end ( ).transact ({
    "from": owner
})

stop = True

highest_bid_increased_thread.join ( )
auction_end_thread.join ( )
