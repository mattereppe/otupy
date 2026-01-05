""" Expose REST API to control discovery

	This module creates a web server that exposes REST APIs to control the discovery service.
	
	The following endpoints are available:
	- start: POST request with a config in json format to start discovery, returns the id of started thread
	- stop: POST request with a list of thread ids to stop
	- threads: GET request which returns the list of active threads (active means not cancelled, they may have terminated their job)
	- clean: GET request that clean up all threads



"""

import logging
import json
import time

from threading import Thread, Event
from datetime import datetime

from flask import Flask, request, make_response
from werkzeug.exceptions import HTTPException, UnsupportedMediaType

from otupy.apps.ctxd.discover_functions import start_discovery
from otupy.apps.ctxd.defaults import parse_and_default, set_defaults

logger = logging.getLogger()

SAFE_CONFIG_KEYS=['name', 'loop', 'frequency', 'publishers', 'services' ]

def api_listen(config: dict) -> None:
	""" Listen for HTTP connections

		Start a web server waiting for commands. Commands may include a configuration for the discovery.
		Missing values will be taken from the web service base configuration (which includes default
		values and local file configuration).
		
		:param discovery: The discovery function that will be invoked on start operation
		:param config: The config dictionary that contains a default configuration.
	"""
	thread_list = {}

	app = Flask(__name__)

	@app.route("/start", methods=['POST'])
	def _start():
		""" Serving endpoint for `Flask` """
		
		# Check the HTTP content type (only json supported)
		content_type =request.headers['Content-type']

		if content_type != 'application/json':
			raise UnsupportedMediaType("Unsupported content type")

		try:
			req_conf = json.loads(request.data)
		except:
			req_conf = {}
		logger.info("Got start request with config: %s", req_conf)
		sanitize_config(req_conf)
		logger.debug("Sanitized input data: %s", req_conf)
		# Generate a configuration by merging the default values with requested config
		myconf = config | req_conf
		myconf = parse_and_default(myconf)

		# Start periodic discovery task, according to the configuration
		try:
			e = Event()
			t = Thread(target=start_discovery, args=(myconf, e))
			t.start()
			id = t.ident
			if id is not None:
				thread_list[id] = {'thread': t, 'event': e}
			httpcode = 200
			logger.info("Started discovery thread: %s", str(id))
		except Exception as ex:
			logger.warn("Unable to start discovery thread: %s", ex)
			httpcode = 501
		
		start_time = datetime.now().timestamp()
		if myconf['loop'] < 0:
			expected_end_time = None
		elif myconf['loop'] == 0:
			expected_end_time = start_time
		else:
			expected_end_time = start_time + myconf['frequency'] * myconf['loop']
		resp = {'id': id,
			'start_time': start_time,
			'end_time': expected_end_time,
			'loop': myconf['loop'],
			'frequency': myconf['frequency']}	
		httpresp = make_response(resp)
		
		return httpresp, httpcode

	@app.route("/threads", methods=['GET'])
	def _get_thread_ids():
		""" Serving endpoint for `Flask` """
		
		httpresp = make_response(list(thread_list.keys()))

		return httpresp, 200	

	@app.route("/stop", methods=['POST'])
	def _stop():
		""" Serving endpoint for `Flask` """

		# Check the HTTP content type (only json supported)
		try:
			content_type =request.headers['Content-type']
		except KeyError:
			return make_response("Missing content type", 400) 

		if content_type != 'application/json':
			raise UnsupportedMediaType("Unsupported content type")

		try:
			ids = json.loads(request.data)
		except:
			ids = []	
		logger.info("Got stop request for threads: %s", ids)

		# Stop discovery threads
		try:
			stopped = []
			for id in ids:
				e = thread_list[id]['event']
				t = thread_list[id]['thread']
				e.set()
				#t.join() We do not join, since it may takes a long time (depending on frequency
				stopped.append(id)
				thread_list.pop(id)
				logger.info("Stopped discovery thread: %s", str(id))
			httpcode = 200
		except Exception as ex:
			logger.warn("Unable to stop discovery thread: %s", ex)
			httpcode = 501

		httpresp = make_response(stopped)

		return httpresp, httpcode
	
	@app.route("/clean", methods=['GET'])
	def _clean():
		""" Remove all running threads """

		# Stop discovery threads
		try:
			stopped = []
			for id in thread_list.keys():
				e = thread_list[id]['event']
				t = thread_list[id]['thread']
				e.set()
				#t.join() We do not join, since it may takes a long time (depending on frequency
				stopped.append(id)
				logger.info("Stopped discovery thread: %s", str(id))
			for id in stopped:
				thread_list.pop(id)
			httpcode = 200
		except Exception as ex:
			logger.warn("Unable to stop discovery thread: %s", ex)
			httpcode = 501

		httpresp = make_response(stopped)
	
		return httpresp, httpcode

	app.run(debug=True, host=config['api']['host'], port=config['api']['port'], ssl_context=None)

def sanitize_config(conf):
	""" Sanitize input data

		Only keep expected keyworkd in input data. Very simple check so far on the key names, more
		accurate controls may be implemented in the future.
	"""
	unexpected = []
	for key in conf.keys():
		if key not in SAFE_CONFIG_KEYS:
			unexpected.append(key)

	for key in unexpected:
		conf.pop(key)

	return conf
