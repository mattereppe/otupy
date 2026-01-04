""" Utilities to export context

	This module contains utilities used to save data retrieved by OpenC2 context discovery.

"""

import json

from pymongo import MongoClient
from kafka import KafkaProducer

import otupy 

JSONSCHEMA = "http://mirandaproject.eu/ctxd/v1.0/schema.json"
""" Json schema id currently used to log context data """

def connect_to_publishers(config):
	""" Connect to the list of publishers

		Takes a config file with the endpoints and auth data to connect. Used only for those publishers
		that support persistent connection (including opening a file).
	"""

	publishers = {}
	# Publishers will always have default values!
	for name, conf in config['publishers'].items():
		match name:
			case "mongodb":
				try: 
					if conf['user'] is not None and conf['pass'] is not None:
						client = MongoClient("mongodb://"+conf['user']+":"+conf['pass']+"@"+conf['host']+":"+str(conf['port']))
					else:
						client = MongoClient("mongodb://"+conf['host']+":"+str(conf['port']))
					# Create or switch to a database
					publishers['mongodb'] = client[conf['db_name']]
				except Exception as e:
					logger.error("Unable to connect to mongodb: %s", e)
			case "kafka":
				try:
					producer = KafkaProducer(bootstrap_servers = [ conf['host']+":"+str(conf['port']) ],
							client_id = config['name'],
                     sasl_plain_username = conf['sasl_plain_username'],
                     sasl_plain_password = conf['sasl_plain_password'],
                     security_protocol = conf['security_protocol'],
                     sasl_mechanism = conf['sasl_mechanism'],
							ssl_check_hostname=conf['ssl_check_hostname'],
							ssl_cafile='ca-cert')
					publishers['kafka'] = producer
				except Exception as e:
					logger.error("Unable to connect to kafka: %s", e)
			case "file":
				try:
					publishers['file'] = open(conf['path']+"/"+conf['name'], 'a')
				except Exception as e:
					logger.error("Unable to open file: %s, reason: %s", conf['name'], e)
			case _:
				logger.warning("Skipping unsupported db: %s", name)
	
	return publishers

def disconnect_from_publishers(publishers):
	""" Cleanly close the connection

		Close open connections to publishers. Used to clean up the session of persistent connections
		(including files).
	"""

	for name, conf in publishers.items():
	
		match name:
			case "mongodb":
				pass
			case "kafka":
				conf.flush()
				conf.close()
			case "file":
				conf.close()
			case _:
				logger.warning("Skipping unsupported publisher: %s", name)



def publish_data(config, ctx):
	""" Publish data

		Publishes data on all available publishers. This function assumes a persistent session is active.
	"""

	publishers = connect_to_publishers(config)

	# TODO: Add metadata about the service which publish data
	ctx['date'] = otupy.DateTime()
	try:
		ctx['creator'] = config['name']
	except:
		ctx['creator'] = "unkwnon"
	ctx['jsonschema'] = JSONSCHEMA

	jsondata = otupy.encoders.JSONEncoder().encode(ctx)

	for name, pub  in publishers.items(): 
		match name:
			case 'mongodb':
				try:
					collection = pub[ config['publishers'][name]['collection'] ]
				except:
					# Default collection name if that provided does not work
					collection = pub["contextdata"]
				# Delete all documents in the collection -- NO MORE NECESSARY, because we use metadata right now
				# collection.delete_many({})
				# Note: otupy encoders return str, so we must convert them to dict
				collection.insert_one(json.loads(jsondata)).inserted_id
			case 'kafka':
				try:
					pub.send(config['publishers'][name]['topic'], value=jsondata.encode('utf-8'))
#	pub.send('demo', b'Hello, Kafka!')
					pub.flush()
				except Exception as e:
					logger.error("Unable to publish data to kafka topic: %s", str(e))
			case 'file':
				try:
					pub.write(jsondata)
				except Exception as e:
					logger.error("Unable to dump data to file: %s", e)
			case _:
				# Unrecognized names have been already pruned in the connect phase
				pass

	disconnect_from_publishers(publishers)
	
