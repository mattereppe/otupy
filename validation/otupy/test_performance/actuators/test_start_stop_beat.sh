#!/bin/bash

# Test start/stop beats with ssh
#

count=1
base_path="/home/matteo/otupy/src/otupy/apps/connector/"

while getopts "b:c:p:" opt; do
  case "$opt" in
		b)
			beat="$OPTARG"
			;;
		c)
			count="$OPTARG"
			;;
		p)
			path="$OPTARG"
			;;
  esac
done

echo "Beat: $beat"
echo "Path: $path"
echo "Count: $count"
 
beat_exe="/usr/share/$beat/bin/$beat"

[ -z "$beat" ] || [ -z "$path" ] && ( echo "Missing parameters"; exit 1 )

#time -p pid=$(ssh tulipano 'cd /home/matteo/otupy/src/otupy/apps/connector/beat/Alpha_11992X && (sudo /usr/bin/filebeat -c filebeat.yml --path.config filebeat-config > /dev/null  2>&1 & while [ -z $pid ]; do pid=$(pgrep -af '^/usr/share/filebeat/bin/filebeat' | awk "{print \$1}"); done; echo $pid) ') ) 2>&1 | awk '/^real/ {print $2}'

echo -e "Start\tStop"
for i in $(seq $count); do
	start=$( (time -p ssh tulipano "cd $base_path && (sudo $beat_exe -c $beat.yml --path.config $path/$beat-config > /dev/null  2>&1 & while [ -z \$pid ]; do pid=\$(pgrep -af \"^/usr/share/$beat/bin/$beat\" | awk '{print \$1}'); done; echo \$pid) " > beat.pid  ) 2>&1 | awk '/^real/ {print $2}' )
	
	sleep 6
	pid=$(cat beat.pid)
#echo "pid: $pid"
	stop=$( (time -p ssh tulipano "sudo kill -9 $pid")  2>&1 | awk '/^real/ {print $2}' )
	
	echo -e "$start\t$stop "
done
