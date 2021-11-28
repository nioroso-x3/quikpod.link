// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "@chainlink/contracts/src/v0.8/ChainlinkClient.sol";
import "@chainlink/contracts/src/v0.8/ConfirmedOwner.sol";
import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

contract quikpod_kovan is ChainlinkClient, ConfirmedOwner {
  using Chainlink for Chainlink.Request;
  //kovan oracle
  address ORACLE = 0x9C0383DE842A3A0f403b0021F6F85756524d5599;

  uint256 constant private ORACLE_PAYMENT = 1 * LINK_DIVISIBILITY ;
 
  AggregatorV3Interface internal priceFeed;

  event RequestBuildPodFulfilled(
    bytes32 indexed requestId,
    bytes32 indexed code
  );
  event RequestLogsPodFulfilled(
    bytes32 indexed requestId,
    bytes32 indexed logs
  );
  constructor() ConfirmedOwner(msg.sender){
    setPublicChainlinkToken();
    priceFeed = AggregatorV3Interface(0x9326BFA02ADD2366b30bacB125260Af641031331);
  }
  //some functions for char and strings from stackoverflow
  function char(bytes1 b) internal pure returns (bytes1 c) {
    if (uint8(b) < 10) return bytes1(uint8(b) + 0x30);
    else return bytes1(uint8(b) + 0x57);
  }
  function toAsciiString(address x) internal pure returns (string memory) {
    bytes memory s = new bytes(40);
    for (uint i = 0; i < 20; i++) {
        bytes1 b = bytes1(uint8(uint(uint160(x)) / (2**(8*(19 - i)))));
        bytes1 hi = bytes1(uint8(b) / 16);
        bytes1 lo = bytes1(uint8(b) - 16 * uint8(hi));
        s[2*i] = char(hi);
        s[2*i+1] = char(lo);            
    }
    return string(s);
  }

  mapping(address => uint256) public addressToAmountFunded;
  //stores last log command issued
  mapping(bytes32 => bytes32) public reqIdToLogs;
  mapping(bytes32 => bytes32) public reqIdToBuildCode;
  mapping(address => bytes32) public addrToLastBuildReqId;
  mapping(address => bytes32) public addrToLastLogsReqId;
  address[] public funders;
  
  function getPrice() public view returns(uint256){
    (,int256 answer,,,) = priceFeed.latestRoundData();
    return uint256(answer * 10000000000);
  }
  function getConversionRate(uint256 ethAmount) public view returns (uint256){
    uint256 ethPrice = getPrice();
    uint256 ethAmountInUsd = (ethPrice * ethAmount) / 1000000000000000000;
    return ethAmountInUsd;
  }

  function fund() public payable {
    uint256 minimumUSD = (1 * 10 ** 18) / 10;
    require(getConversionRate(msg.value) >= minimumUSD, "You need to spend more ETH!");
    addressToAmountFunded[msg.sender] += msg.value;
    funders.push(msg.sender);
  }


  //proxy url will always be address-name.quikpod.link Ex: 0x123456789-kovan_test.quikpod.link
  function requestBuildPod(string memory _jobId,string memory _img, string memory _name, string memory _cmdurl) 
    public payable returns (bytes32)
  {

    uint256 minimumUSD = (1 * 10 ** 18);
    require(getConversionRate(msg.value) >= minimumUSD, "You need to spend more ETH!");
    addressToAmountFunded[msg.sender] += msg.value;
    funders.push(msg.sender);

    Chainlink.Request memory req = buildChainlinkRequest(stringToBytes32(_jobId), address(this), this.fulfillBuildPod.selector);
    req.add("addr", toAsciiString(msg.sender));
    req.add("img", _img); //only httpd or ubuntu for now
    req.add("name", _name); //up to 30 characters name
    req.add("cmd", _cmdurl); //url with commands
    bytes32 ret = sendChainlinkRequestTo(ORACLE, req, ORACLE_PAYMENT);
    addrToLastBuildReqId[msg.sender] = ret;
    return ret;
  }
  //get last 30 bytes of  docker logs.
  function requestLogsPod(string memory _jobId,string memory _name, string memory _regex)
    public payable returns (bytes32)
  {
    uint256 minimumUSD = (1 * 10 ** 18)/10;
    require(getConversionRate(msg.value) >= minimumUSD, "You need to spend more ETH!");
    addressToAmountFunded[msg.sender] += msg.value;
    funders.push(msg.sender);
    Chainlink.Request memory req = buildChainlinkRequest(stringToBytes32(_jobId), address(this), this.fulfillLogsPod.selector);
    req.add("addr", toAsciiString(msg.sender));
    req.add("name", _name);
    req.add("regex",_regex);
    bytes32 ret = sendChainlinkRequestTo(ORACLE, req, ORACLE_PAYMENT);
    addrToLastLogsReqId[msg.sender] = ret;
    return ret;
  }
  function ViewLastBuildCode() 
    public view returns (bytes32)
  {
    return reqIdToBuildCode[addrToLastBuildReqId[msg.sender]];
  }
  function ViewLastLogs() 
    public view returns (bytes32)
  {
    return reqIdToLogs[addrToLastLogsReqId[msg.sender]];
  }
  function fulfillBuildPod(bytes32 _requestId, bytes32 _code)
    public
    recordChainlinkFulfillment(_requestId)
  {
    emit RequestBuildPodFulfilled(_requestId,_code);
    reqIdToBuildCode[_requestId] = _code;
  }
  function fulfillLogsPod(bytes32 _requestId, bytes32 _logs)
    public
    recordChainlinkFulfillment(_requestId)
  {
    emit RequestLogsPodFulfilled(_requestId,_logs);
    reqIdToLogs[_requestId] = _logs;
  }

  function getChainlinkToken() public view returns (address) {
    return chainlinkTokenAddress();
  }

  function withdrawLink() public onlyOwner {
    LinkTokenInterface link = LinkTokenInterface(chainlinkTokenAddress());
    require(link.transfer(msg.sender, link.balanceOf(address(this))), "Unable to transfer");
  }

  function cancelRequest(
    bytes32 _requestId,
    uint256 _payment,
    bytes4 _callbackFunctionId,
    uint256 _expiration
  )
    public
    onlyOwner
  {
    cancelChainlinkRequest(_requestId, _payment, _callbackFunctionId, _expiration);
  }
  
  function withdraw() payable onlyOwner public {
        payable(msg.sender).transfer(address(this).balance);      
        for (uint256 funderIndex=0; funderIndex < funders.length; funderIndex++){
            address funder = funders[funderIndex];
            addressToAmountFunded[funder] = 0;
        }
        funders = new address[](0);
  }
  function stringToBytes32(string memory source) private pure returns (bytes32 result) {
    bytes memory tempEmptyStringTest = bytes(source);
    if (tempEmptyStringTest.length == 0) {
      return 0x0;
    }

    assembly { // solhint-disable-line no-inline-assembly
      result := mload(add(source, 32))
    }
  }
}
