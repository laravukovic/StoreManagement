pragma solidity ^0.8.0;

contract Contract {
    address payable public owner;
    address payable public customer;
    address payable public courier;
    uint256 public totalAmount;


    constructor(address payable _customer) {
        owner = payable(msg.sender);
        customer = _customer;
    }

    function setCourier(address payable _courier) external {
        require(courier == address(0), "Courier address has already been set.");
        require(msg.sender != courier && msg.sender != customer, "Only the owner can set the courier address.");
        courier = _courier;
    }

    function transferFunds() external payable {
        require(msg.sender == customer, "Only the customer can transfer funds.");
        require(msg.value > 0, "No funds provided.");
        totalAmount = msg.value;
    }

    function distributeFunds() external {
        require(msg.sender == customer, "Only the customer can distribute funds.");
        require(totalAmount > 0, "No funds available to distribute.");

        uint256 ownerAmount = (totalAmount * 80) / 100;
        uint256 courierAmount = (totalAmount * 20) / 100;

        owner.transfer(ownerAmount);

        if (courier != address(0)) {
            courier.transfer(courierAmount);
        } else {
            // If courier address is not set, the funds allocated for the courier will remain in the contract
            // and can be distributed later when the courier address is set by the courier using the `setCourier` function.
        }

        totalAmount = 0;
    }

    function getOwnerAddress() external view returns (address) {
        return owner;
    }

    function getCustomerAddress() external view returns (address) {
        return customer;
    }

    function getCourierAddress() external view returns (address) {
        return courier;
    }

    function getTotalAmount() external view returns (uint256) {
        return totalAmount;
    }
}
