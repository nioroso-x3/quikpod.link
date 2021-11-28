Super alpha version of blockchain to docker control system.

Users will be able to run any command on a remote docker container and retrieve the last 30 bytes as bytes32 value, and also serve http or https apis directly through reverse proxies running in the docker server. URL format is https://{address}-{name}.quikpod.link, this url will always proxy http requests to the containers ports 80 and 443.

Needs a VPS or other server with docker, mysql and python3 installed for hosting the docker containers.

Use contract.sol and Remix to operate, no frontend yet.

Contract is at 0x23237D8E9154BE303DE9f1039746a86F0D180Be2.

Job id for the build function is "d12216732aaa4bee8bb3785b62ddf4b6", for the logs function is "4728012b6d4c4ae5bae9d7444a433330"

Instructions:

1 - To make a http server docker container:

Use the requestBuilPod function, parameters are jobid, img (can be ubuntu or httpd for now), name (up to 32 ascii chars), and a url with a txt file for commands to load.
Example parameters for running httpd service:
jobId : d12216732aaa4bee8bb3785b62ddf4b6
img : httpd
name : TestHttp
cmd : https://api.quikpod.link/static/cmd.txt

You will be able to access a http server running at the url "https://<your_eth_address>-TestHttp.quikpod.link", which will serve the index.html specified in cmd.txt

2 - To make a single run docker container:
Example parameters for running httpd service:
jobId : d12216732aaa4bee8bb3785b62ddf4b6
img : ubuntu
name : TestSingleRun
cmd : https://api.quikpod.link/static/cmd2.txt

This will run the container and exit.

To retrieve and store the return value we use the requestLogsPod function:

jobId : d12216732aaa4bee8bb3785b62ddf4b6
name : TestSingleRun
regex : .*

This will store 'hello world from quikpod.link' in the reqIdToLogs map, with the reqId as key.



