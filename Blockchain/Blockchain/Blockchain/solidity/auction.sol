pragma solidity ^0.8.2;

contract Auction {
    address payable owner;
    string description;
    uint auction_end;

    address highest_bidder;
    uint highest_bid;

    // struct PendignReturn {
    //     address payable account;
    //     uint amount;
    // }
    // PendignReturn[] pending_returns;

    mapping ( address => uint ) pending_returns;

    modifier not_after ( uint time ) {
        require ( block.timestamp < time, "Auction has ended." );
        _;
    }

    modifier not_before ( uint time ) {
        require ( block.timestamp < time, "Auction is ongoing." );
        _;
    }

    event HighestBidIncreased ( address bidder, uint amount );
    event AuctionEnd ( address winner, uint amount );

    // error CustomError ( );

    constructor ( string memory _description, uint _duration_in_seconds ) {
        owner       = payable ( msg.sender );
        auction_end = block.timestamp + _duration_in_seconds;
        highest_bid = 0;
        description = _description;
    }

    function get_highest_bid ( ) external view returns ( uint ) {
        return highest_bid;
    }

    function bid ( ) external payable not_after ( auction_end ) {
        require ( msg.value > highest_bid, "Bid not high enough." );

        if ( highest_bidder != address ( 0 ) ) {
            // highest_bidder.transfer ( highest_bid );
            
            // uint index = 0;
            // bool found = false;
            // for ( uint i = 0; i < pending_returns.length; ++i ) {
            //     if ( pending_returns[i].account == highest_bidder ) {
            //         index = i;
            //         found = true;
            //         break;
            //     }
            // }
            // if ( found == false ) {
            //     pending_returns.push(PendingReturn({
            //         account: highest_bidder,
            //         amount: highest_bid
            //     }));
            // } else {
            //     pending_returns[index].amount += highest_bid;
            // }
            
            if ( pending_returns[highest_bidder] != 0 ) {
                pending_returns[highest_bidder] += highest_bid;
            } else {
                pending_returns[highest_bidder] = highest_bid;
            }
        }

        highest_bidder = msg.sender;
        highest_bid    = msg.value;

        emit HighestBidIncreased ( msg.sender, msg.value );
    }

    function end ( ) external not_before ( auction_end ) {
        // require ( msg.sender == owner, "Only owner can access this function." );
        // if ( msg.sender != owner ) {
        //     revert CustomError ( );
        // }

        owner.transfer ( highest_bid );
    
        // for ( uint i = 0; i < pending_returns.length; ++i ) {
        //     pending_returns[i].account.transfer ( pending_returns[i].amount );
        // }

        emit AuctionEnd ( highest_bidder, highest_bid );
    }

    function withdraw ( ) external not_before ( auction_end ) returns ( bool ) {
        uint amount = pending_returns[msg.sender];
        if ( amount > 0 ) {
            ( bool success,  ) = payable ( msg.sender ).call { value: amount } ( "" );
            return success;
        }
        return false;
    }
}