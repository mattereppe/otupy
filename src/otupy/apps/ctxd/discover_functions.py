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

#import otupy.profiles.ctxd as ctxd
import otupy.profiles.xbom as xbom
from otupy.models.xbom import Xbom
import otupy.models.xbom

from otupy.apps.ctxd.publishers import *
from otupy.apps.ctxd.defaults import defaults, set_consumer_defaults

logger = logging.getLogger(__name__)

#def _log_context(xboms):
#	""" Debug-only function to check what was reported """
#	try:
#		tot_services = 0
#		tot_links = 0
#		for type_ in ctx.keys():
#			for item in ctx[type_]:
#				if 'service' in item:
#					sub=""
#					if item['service'].subservices is not None:
#						for s in item['service'].subservices:
#							sub+=str(s)+","
#					logger.debug("Service: %s [%s] {%s}", item['service'].sid, item['service'].name, sub)
#					tot_services = tot_services+1
#				if 'link' in item:
#					if item['link'].peers is not None:
#						peers=""
#						for p in item['link'].peers:
#							peers+=str(p.sid)+"@"+str(p.consumer)+" ["+str(p.role)+"], "
#						logger.debug("Link: %s [%s] -- (%s) --> {%s} ", item['link'].sid, item['link'].role, item['link'].link_type, peers)
#						tot_links = tot_links+1
#		logger.info("Found %d service(s), %d link(s)", tot_services, tot_links)
#	except:
#		logger.info("No service/link found!")
#

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
	xboms = []
	queried_consumers = []
	producer_name=config.get('name','Discovery')

	# We allow more root services to be present in the configuration
	for root in config['services']:
		consumers = [root]

		# Start recursive discovery
		while len(consumers) > 0: 
			consumer = consumers.pop()
			if consumer in queried_consumers:
				logger.info("Skipping %s: already queried", get_consumer_short(consumer))
			else:
				logger.info("Now discovering services and links from %s", get_consumer_short(consumer))
			
				res = discover(consumer, producer_name, 
							config.get("xbom_format", xbom.XbomFormat.ctxd.name), 
							config.get("xbom_encoding", xbom.XbomEncoding.json.name))
				if res is not None:
					boms = res['boms']
					xbom_encoding = res['encoding']
					xbom_format = res['format']
					logger.info("Got %d %s bom(s) (encoded as %s)", len(boms), xbom_format, xbom_encoding)
					logger.debug("%s", boms)

					try:
						for b in boms:
							xbom_raw = Xbom.get(xbom_format)()
							xbom_data = xbom_raw.deserialize(b, xbom_encoding)
							xboms.append(xbom_raw)
							logger.debug("Bom data:\n%s", xbom_raw.summary())
							publish_data(config, b)


						if config['recursive']:
							consumers += xbom_raw.get_consumers()
					except Exception as e:
						logger.error("Unable to retrieve consumers for external bom refs: %s", e)
				else:
					logger.warning("No links returned for %s", get_consumer_short(consumer))

				queried_consumers.append(consumer)


def get_consumers(links):
	""" Retrieve additional consumers from links 

		:param links: An array of links, as discovered by the `discover` function.
		:return: A list of consumers found in the links' peers
	"""
	consumers = []
	for l in links:
		if l.peers:
			for p in l.peers:
				if p.consumer:
					if not p.consumer.profile or p.consumer.profile == xbom.Profile.nsid:
						new_consumer=set_consumer_defaults(vars(p.consumer))
						if new_consumer not in consumers:
							logger.info("Found new context actuator: %s", get_consumer_short(new_consumer))
							consumers.append(new_consumer)
				
	return consumers

def discover(consumer, producer_name, xbom_format, xbom_encoding):
	""" Query an OpenC2 discovery consumer

		Get the list of services and links from a context discovery actuator.
		:param consumer: The endpoint to query from the configuration file.
		:return: service and link lists
	"""
	try:
		consumer.setdefault('encoding', defaults['openc2']['encoding'])
		encoder = otupy.Encoders[consumer['encoding']].value
	except:
		logger.error("No valid encoder: %s", consumer['encoding'])
		logger.info("Using default encoder: %s", defaults['openc2']['encoding'])
		consumer['encoding']= defaults['openc2']['encoding']
		encoder = otupy.Encoders[consumer['encoding']].value

	try:
		consumer.setdefault('transfer',  defaults['openc2']['transfer'])
		transferer = otupy.Transfers[consumer['transfer']](consumer['host'], 
				consumer['port'], consumer['endpoint'])
	except:
		logger.error("No valid transfer: %s", consumer['transfer'])
		logger.info("Using default transfer: %s", defaults['openc2']['transfer'])
		consumer['transfer'] = defaults['openc2']['transfer']
		transferer = otupy.Transfers[consumer['transfer']](consumer['host'], 
				consumer['port'], consumer['endpoint'])


	producer = otupy.Producer(producer_name, encoder, transferer)
                                                             
	actuator = xbom.Specifiers({'asset_id': consumer['actuator']['asset_id']})
	arg = xbom.Args({'cached': False, 
							'format': xbom.XbomFormat[xbom_format], 
							'encoding': xbom.XbomEncoding[xbom_encoding]})
	target = xbom.XbomTarget() # Retrieve all BOMs 
	cmd = otupy.Command(action=otupy.Actions.query, target=target, args=arg, actuator=actuator)
	try:
		context = producer.sendcmd(cmd)
		logger.info("Got response from: %s", context.from_)
		if context.status == otupy.StatusCode.OK:
			return context.content['results']
		else:
			logger.warn("Unable to query %s: %s", actuator, context.content['status_text'])
			return None
	except Exception as e: 
		logger.warn("No bom available from %s", actuator)
		logger.warn("Reason: %s", e)
		return None


def start_discovery(config: dict, event: Event = None):
	""" Manage the discovery process

		Repeats the discovery process according to the configuration
	"""
	# Add a trailing id to the name, to distinguish between parallel threads
	if config.get('append_thread_id', True):
		config['name']=config.get('name', "") + "#" + str(get_ident())
	# Set loop and frequency of the discovery process
	repeat_discovery = loop(config['loop'],config['frequency'],event)(discovery)
	repeat_discovery(config)

def get_consumer_short(consumer: dict):
	""" Return a short id for the consumer
	
		Returns a short string identifier for a consumer,
		using a compact notation that does not include communication
		details (transfer, encoding, ...):
			<asset_id>.<domain>@<host>:<port>

		:param consumer: Dictionary representation of the consumer
		:return: compact string.
	"""

	return f"[{consumer['actuator'].get('asset_id')}.{consumer['actuator'].get('domain')}@{consumer.get('host')}:{consumer.get('port')}"

