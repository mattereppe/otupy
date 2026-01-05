""" Manage default values 

	The module is necessary to use functions in threads
"""

import logging

logger = logging.getLogger()

defaults = { # Default values for context discovery operation
				'name': "Discovery",
				'loop': -1,
				'frequency': 60,
				# Default values for OpenC2 communication
				'openc2': {
					'host': '127.0.0.1',
					'port': 443,
					'endpoint': "/.well-known/openc2",
					'encoding': 'json',
					'transfer': 'http'},
				# Default values for Mongodb connection
				'mongodb': {
					'host': '127.0.0.1',
					'port': 27017,
					'db_name': '',
					'user': None,
					'pass': None},
				# Default values for Kafka 
				'kafka': {
					'host': '127.0.0.1',
					'port': 9092,
					'topic': None,
					'security_protocol': 'PLAINTEXT',
					'sasl_mechanism': None,
					'sasl_plain_username': None,
					'sasl_plain_password': None,
					'ssl_cafile': None,
					'ssl_check_hostname': True
				},
				# Default configuration for file publisher
				'file': {
					'name': 'contextdata.json',
					'path': '.'
				},
				# Default configuration for logger
				'logger': {
				   'version': 1, 
				   'formatters': {
						'otupy': {
							'()': 'otupy.LogFormatter', 
							'datetime': True, 
							'name': True
						} 
					},
					'handlers': {
						'console': {
							'class': 'logging.StreamHandler', 
							'formatter': 'otupy', 
							'level': 'INFO', 
							'filters': None
						}
					},
					'root': {
						'handlers': ['console'], 
						'level': 'INFO'
					}
				}
}
""" Defaults value to be used for missing input parameters """

def set_defaults(config, type_, param):
	""" Sets default values

		Checks if input parameters have value, and assign a default value in case no value was provided.

		:param config: The dictionary with input config parameter.
		:param type_: The group to which the parameter belongs (check `defaults`). There might be parameters with the same name under different stanzas.
		:param param: The name of the parameter.
		:return: The value to be assigned to the parameter.
	"""

	try:
		if config[param] is not None:
			return config[param]
	except:
		pass

	try:
		logger.info("Using default value %s for %s", defaults[type_][param], param)
		return defaults[type_][param]
	except:
		logger.warn("No default value for: %s/%s", type_, param)
		return None

	

def parse_and_default(config):
	""" Parse config dictionary and assign default values to mising items
	"""

	# Logging framework and base service parameters
	for c in ['name', 'logger', 'loop', 'frequency']:
		if c not in config:
			config[c]=defaults[c]

	# Service section (ctxd actuators)
	if 'services' in config and config['services'] is not None:
		for service in config["services"]:
			
			# Load default values for missing parameters
			for p in defaults['openc2'].keys():
				service[p] = set_defaults(service,'openc2',p)

			# Check discovery params
			for p in 'loop', 'frequency':
				config[p] = set_defaults(config, 'ctxd', p)	
	else:
		config['services'] = []

	# Database section:
	if 'publishers' in config:
		for name in config['publishers'].keys():
			if config['publishers'][name] is None:
				config['publishers'][name]={}
			for p in defaults[name].keys():
				config['publishers'][name][p] = set_defaults(config['publishers'][name], name,  p)
	else:
		config['publishers']={}

	return config

