BEGIN {
	print "Command ready\t\tSending\t\t\tGot response\t\tResponse decoded"
}

/root: Sending command/ {
	sending = $1
}

/mqtt_transfer: Publishing msg/ {
	transfering = $1
}

/mqtt_transfer: MQTT got response/ {
	gotresponse = $1
}

/root: Got response/ {
	response = $1
	dump(sending, transfering, gotresponse, response)
}


	
function dump(sending, transfering, gotresponse, response)
{
	print sending "\t" transfering "\t" gotresponse "\t" response 
}
