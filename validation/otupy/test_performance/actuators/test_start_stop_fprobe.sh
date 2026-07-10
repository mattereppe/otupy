#!/bin/bash

# Test start/stop beats with ssh
#

# Default values
count=1
probe="fprobe"
base_path="/usr/sbin/"
host="127.0.0.1"

while getopts "c:p:b:h:" opt; do
  case "$opt" in
		c)
			count="$OPTARG"
			;;
		p)
			probe="$OPTARG"
			;;
		b)
			path="$OPTARG"
			;;
		h) 
			host="$OPTARG"
			;;
  esac
done
 
probe_exe=$base_path$probe
echo $probe_exe


echo -e "Start\tStop"
for i in $(seq $count); do
	start=$( (time -p ssh $host "sudo $probe_exe -l 2 -i ens18 -n 5 -e 60 127.0.0.1:2055 > /dev/null 2>&1 & while [ -z \$pid ]; do pid=\$(pgrep -af \"^$probe_exe\" | awk '{print \$1}'); done; echo \$pid " > probe.pid ) 2>&1 | awk '/^real/ {print $2}' )
	
	sleep 6
	pid=$(cat probe.pid)
#	echo "pid: $pid"
	stop=$( (time -p ssh $host "sudo kill -9 $pid")  2>&1 | awk '/^real/ {print $2}' )
	
	echo -e "$start\t$stop "
done
