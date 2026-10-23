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
	- ``append_thread_id``: Append internal process identifier to the name of this discovery (boolean value). Default to False
	- ``frequency``: The time interval before starting a new round of queries (the real interval will be longer because the timer starts after receving the last answer). Run one-shot if sets to 0.
	- ``loop``: Number of times to repeat the discovery. Loops forever if set to -1, does not run if set to 0.
	- ``recursive``: True if the service chain must be inspected recursively, False if only the provided services must be retrieved. Defaults to False.
	- ``publishers``: a dictionary of places where the context data are published after each round. The configuration changes according to the specific publisher:

		- ``mongodb``: A dictionary with configuration to write data to MongoDB

			- ``host``: IP address or hostname of the server hosting the database
			- ``port``: Port number where the mongodb service listens to
			- ``db_name``: Name of the internal database to store data 
			- ``collection``: Name to be used for the collection of documents
			- ``user``: username to connect to the database
			- ``pass``: password to connect to the database

		- ``kafka``: A dictionary with the configuration to publish to Kafka brokers

			- ``bootstrap``: a list of bootstrap servers, given as:

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

	- ``services``: A list of "root services" to query, indicated as their :py:class:`~otupy.models.ctxd.consumer.Consumer` endpoints:

		- ``host``
		- ``port``
		- ``profile``
		- ``encoding``
		- ``transfer``
		- ``endpoint``
		- ``actuator`` (x-ctxd :py:class:`~otupy.profiles.ctxd.actuator.Specifiers`)

	- ``logger``: The configuration for the ``Logging`` framework. See the module `documentation <https://docs.python.org/3/howto/logging.html#logging-advanced-tutorial>`__

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

	All requests that require an input payload must be sent with the header ``Content-Type: application/json``.

	.. http:post:: /start

	   Starts a new background periodic discovery thread task based on the provided configuration options.

	   .. warning::
	      **Input Sanitization:** The request body only permits a specific subset of parameters. Any keys sent outside of ``name``, ``loop``, ``frequency``, ``publishers``, and ``services`` will be silently dropped by the server before initialization. Other operational defaults (such as logger configurations) are pulled dynamically from the base server context.

	   :reqheader Content-Type: must be ``application/json``
	   
	   **Request JSON Payload:**
	      * **string name:** *(Optional)* Descriptive identity tracking name for this discovery.
	      * **integer loop:** *(Optional)* Total iteration limit constraints. Set to ``-1`` for endless looping runtime behaviors.
	      * **integer frequency:** *(Optional)* Active scheduling delta sleep gap sequence interval quantified in seconds.
	      * **object publishers:** *(Optional)* Dictionary data mappings defining active external publishing storage sinks.
	      * **array services:** *(Optional)* Target listing array defining starting consumer root service profiles.

		Full description of the configuration items is given in the `Configuration <https://otupy.readthedocs.io/en/latest/_autosummary/otupy.apps.ctxd.html#configuration>`__ section.

	   **Response JSON Payload:**
	      * **integer id:** The unique internal operating thread sequence key.
	      * **float start_time:** Execution launch tracking stamp format tracking.
	      * **float end_time:** Estimated task cleanup tracking stamp calculation, or ``null`` if loop rules require indefinite monitoring cycles.
	      * **integer loop:** The finalized configuration constraint value active on the running instance.
	      * **integer frequency:** The finalized sleep loop timing configuration value applied to the running thread.

	   **Example Request Body (JSON):**
	   
	   .. code-block:: json

	      {
	        "name": "Local Network Scanner",
	        "loop": 5,
	        "frequency": 10,
	        "publishers": {},
	        "services": []
	      }

	   **Example Response Body (JSON):**

	   .. code-block:: json

	      {
	        "id": 140224158140160,
	        "start_time": 1795283000.0,
	        "end_time": 1795283050.0,
	        "loop": 5,
	        "frequency": 10
	      }

	   :statuscode 200: Thread spawned successfully and joined active tracker framework pipelines.
	   :statuscode 415: Provided Content-Type was missing or did not match expected application/json format mappings.
	   :statuscode 501: Backend exception encountered while trying to instantiate background thread workers.

	.. http:post:: /stop

	   Terminates specifically requested active discovery processes running in the ecosystem.

	   :reqheader Content-Type: must be ``application/json``

	   **Request JSON Payload:**
	      * **Array of Integers:** A list of internal target thread unique identifiers to terminate.

	   **Response JSON Payload:**
	      * **Array of Integers:** A list of unique operational identifiers successfully unmapped and safely shut down from the active registry.

	   **Example Request Body (JSON):**
	   
	   .. code-block:: json

	      [140224158140160, 140224158140161]

	   **Example Response Body (JSON):**

	   .. code-block:: json

	      [140224158140160, 140224158140161]

	   :statuscode 200: Safe evaluation step processed. Stopped and collected matching event references.
	   :statuscode 400: Call failed context validation checks due to missing explicit content type descriptions.
	   :statuscode 415: Payload structure mapping extraction validation failed parsing checks.
	   :statuscode 501: Processing failure encountered while accessing active worker indexes.

	.. http:get:: /threads

	   Provides a complete active snapshot list of all thread registration identity integers managed by the local tracker.

	   **Response JSON Payload:**
	      * **Array of Integers:** Array list containing all currently active numeric identifier reference values.

	   **Example Response Body (JSON):**

	   .. code-block:: json

	      [140224158140160, 140224158140161]

	   :statuscode 200: Array snapshot compiled and output successfully.

	.. http:post:: /clean

	   Signals a destructive global termination event message across all stored threads, wiping the application registry clean.

	   **Response JSON Payload:**
	      * **Array of Integers:** List of unique thread identification numbers evicted during systemic sweep iterations.

	   **Example Response Body (JSON):**

	   .. code-block:: json

	      [140224158140160, 140224158140161]

	   :statuscode 200: All background execution maps safely cleared out.
	   :statuscode 501: System intercepted context extraction faults while indexing elements during iterative removal processing.

"""

