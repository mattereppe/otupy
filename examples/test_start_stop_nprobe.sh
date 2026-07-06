#!/bin/bash

# Test start/stop beats with ssh
#

count=1

while getopts "c:p:b:" opt; do
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
  esac
done

[ -z "$base_path" ] && base_path="/usr/bin/"
 
probe_exe=$base_path$probe

[ -z "$probe" ] && { echo "Missing parameters"; exit 1; }

echo -e "Start\tStop"
for i in $(seq $count); do
	start=$( (time -p ssh docker "sudo $probe_exe --interface eth1 -T %IPV4_SRC_ADDR %IPV4_DST_ADDR --collector 127.0.0.1:2055 --collector-timeout 60 -D netflow5 > /dev/null 2>&1 & while [ -z \$pid ]; do pid=\$(pgrep -af \"^$probe_exe\" | awk '{print \$1}'); done; echo \$pid " > probe.pid ) 2>&1 | awk '/^real/ {print $2}' )
	
	sleep 3
	pid=$(cat probe.pid)
	echo "pid: $pid"
	stop=$( (time -p ssh docker "sudo kill -9 $pid")  2>&1 | awk '/^real/ {print $2}' )
	
	echo -e "$start\t$stop "
done
