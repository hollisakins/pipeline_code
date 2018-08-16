#!/bin/bash

# this script is what is executed daily via the CRONTAB
# it includes a command to cd to /data1 and ls because that is the only way
# i know that works to undo the lockup from the virtually mounted drives

cd /data1
ls
python pipeline.py
