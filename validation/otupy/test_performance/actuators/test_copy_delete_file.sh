#!/bin/bash

# Test start/stop beats with ssh
#

# Default values
count=1
base_path="/tmp/matteo"
host="127.0.0.1"

while getopts "b:h:f:c:" opt; do
  case "$opt" in
		b)
			base_path="$OPTARG"
			;;
		h) 
			host="$OPTARG"
			;;
		f)
			filename="$OPTARG"
			;;
		c)
			count="$OPTARG"
  esac
done
 
file_location=$base_path"/"$filename
echo $file_location


echo -e "Copy\tDelete"
for i in $(seq $count); do
	copy=$( (time -p scp $filename $host:$file_location) 2>&1 | awk '/^real/ {print $2}' )
#	scp $filename $host:$file_location
	
	sleep 6
	delete=$( (time -p ssh $host "rm -f $file_location")  2>&1 | awk '/^real/ {print $2}' )
#	ssh $host "rm -f $file_location"
	
	echo -e "$copy\t$delete "
done
