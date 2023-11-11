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

bytecode = read_file ( "./solidity/output/TicTacToe.bin" )
abi      = read_file ( "./solidity/output/TicTacToe.abi" )

contract = web3.eth.contract ( bytecode = bytecode, abi = abi )

x_player = web3.eth.accounts[0]
o_player = web3.eth.accounts[1]
intruder = web3.eth.accounts[2]

transaction_hash = contract.constructor ( "XPlayer" ).transact ({
    "from": x_player,
    "value": 100
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

o_joined_event_filter = contract.events\
                                .OJoined\
                                .create_filter ( fromBlock = "latest" )
move_event_filter = contract.events\
                            .Move\
                            .create_filter ( fromBlock = "latest" )

game_finished_event_filter = contract.events\
                                     .GameFinished\
                                     .create_filter ( fromBlock = "latest" )

o_joined_thread = threading.Thread ( 
    target = event_loop, 
    args = ( o_joined_event_filter, 1, stopped ) 
)

move_thread = threading.Thread ( 
    target = event_loop, 
    args = ( move_event_filter, 1, stopped ) 
)

game_finished_thread = threading.Thread ( 
    target = event_loop, 
    args = ( game_finished_event_filter, 1, stopped ) 
)

o_joined_thread.start ( );
move_thread.start ( )
game_finished_thread.start ( )


x_player_name = contract.functions.get_x_player_name ( ).call ( )
wager         = contract.functions.get_wager ( ).call ( )
state         = contract.functions.get_state ( ).call ( )

print ( f"X player name: {x_player_name}" )
print ( f"Wager: {wager}" )
print ( f"state: {state}" )

try:
    result = contract.functions.play ( 0, 0 ).call ( )
except ContractLogicError as error:
    print ( error )

contract.functions.join_o ( "OPlayer" ).transact ({
    "from": o_player,
    "value": 100
})

game_over = False

def print_board ( board ):
    symbols = [" ", "X", "0"]
    
    symbol_board = [symbols[item] for item in board]

    for row in range ( 3 ):
        for column in range ( 3 ):
            if ( column != 0 ):
                print ( "|", end = "" )
            index = row * 3 + column
            print ( symbol_board[index], end = "" )

        print ( )
        if ( row != 2 ):
            print ( "-----" )
         
    print ( "====================" )

while ( not game_over ):
    board = contract.functions.get_board ( ).call ( )
    print_board ( board )

    free_slots = [
        (index // 3, index % 3) 
        for index, value in enumerate ( board ) 
        if ( value == 0 )
    ]

    slot = random.choice ( free_slots )

    print ( slot )
    try:
        contract.functions.play ( slot[0], slot[1] ).transact({
            "from": x_player
        })
    except ContractLogicError as error: 
        print ( error )

    try:
        contract.functions.play ( slot[0], slot[1] ).transact({
            "from": o_player
        })
    except ContractLogicError as error: 
        print ( error )

    game_over = contract.functions.get_state ( ).call ( ) == 2;

board = contract.functions.get_board ( ).call ( )
print_board ( board )

stop = True

o_joined_thread.join ( )
move_thread.join ( )
game_finished_thread.join ( )


try:
    print ( "Intruder withdrawing wager" )
    contract.functions.withdraw ( ).transact ({
        "from": intruder 
    })
except ContractLogicError as error:
    print ( error )

try:
    print ( "X withdrawing wager" )
    contract.functions.withdraw ( ).transact ({
        "from": x_player
    })
except ContractLogicError as error:
    print ( error )

try:
    print ( "O withdrawing wager" )
    contract.functions.withdraw ( ).transact ({
        "from": o_player
    })
except ContractLogicError as error:
    print ( error )


