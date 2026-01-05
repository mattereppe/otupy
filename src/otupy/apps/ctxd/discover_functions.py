""" Implementation of the discovery functions

	This module includes a few functions that implement the discovery loops, including 
	querying OpenC2 Consumers and publishing data.
"""

import logging
import time

from threading import Event

import otupy 
import otupy.encoders  # Do not remove! It is necessary to find the registered encoders.
import otupy.actuators  # Do not remove! It is necessary to find the registered actuators.

import otupy.profiles.ctxd as ctxd
from otupy.profiles.ctxd.data.name import Name
#from otupy.transfers.http.message import Message

from otupy.apps.ctxd.publishers import *
from otupy.apps.ctxd.defaults import set_defaults

logger = logging.getLogger()

def _log_context(ctx):
	""" Debug-only function to check what was reported """
	try:
		for type_ in ctx.keys():
			for item in ctx[type_]:
				logger.info("Found %s: %s", type_, item)
	except:
		logger.info("No service/link found!")

# The loop "decorator", which cannot be used as decorator
# because the two arguments are only known at run-time
def loop(num=0, freq=0, event=None):
	""" Sort of decorator to manage loops of the main function """
	def decorator(func):
		def wrapper(*args, **kwargs):
			nonlocal num, freq
			while num!=0 and (event is None or not event.is_set()):
				func(*args, **kwargs)
				num-=1
				if num!=0:
					time.sleep(freq)
			return 
		return wrapper
	return decorator

def add_resource(context, root, res_type, resource_list):
	""" Add discovered service/link to the internal list for publishing """
	if context is None:
		context = []
	for r in resource_list:
		res = {}
		res['source'] = root
		res[res_type] = r
		context.append(res)
	return context
	

def discovery(config):
	""" Orchestrate discovery

		Start the discovery process for each root service provided by configuration.
		TODO: Add a recursive mechanism to discover new services found in `Links`.

		:param config: A dictionary reporting the known list of services to discover.
		:return: None. Data are directly inserted in the output sinks.
	"""
	ctx = {'services': None, 'links': None}

	# Start recursive discovery
	for root in config['services']:
		resources = discover(root)
		try:
			ctx['services'] = add_resource(ctx['services'], root, 'service', resources['services'])
		except:
			logger.warning("No services returned for %s", root)
		try:
			ctx['links'] = add_resource(ctx['links'], root, 'link', resources['links'])
		except:
			logger.warning("No links returned for %s", root)
		# TODO: recursive discovery of peers with valid actuators in links

	_log_context(ctx)
	publish_data(config, ctx)

def discover(service):
	""" Query an OpenC2 discovery service

		Get the list of services and links from a context discovery actuator.
		:param service: The endpoint to query from the configuration file.
		:return: service and link lists
	"""
	try:
		encoder = otupy.Encoders[service['encoding']].value
	except:
		service['encoding'] = set_defaults(service, 'openc2', 'encoding')
		logger.error("No valid encoder: %s", service['encoding'])
		logger.info("Using default encoder: %s", )
		encoder = otupy.Encoders[service['encoding']].value

	# Load the transferer (beautiful name, eh?).
	try:
		transferer = otupy.Transfers[service['transfer']](service['host'], 
				service['port'], service['endpoint'])
	except:
		service['transfer'] = set_defaults(service, 'openc2', 'transfer')
		logger.error("No valid transfer: %s", service['transfer'])
		logger.info("Using default transfer: %s", service['transfer'])
		transferer = otupy.Transfers[service['transfer']](service['host'], 
				service['port'], service['endpoint'])


	producer = otupy.Producer("ctxd-discovery.mirandaproject.eu", encoder, transferer)
                                                             
	actuator = ctxd.Specifiers({'asset_id': service['actuator']['asset_id']})
	arg = ctxd.Args({'name_only': False, 'cached': False})
	target = ctxd.Context(services=otupy.ArrayOf(Name)(), links=otupy.ArrayOf(Name)())  # expected all services and links
	cmd = otupy.Command(action=otupy.Actions.query, target=target, args=arg, actuator=actuator)
	context = producer.sendcmd(cmd)
	logger.info("Got context from: %s", context.from_)

	try:
		return context.content['results']
	except: 
		return None


def start_discovery(config: dict, event: Event = None):
	""" Manage the discovery process

		Repeats the discovery process according to the configuration
	"""
	# Set loop and frequency of the discovery process
	repeat_discovery = loop(config['loop'],config['frequency'],event)(discovery)
	repeat_discovery(config)
