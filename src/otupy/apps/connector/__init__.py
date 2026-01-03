""" 
	
	The ``connector`` is a local OpenC2 agent that runs multiple profiles.
	It reades its own configuration in ``connector.yaml`` (or any other file
	given at the command line); additionally, it loads all actuator-specific
  	configuration files in a given folder and sets them up.

	Setup 
	-----

	To run the MIRANDA connector, either download the source code or install from ``PyPI`` (see 
	`setup <https://otupy.readthedocs.io/en/latest/download.html#download-and-setup>`__).

	Alternatively, you can deploy a docker container. Put all configuration files in a local folder (also including
	subfolders, if necessary), and then mount it under the ``/config`` folder of the container when starting it.
	Don't forget to expose the HTTP port used in the configuration file. An example of running in docker: ::

		docker run --rm -v ./config:/config -p 8080:8080 --name connector -d ghcr.io/mattereppe/connector:latest


	Configuration
	-------------

	The `connector.yaml <https://github.com/mattereppe/otupy/blob/main/src/otupy/apps/connector/connector.yaml>`__
	contains a working configuration for running the ``connector`` locally, including comments
	to explains the different parameters.

	The `config-templates <https://github.com/mattereppe/otupy/tree/main/src/otupy/apps/connector/config-templates>`__  
	folder includes templates for configuring the different actuators. Each actuator is described by an item in a
	``yaml`` dictionary, which key is a name that will be assigned to the instance of an actuator, to distinguish 
	between multiple instances of the same class (e.g., ``ctxd-kubernetes-example``). 
	It is mostly an internal identifier not visible to Producers. 
	Multiple actuator configurations may be includedin the same file, or split in different files. 

	The configuration of each actuator must include the following parameters:
	
	- ``actuator``: the identifier of the actuator class (it is not the class name, but an identifier used to register it in otupy (see the ``@actuator`` decorator)
	- ``profile``: namespace identifier of the implemented profile (this might be necessary for actuators that implement multiple profiles

	See the documentation of specific actuators to know additional configuration.

	Run
	---

	Run the connector: ::
		
		python3 connector.py [-c | --config  <config.yaml>]


	Code reference
	--------------

"""
#from connector import main
