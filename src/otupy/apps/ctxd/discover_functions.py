""" Implementation of the discovery functions

	This module includes a few functions that implement the discovery loops, including 
	querying OpenC2 Consumers and publishing data.
"""

import logging
import time

from threading import Event, get_ident

import otupy 
import otupy.encoders  # Do not remove! It is necessary to find the registered encoders.
import otupy.actuators  # Do not remove! It is necessary to find the registered actuators.

import otupy.profiles.ctxd as ctxd
from otupy.profiles.ctxd.data.name import Name
#from otupy.transfers.http.message import Message

from otupy.apps.ctxd.publishers import *

logger = logging.getLogger(__name__)

def _log_context(ctx):
	""" Debug-only function to check what was reported """
	try:
		tot_services = 0
		tot_links = 0
		for type_ in ctx.keys():
			for item in ctx[type_]:
				if 'service' in item:
					sub=""
					if item['service'].subservices is not None:
						for s in item['service'].subservices:
							sub+=str(s)+","
					logger.debug("Service: %s [%s] {%s}", item['service'].sid, item['service'].name, sub)
					tot_services = tot_services+1
				if 'link' in item:
					if item['link'].peers is not None:
						peers=""
						for p in item['link'].peers:
							peers+=str(p.sid)+"@"+str(p.consumer)+" ["+str(p.role)+"], "
						logger.debug("Link: %s [%s] -- (%s) --> {%s} ", item['link'].sid, item['link'].role, item['link'].link_type, peers)
						tot_links = tot_links+1
		logger.info("Found %d service(s), %d link(s)", tot_services, tot_links)
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
		service.setdefault('encoding', defaults['openc2']['encoding'])
		logger.error("No valid encoder: %s", service['encoding'])
		logger.info("Using default encoder: %s", )
		encoder = otupy.Encoders[service['encoding']].value

	# Load the transferer (beautiful name, eh?).
	try:
		transferer = otupy.Transfers[service['transfer']](service['host'], 
				service['port'], service['endpoint'])
	except:
		service.setdefault('transfer',  defaults['openc2']['transfer'])
		logger.error("No valid transfer: %s", service['transfer'])
		logger.info("Using default transfer: %s", service['transfer'])
		transferer = otupy.Transfers[service['transfer']](service['host'], 
				service['port'], service['endpoint'])


	producer = otupy.Producer("ctxd-discovery.mirandaproject.eu", encoder, transferer)
                                                             
	actuator = ctxd.Specifiers({'asset_id': service['actuator']['asset_id']})
	arg = ctxd.Args({'name_only': False, 'cached': False})
	target = ctxd.Context(services=otupy.ArrayOf(Name)(), links=otupy.ArrayOf(Name)())  # expected all services and links
	cmd = otupy.Command(action=otupy.Actions.query, target=target, args=arg, actuator=actuator)
	try:
		context = producer.sendcmd(cmd)
		logger.info("Got response from: %s", context.from_)
		if context.status == otupy.StatusCode.OK:
			return context.content['results']
		else:
			logger.warn("Unable to query %s: %s", actuator, context.content['status_text'])
	except: 
		logger.warn("No context available from %s", actuator)
		return None


def start_discovery(config: dict, event: Event = None):
	""" Manage the discovery process

		Repeats the discovery process according to the configuration
	"""
	# Add a trailing id to the name, to distinguish between parallel threads
	if config.get('append_threadid', True):
		config['name']=config.get('name', "") + "#" + str(get_ident())
	# Set loop and frequency of the discovery process
	repeat_discovery = loop(config['loop'],config['frequency'],event)(discovery)
	repeat_discovery(config)
