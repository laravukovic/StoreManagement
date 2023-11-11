pragma solidity ^0.8.2;

contract TicTacToe {
    // x player is the owner
    address payable x_player;
    address payable o_player;

    string x_player_name; 
    string o_player_name; 

    uint wager;

    enum State {
        WAITING_FOR_O,
        IN_PROGRESS,
        FINISHED,
        WAGER_WITHDRAWN
    }
    State state;
    mapping ( State => string ) state_names;

    uint move;
    uint winner;
    uint[] board;

    bool x_withdrawn;
    bool o_withdrawn;

    modifier is_in_state ( State required_state ) {
        require ( 
            state == required_state, 
            string.concat ( "Contract not in required state: ", state_names[required_state] )
        );

        _;
    }

    modifier is_player {
        require (
            ( msg.sender == x_player ) || ( msg.sender == o_player ),
            "You are not a part of this game."
        );

        _;
    }

    event OJoined ( string name );
    event Move ( uint row, uint column, uint symbol );
    event GameFinished ( uint winner );

    error InsufficientFunds ( uint required, uint given );

    constructor ( string memory _x_player_name ) payable {
        x_player      = payable ( msg.sender );
        x_player_name = _x_player_name;

        wager = msg.value;
        state = State.WAITING_FOR_O;

        state_names[State.WAITING_FOR_O] = "WAITING_FOR_O";
        state_names[State.IN_PROGRESS]   = "IN_PROGRESS";
        state_names[State.FINISHED]      = "FINISHED";

        move = 0;
        board = new uint[] ( 9 );

        x_withdrawn = false;
        o_withdrawn = false;
    }

    function get_wager ( ) external view returns ( uint ) {
        return wager;
    }
    
    function get_x_player_name ( ) external view returns ( string memory ) {
        return x_player_name;
    }

    function get_state ( ) external view returns ( State ) {
        return state;
    }

    function get_board ( ) external view returns ( uint[] memory ) {
        return board; 
    }

    function join_o ( string calldata _o_player_name ) external payable is_in_state ( State.WAITING_FOR_O ) {
        if ( msg.value < wager ) {
            revert InsufficientFunds ( wager, msg.value );
        }
    
        o_player      = payable ( msg.sender );
        o_player_name = _o_player_name;
    
        state = State.IN_PROGRESS;
    
        emit OJoined ( o_player_name );
    }

    function check ( ) internal returns ( bool ) {
        bool x_is_winner = ( board[0] == 1 && board[1] == 1 && board[2] == 1 )
                        || ( board[3] == 1 && board[4] == 1 && board[5] == 1 )
                        || ( board[6] == 1 && board[7] == 1 && board[8] == 1 )
                        || ( board[0] == 1 && board[3] == 1 && board[6] == 1 )
                        || ( board[1] == 1 && board[4] == 1 && board[7] == 1 )
                        || ( board[2] == 1 && board[5] == 1 && board[8] == 1 )
                        || ( board[0] == 1 && board[4] == 1 && board[8] == 1 )
                        || ( board[2] == 1 && board[4] == 1 && board[6] == 1 );
    
        bool o_is_winner = ( board[0] == 2 && board[1] == 2 && board[2] == 2 )
                        || ( board[3] == 2 && board[4] == 2 && board[5] == 2 )
                        || ( board[6] == 2 && board[7] == 2 && board[8] == 2 )
                        || ( board[0] == 2 && board[3] == 2 && board[6] == 2 )
                        || ( board[1] == 2 && board[4] == 2 && board[7] == 2 )
                        || ( board[2] == 2 && board[5] == 2 && board[8] == 2 )
                        || ( board[0] == 2 && board[4] == 2 && board[8] == 2 )
                        || ( board[2] == 2 && board[4] == 2 && board[6] == 2 );
    
        if ( x_is_winner ) {
            winner = 1;
        } else if ( o_is_winner ) {
            winner = 2;
        }

        return x_is_winner || o_is_winner;
    }

    function play ( uint row, uint column ) external is_in_state ( State.IN_PROGRESS ) is_player returns ( bool ) {
        bool is_x = msg.sender == x_player;
        bool is_o = msg.sender == o_player;
        
        bool is_even = move % 2 == 0;
        bool is_odd  = move % 2 == 1;

        uint index = row * 3 + column;

        require ( 
            is_x || is_o,
            "You are not a part of this game."
        );
    
        require (
            ( is_x && is_even ) || ( is_o && is_odd ),
            "Wrong turn."
        );

        require (
            row < 3 && column < 3,
            "Invalid row or column."
        );

        require (
            board[index] == 0,
            "Field not empty."
        );

        // 1 == X
        // 2 == 0
        uint symbol = is_x ? 1 : 2;
    
        board[index] = symbol;
    
        move++;
    
        if ( check ( ) || move == 9 ) {
            state = State.FINISHED;

            emit GameFinished ( winner );
        
            return true;
        } else {
            emit Move ( row, column, symbol );
            return false;
        }
    }

    function withdraw ( ) external payable is_in_state ( State.FINISHED ) is_player {
        bool is_x = msg.sender == x_player;
        bool is_o = msg.sender == o_player;
    
        require (
            winner == 0 || ( is_x && winner == 1 ) || ( is_o && winner == 2 ),
            "You did not win this game."
        );

        require (
            ( winner == 0 && x_withdrawn == false ) ||
            ( winner == 0 && o_withdrawn == false ) ||
            ( is_x && winner == 1 && x_withdrawn == false ) || 
            ( is_o && winner == 2 && o_withdrawn == false ),
            "You already withdrew your wager."
        );

        if ( winner == 1 ) {
            x_player.transfer ( 2 * wager );

            x_withdrawn = true;
            state       = State.WAGER_WITHDRAWN;
        } else if ( winner == 2 ) {
            o_player.transfer ( 2 * wager );

            o_withdrawn = true;
            state       = State.WAGER_WITHDRAWN;
        } else {
            if ( is_x ) {
                x_player.transfer ( wager );
            } else {
                o_player.transfer ( wager );
            }

            if ( address ( this ).balance == 0 ) {
                state = State.WAGER_WITHDRAWN;
            }
        }

    }
}