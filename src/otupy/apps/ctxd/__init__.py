""" 
	The ``discovery`` application recursively queries context actuators to build
	a chain of interconnected services. It starts from one or more root services
	(which consumers are known a priori) and periodically and iteratively queries additional 
	peers found in the responses.

	The application is designed to publish context data to multiple sinks.


	Setup 
	-----

	To run the discovery, either download the source code or install from ``PyPI`` (see 
	`setup <https://otupy.readthedocs.io/en/latest/download.html#download-and-setup>`__).



	Configuration
	-------------

	The ``discovery`` application works according to a ``yaml`` configuration file that contains the following
	parameters:
	
	- ``name``: An identifier used to distinguish context originated by different ``discovery``s
	- ``frequency``: The time interval before starting a new round of queries (the real interval will be longer because the timer starts after receving the last answer). Run one-shot if sets to 0.
	- ``loop``: Number of times to repeat the discovery. Loops forever if set to -1, does not run if set to 0.
	- ``publishers``: a dictionary of places where the context data are published after each round. The configuration changes according to the specific publisher:

		- ``mongodb``: A dictionary with configuration to write data to MongoDB

			- ``host``: IP address or hostname of the server hosting the database
			- ``port``: Port number where the mongodb service listens to
			- ``db_name``: Name of the internal database to store data 
			- ``collection``: Name to be used for the collection of documents
			- ``user``: username to connect to the database
			- ``pass``: password to connect to the database

		- ``kafka``: A dictionary with the configuration to publish to Kafka brokers

			- ``host``: IP address or hostname of the server hosting one bootstrap server
			- ``port``: Port number where the bootstrap server listens to
			- ``topic``: The topic used to publish data
			- ``security_protocol``: Security protocol used to connect to Kafka (PLAINTEXT, SSL, SASL_PLAINTEXT, SASL_SSL - see Kafka documentation) 
 			- ``sasl_mechanism``: Username/password authentication mechanism (PLAIN, GSSAPI, OAUTHBEARER, SCRAM-SHA-256, SCRAM-SHA-512). Only valid for security protocols SASL_PLAINTEXT or SASL_SSL
			- ``sasl_plain_username``: Username when sasl mechanism is enabled
			- ``sasl_plain_password``: Password when sasl mechanism is enabled
			- ``ssl_cafile``: CA file used to sign the Kafka certificate
			- ``ssl_check_hostname``: Enable (True) or disable (False) server name validation in the certificate file

		- ``file``: A dictionary with configuration to write to file (append mode)

			- ``name``: Filename (created if does not exist)
		  	- ``path``: Filesystem path to the file (current directory if not given) 	

	- ``services``: A list of "root services" to query, indicated as their :py:class:`~otupy.profiles.ctxd.data.consumer.Consumer` endpoints:

		- ``host``
		- ``port``
		- ``profile``
		- ``encoding``
		- ``transfer``
		- ``endpoint``
		- ``actuator`` (x-ctxd py:class:`~otupy.actuators.ctxd.actuator.Specifiers`)

	- ``logger``: The configuration for the `Logging` framework. See the module `documentation <https://docs.python.org/3/howto/logging.html#logging-advanced-tutorial>`__

	A template configuration file is available `here <https://github.com/mattereppe/otupy/blob/main/src/otupy/apps/ctxd/discovery.yaml.template>`__.

	Run
	---

	Run the discovery service: ::

		python3 discovery.py [-c | --config <config.yaml>] [ -p | --port <port>] [ --host <hostname> ] [  --api ]

		Enable the API service with the ``--api`` flag. If the hostname/port are not given, default values will be used.
		Even if the API service expects a configuration file in the start command, the configuration file remains a valid option and
		can be used to load "default" values and parameters that makes no sense in the API service (e.g., the ``logger`` configuration).

	API service
	-----------

	The following endpoints are available:

	- ``/start``: POST request with a config in json format to start discovery, returns the id of started thread
	- ``/stop``: POST request with a list of thread ids to stop
	- ``/threads``: GET request which returns the list of active threads (active means not cancelled, they may have terminated their job)
	- ``/clean``: POST request that clean up all threads

	All ``POST`` requests MUST have the ``Content-type`` header set to ``application/json``. The configuration of the start request
	only includes a subset of the parameters described above: ``logger`` is not allowed and is ignored.

"""
