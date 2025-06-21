/mqtt_transfer: Received MQTT payload/ {
	received = $1
}

/mqtt_transfer: Processing command/ {
	gotcommand = $1
}

# In case of bad request, an error is returned
/mqtt_transfer: Unable to understand/ {
	gotcommand = $1
}

/mqtt_transfer: Got response/ {
	gotresponse = $1
}

/mqtt_transfer: Sending response/ {
	sending = $1
	dump(received, gotcommand, gotresponse, sending)
}


	
function dump(received, gotcommand, gotresponse, sending)
{
	print received "\t" gotcommand "\t" gotresponse "\t" sending
}
