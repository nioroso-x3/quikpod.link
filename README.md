# quikpod.link

## Super alpha version of blockchain to docker control system.


Users will be able to run any command on a remote docker container and retrieve the last 30 bytes as bytes32 value, and also serve http or https apis directly through reverse proxies running in the docker server. URL format is https://{address}-{name}.quikpod.link, this url will always proxy http requests to the containers ports 80 and 443.

Needs a VPS or other server with docker, mysql and python3 installed for hosting the docker containers.  
Use contract.sol and Remix on the kovan network to operate, no frontend yet.  
Contract is at 0x4f626808E8d48632eef4B73878c267fECb6Ef111.  
Job id for the build function is "9bf9d1522f1f4ffdaa4a04756e083c3f", for the logs function is "4728012b6d4c4ae5bae9d7444a433330"


Instructions:


### 1 - To make a http server docker container:


Use the requestBuilPod function, parameters are jobid, img (can be ubuntu or httpd for now), name (up to 32 ascii chars), and a url with a txt file for commands to load.

Example parameters for running httpd service:

jobId : 9bf9d1522f1f4ffdaa4a04756e083c3f  
img : httpd  
name : TestHttp  
cmd : https://api.quikpod.link/static/cmd.txt

You will be able to access a http server running at the url "https://<your_eth_address>-TestHttp.quikpod.link", which will serve the index.html specified in cmd.txt

### 2 - To make a single run docker container:

Example parameters for running a ubuntu container running commands from a file in a url:

jobId : 9bf9d1522f1f4ffdaa4a04756e083c3f  
img : ubuntu  
name : TestSingleRun  
cmd : https://api.quikpod.link/static/cmd2.txt

This will run the container and exit.  
#### 2.1 To retrieve and store the return value we use the requestLogsPod function:

jobId : d12216732aaa4bee8bb3785b62ddf4b6  
name : TestSingleRun  
regex : .*

This will store 'hello world from quikpod.link' in the reqIdToLogs map, with the reqId as key.

Use the ViewLastLogs and ViewLastBuildCode functions to view the results.
