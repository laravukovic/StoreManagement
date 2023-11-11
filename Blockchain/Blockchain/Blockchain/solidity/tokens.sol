pragma solidity ^0.8.2;

contract Tokens {
    address payable owner;
    mapping ( address => uint256 ) balances;

    constructor ( address payable _owner ) {
        owner = _owner;
    }

    function buyToken ( ) external payable {
        owner.transfer ( msg.value );
        balances[msg.sender] += 1;
    }

    function getToken ( address customer ) external view returns ( uint256 ) {
        return balances[customer];
    }

    function spendToken ( address customer ) external {
        require ( balances[customer] > 0, "Not enough tokens." );
        balances[customer] -= 1;
    }
}