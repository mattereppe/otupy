""" Service discovery

	To run the discovery, either download the source code or install from ``PyPI`` (see 
	`setup <https://otupy.readthedocs.io/en/latest/download.html#download-and-setup>`__).

	Run the discovery service: ::

		python3 discovery.py [-c | --config <config.yaml>]

"""
#!../.oc2-env/bin/python3
# Example to use the OpenC2 library
#
from argparse import ArgumentParser
from glob import glob
from os.path import dirname
from yaml import safe_load

import logging
import logging.config

import os
import sys

from otupy.apps.ctxd.api_service import api_listen
from otupy.apps.ctxd.discover_functions import start_discovery
from otupy.apps.ctxd.defaults import parse_and_default

logger = logging.getLogger()


def main() -> None:
	"""
		The main function

		Loads configuration file, parses it, and run the discovery loop.
	
	"""
	
	# Parse the CLI arguments.
	arguments = ArgumentParser()
	arguments.add_argument("-c", "--config", default=f"{dirname(__file__)}/discovery.yaml",
	                       help="path to the configuration file")
	arguments.add_argument("-p", "--port", default=80,
	                       help="TCP port of the API service")
	arguments.add_argument("--host", default="127.0.0.1",
	                       help="IP address of the API service")
	arguments.add_argument("-a", "--api", action="store_true")
	args = arguments.parse_args()

	try:
		# Parse the configuration file.
		with open(args.config) as cf:
		    config = safe_load(cf)
	except:
		config = {}

	# We don't include these values in the config files, because when the api service is used
	# it is likely we don't use a config file at all (logger taken from default)
	config['api']={}
	config['api']['host']=args.host
	config['api']['port']=args.port

	config = parse_and_default(config)

	# Set up logging
	logging.config.dictConfig(config["logger"]) 
	
	if args.api:
		# Start HTTP server and listen for commands
		api_listen(config)
	else:
		start_discovery(config)	
						
if __name__ == "__main__":
	main()


