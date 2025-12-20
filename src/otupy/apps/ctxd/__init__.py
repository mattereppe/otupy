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
	
	- ``frequency``: The time interval before starting a new round of queries (the real interval will be longer because the timer starts after receving the last answer). Run one-shot if sets to 0.
	- ``loop``: Number of times to repeat the discovery. Loops forever if set to -1, does not run if set to 0.
	- ``publishers``: a list of places where the context data are published after each round. The configuration changes according to the specific publisher:

		- ``mongodb``: A dictionary with configuration to write data to MongoDB

			- ``host``: IP address or hostname of the server hosting the database
			- ``port``: Port number where the mongodb service listens to
			- ``db_name``: Name of the internal database to store data (data are saved in the ``services`` and ``links`` collections
			- ``user``: username to connect to the database
			- ``pass``: password to connect to the database

	- ``services``: A list of "root services" to query, indicated as their :py:class:`~otupy.profiles.ctxd.data.consumer.Consumer` endpoints:

		- ``host``
		- ``port``
		- ``profile``
		- ``encoding``
		- ``transfer``
		- ``endpoint``
		- ``actuator`` (x-ctxd py:class:`~otupy.actuators.ctxd.actuator.Specifiers`)

	A template configuration file is available `here <https://github.com/mattereppe/otupy/blob/main/src/otupy/apps/ctxd/discovery.yaml.template>`__.

	Run
	---

	Run the discovery service: ::

		python3 discovery.py [-c | --config <config.yaml>]

	Code reference
	--------------

"""
