#!/bin/bash

# this script is what is executed daily via the CRONTAB
# it includes a command to cd to /data1 and ls because that is the only way
# i know that works to undo the lockup from the virtually mounted drives

cmd="cd /data1"
echo $cmd
eval $cmd

cmd = "ls" 
echo $cmd
eval $cmd

cmd="python pipeline.py"
echo $cmd
eval $cmd

