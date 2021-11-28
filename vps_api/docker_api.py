import docker
import json
import re
import time

def docker_create(db,addr,image,name,cmd):
    if addr is None:
        raise 
    if image is None:
        raise
    if len(image) > 64:
       raise
    if len(name) > 32:
       raise
    try:
       name = re.sub(r'\W+', '', name)
       if image not in ["ubuntu","httpd"]:
           image = "httpd"
       cursor = db.connection.cursor()
       sql = "INSERT INTO jobs (address,action,status,argv) VALUES (%s, %s, %s, %s)"
       val = (addr,"create","queued",json.dumps({"img":image,"cmd":cmd,"name":name}))
       cursor.execute(sql,val)
       db.connection.commit()
       cursor.close()
    except BaseException as e:
       return {"status":str(e)}
    return {"status":"queued"}
def docker_destroy(db,addr,id):
    return {"status":"ok","id":0}
def docker_getlist(db,addr):
    result = {"status":"","pods":{}} 
    try:
        cursor = db.connection.cursor()
        sql = "SELECT podid,podname,status FROM pods WHERE address = %s"
        cursor.execute(sql,(addr,))
        pods = cursor.fetchall() 
        cursor.close()
        for pod in pods:
            podid,podname,status = pod
            result[pods][podid] = {"podname":podname,"status":status}
        result["status"] = "ok"
        return result
    except BaseException as e:
        return {"status":"error","result":str(e)}

def docker_getlogs(db,addr,name,regex):
    if addr is None:
       raise 
    #check name length, validate on cron job
    if len(name) > 32:
       raise
    try:
       name = re.sub(r'\W+', '', name)
       cursor = db.connection.cursor()
       argv = json.dumps({"regex":regex,"name":name})
       sql = "INSERT INTO jobs (address,action,status,argv) VALUES (%s, %s, %s, %s)"
       val = (addr,"getlogs","queued",argv)
       cursor.execute(sql,val)
       db.connection.commit()
       while(True):
           sql = "SELECT id,result FROM jobs WHERE address = %s and action = %s and status = %s and argv = %s"
           val = (addr,"getlogs","ok",argv)
           cursor.execute(sql,val)
           row = cursor.fetchone()
           if row:
               jobid, result = row
               result = json.loads(result)
               sql = "UPDATE jobs SET updated = now(), status = %s WHERE id = %s"
               cursor.execute(sql,("parsed",jobid))
               db.connection.commit()
               return result
           db.connection.commit()
           time.sleep(1)
       cursor.close()
    except BaseException as e:
        print(e)
        return {"status":"error", "logs":str(e)}

