from flask import Flask
app = Flask(__name__)
from functools import wraps
from flask import request, abort
from flask_mysqldb import MySQL
import json
from docker_api import *
VERSION="0.1"
app.config["DEBUG"] = True
app.config["SERVER_NAME"] = 'api.quikpod.link'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'quikpod_dev'
app.config['MYSQL_PASSWORD'] = 'placeholderpassword'
app.config['MYSQL_DB'] = 'quikpod_dev'
db = MySQL(app)

# The actual decorator function
def require_appkey(view_function):
    @wraps(view_function)
    # the new, post-decoration function. Note *args and **kwargs here.
    def decorated_function(*args, **kwargs):
        # replace this with db to check key
        keys = []
        with open('/opt/vps_api/api.key', 'r') as apikey:
            keys = apikey.read().split('\n')
        #if request.args.get('key') and request.args.get('key') == key:
        if  request.args.get('key') and request.args.get('key') in keys:
            return view_function(*args, **kwargs)
        else:
            abort(401)
    return decorated_function

@app.route('/')
def version():
    return json.dumps({"version": VERSION})

@app.route('/create')
@require_appkey
def create():
    try:
        addr = request.args.get('addr')
        image = request.args.get('img')
        name = request.args.get('name')
        result = docker_create(db,addr,image,name)
        return json.dumps({"action":"create","status": result["status"]})
    except BaseException as e:
        return json.dumps({"action":"create","error": str(e)})

@app.route('/build',methods=["PUT","POST"])
def build():
    try:
        req = request.get_json()["data"]
        key = req['key']
        keys = []
        with open('/opt/vps_api/api.key', 'r') as apikey:
            keys = apikey.read().split('\n')
        assert key in keys                         
        addr = req['addr']
        image = req['img']
        name = req['name']
        cmd = req['cmd']
        result = docker_create(db,addr,image,name,cmd)
        #status ok, code 200
        return json.dumps({"data":{"action":"create","status": result["status"],"code":"200"}})
    except BaseException as e:
        return json.dumps({"error":{"action":"create","error": str(e)}})

@app.route('/getlogs',methods=["PUT","POST"])
def logs():
    try:
        req = request.get_json()["data"]
        key = req['key']
        keys = []
        with open('/opt/vps_api/api.key', 'r') as apikey:
            keys = apikey.read().split('\n')
        assert key in keys                         
        addr = req['addr']
        name = req['name']
        regex = req['regex']
        result = docker_getlogs(db,addr,name,regex)
        #status ok, cut result to 32 bytes
        return json.dumps({"data":{"action":"getlogs","status": result["status"],"logs":result["logs"][-30:]}})
    except BaseException as e:
        print(e)
        return json.dumps({"error":{"action":"getlogs","error": str(e)}})




if __name__ == ("__main__"):
    app.run()
