#!/usr/bin/env python3
import docker
import mysql.connector
import sys
import os
import subprocess as sb
import json
import uuid
import requests
import re

def get_name(addr,name):
    return "-".join(["0x"+addr,name])

#create and run container. if it already exists with same name stops and deletes
def docker_create(client,db,addr,argv):
    img = argv["img"]
    name =argv["name"]
    podname = get_name(addr,name)
    try:
        container = client.containers.get(podname)
        container.stop(timeout=0)
        container.reload()
        container.remove()
    except docker.errors.NotFound:
        pass
    try:
        cmd = requests.get(argv["cmd"]).text
        container = client.containers.run(img, command=cmd, detach=True,name=podname)
        container.reload()
        podid = container.attrs["Id"]
        ip = container.attrs['NetworkSettings']['IPAddress']
        return {"status":"ok", "podid":str(podid),"ip":str(ip),"addr":str(addr),"img":str(img),"name":str(podname)}
    except BaseException as e:
        return {"status":"error","error_cause":str(e)}

def docker_getlogs(client,db,addr,argv):
    regex = argv["regex"]
    name = argv["name"]
    podname = get_name(addr,name)
    try:
        container = client.containers.get(podname)
        container.reload()
        logs = str(container.logs().decode("utf-8"))
        if regex != "":
            logs = re.match(regex,logs).string
        return {"status":"ok", "logs":str(logs)}
    except BaseException as e:
        return {"status":"error", "logs":"error", "error_cause":str(e)}

def docker_destroy(client,db,addr,id):
    return {"status":"ok","id":0}
def docker_getlist(client,db,addr):
    return {"status":"ok","pods":{0:{"image":"ubuntu"},1:{"image":"centos"}}}

def docker_create_proxy(param):
    ip = param["ip"]
    name = param["name"]
    apacheconf ="""<VirtualHost *:80>
    ServerName quikpod.link
    ServerAlias {name}.quikpod.link
    ProxyPreserveHost On
    ErrorLog /var/log/apache2/error.{name}.log
    CustomLog /var/log/apache2/access.{name}.log combined
    ProxyPass           / http://{ip}:80
    ProxyPassReverse    / http://{ip}:80
</VirtualHost>
<VirtualHost *:443>
    ServerName quikpod.link
    ServerAlias {name}.quikpod.link
    ProxyPreserveHost On
    SSLProxyEngine On
    SSLProxyCheckPeerCN off
    SSLProxyCheckPeerExpire off
    SSLProxyVerify none
    SSLCertificateChainFile /etc/letsencrypt/live/quikpod.link/chain.pem
    SSLCertificateFile /etc/letsencrypt/live/quikpod.link/cert.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/quikpod.link/privkey.pem
    ErrorLog /var/log/apache2/error_ssl.{name}.log
    CustomLog /var/log/apache2/access_ssl.{name}.log combined
    ProxyPass           / http://{ip}:80
    ProxyPassReverse    / http://{ip}:80
</VirtualHost>
""".format(ip=ip,name=name)
    fname = "/etc/apache2/sites-enabled/"+name+".conf"
    conf_f = open(fname,"w")
    conf_f.write(apacheconf)
    conf_f.close()
    ret = {"status":"","ret":""}
    configtest = sb.check_output(["/usr/sbin/apachectl","configtest"],stderr=sb.STDOUT).decode("utf-8").strip()
    if ("Syntax OK" in configtest):
        log = sb.check_output(["/usr/bin/systemctl","reload","apache2"],stderr=sb.STDOUT).decode("utf-8").strip()
        ret["status"] = "ok"
        ret["ret"] = log
    else:
        log = sb.check_output(["/usr/bin/rm","-rf",fname],stderr=sb.STDOUT).decode("utf-8").strip()
        ret["status"] = "error"
        ret["ret"] = log
    return ret

if __name__ == "__main__":
    jobid = sys.argv[1]
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    db = mysql.connector.connect(host="localhost",
                                     user="quikpod_dev",
                                     password="testpassword",
                                     database="quikpod_dev")

    cursor = db.cursor()   
    try:
        sql = "SELECT address,action,argv from jobs WHERE id = %s"
        cursor.execute(sql,(jobid,))
        address, action, argv = cursor.fetchone()
        argv = json.loads(argv)
        pid = os.getpid()
        sql = "UPDATE jobs SET updated = now(), status = %s, pid = %s WHERE id = %s"
        cursor.execute(sql,("running",pid,jobid))
        db.commit()
    
        if(action == "create"):
            result = docker_create(client,db,address,argv)
            if result["status"] == "ok":
                sql = "INSERT INTO pods (address,podid,name,img,ip,status) values (%s, %s, %s, %s, %s, %s)"
                cursor.execute(sql,(result["addr"],result["podid"],result["name"],result["img"],result["ip"],"ok"))
                db.commit()
                proxy_result = docker_create_proxy(result)
                sql = "UPDATE pods SET updated = now(), http = %s WHERE podid = %s"
                cursor.execute(sql,(proxy_result["status"],result["podid"]))
                db.commit()
            sql = "UPDATE jobs SET updated = now(), status = %s, result = %s WHERE id = %s"
            cursor.execute(sql,(result["status"],json.dumps(result),jobid))
            db.commit()
        if(action == "destroy"):
            pass
        if(action == "status"):
            pass
        if(action == "getlogs"):
            result = docker_getlogs(client,db,address,argv)
            sql = "UPDATE jobs SET updated = now(), status = %s, result = %s WHERE id = %s"
            cursor.execute(sql,(result["status"],json.dumps(result),jobid))
            db.commit()

    except BaseException as e:
        print(e)
        sql = "UPDATE jobs SET updated = now(), status = %s, result = %s WHERE id = %s"
        cursor.execute(sql,("error",json.dumps({"status":"error","error_cause":str(e)}),jobid))
        db.commit()


