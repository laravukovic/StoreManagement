pragma solidity ^0.8.2;

contract Voting {
    struct Candidate {
        uint id;
        string name;
        uint32 vote_count;
    }

    Candidate[] private candidates;

    mapping ( address => uint ) votes;

    modifier notVoted {
        require ( votes[msg.sender] == 0, "The sender already voted." );
        _;
    }

    /// Invalid poll number
    error InvalidPollNumber ( uint number );

    constructor ( string[] memory names ) {
        for ( uint i = 0; i < names.length; ++i ) {
            candidates.push ( Candidate ({
                id: i,
                name: names[i],
                vote_count: 0
            })); 
        }
    }

    function get_results ( ) external view returns (Candidate[] memory) {
        Candidate[] memory result = new Candidate[] ( candidates.length );

        for ( uint i = 0; i < candidates.length; ++i ) {
            result[i] = candidates[i];
        }

        return result;
    }

    function vote ( uint number ) external notVoted {
        // require ( number < candidates.length, "Invalid poll number" );
        if ( number >= candidates.length ) {
            revert InvalidPollNumber ( number );
        }
        votes[msg.sender] = number;
        candidates[number].vote_count += 1;

    }
}