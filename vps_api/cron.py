#!/usr/bin/env python3
import mysql.connector
import sys
import os
import subprocess as sb
queued = "queued"    
running = "running"                                                                                        
ok = "ok" 
LOG_LEVEL=1
MAX_JOBS=4
PID="/opt/vps_api/cron.pid"
def check_cron():
    cpid = os.getpid()
    if os.path.exists(PID):
        try:
            fpid = open(PID, 'r')
            pid = fpid.read()
            fpid.close()
            pid = int(pid)
        except:
            fpid = open(PID, 'w')
            fpid.write(str(cpid))
            fpid.close()
            return False
        return(cpid == pid)            
    else:
        fpid = open(PID, 'w')
        fpid.write(str(cpid))
        fpid.close()
        return False

def PRINT_LOG(msg,level):
    if level > 0:
        print(msg)
def launch_jobs(db):
    cursor = db.cursor()
    cursor.execute("SELECT id FROM jobs WHERE status = %s",(running,))
    running_jobs = len(cursor.fetchall())
    cursor.execute("SELECT id,address FROM jobs WHERE status = %s",(queued,))
    query = cursor.fetchall()
    queued_jobs = len(query)
    slots = min(max(MAX_JOBS - running_jobs,0),queued_jobs)
    PRINT_LOG("Found %d queued jobs" % (queued_jobs,),LOG_LEVEL)
    PRINT_LOG("Found %d running jobs, launching %d jobs" % (running_jobs,slots),LOG_LEVEL)
    for i in range(slots):
        job = query[i]
        jobid, address = job
        #send to wrapper
        pid = sb.Popen(["/usr/bin/python3","/opt/vps_api/wrapper.py",str(jobid)]).pid
        PRINT_LOG("Job %s address %s launched pid %d" % (jobid,address,pid),LOG_LEVEL)

#check status of jobs and subjobs
def check_jobs(db):
    pass

def check_errored_jobs(db):
    pass


if __name__ == "__main__":
    db = mysql.connector.connect(host="localhost",
                             user="quikpod_dev",
                             password="testpassword",
                             database="quikpod_dev")
    if check_cron():
        PRINT_LOG("Found cron already running at pid %s" % (os.getpid(),),LOG_LEVEL)
        exit(0)
    launch_jobs(db)
    check_jobs(db)
    check_errored_jobs(db)
