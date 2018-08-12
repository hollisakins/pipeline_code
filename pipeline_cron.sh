#!/bin/bash

beginSize="$(du --max-depth=1 /data1/ArchSky)"
echo $beginSize


cmd="perl /data1/dailycopy.pl"
echo $cmd
eval $cmd

endSize="$(du --max-depth=1 /data1/ArchSky)"
echo $endSize

if [$beginSize -eq $endSize]
then
echo "I do not think the dailycopy script worked!"
exit
fi

echo "I think the dailycopy script worked!"
exit

cmd="python pipeline.py"
echo $cmd
eval $cmd
