#!/bin/bash
for i in $(seq 30)
do
    /opt/vps_api/cron.py
    sleep 2
done


