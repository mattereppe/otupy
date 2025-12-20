""" Context discovery actuators

	This folder includes several actuators that implement the ``x-ctxd`` profile.
	They provide indeed the function of *actuator managers*, since they use existing
	APIs of cloud management software or configuration files to retrieve the list of
	services.

	The following actuators have been designed to work with the MIRANDA 
	:py:class:`~otupy.apps.connector.connector`:

	The general configuration for each ctxd actuator should include the following:

		- ``owner``: The owner of the context discovery function (specific services might have their own owner).
		- ``specifiers``: This is a dictionary including the OpenC2 identification of the actuator, according to what defined in its own profile :py:class:`~otupy.profiles.ctxd.actuator.Specifiers`:

			- ``domain``
			- ``asset_id``

		- ``auth``: Authentication information to connect to external API to get the context. It is a dictionary that depends on the specific ctxd actuator.
		- ``config``: Additional configuration (e.g., CA certificates) that may be needed by the context APIs.
		- ``peers``: A list of external services and the consumers where to get their description. Each element of this list includes:

			- ``service_name``: a :py:class:`~otupy.profiles.ctxd.data.name.Name` with the identifier of the service.
			- ``consumer``: a :py:class:`~otupy.profiles.ctxd.data.consumer.Consumer` dictionary that identifies how to connect to the remote consumer, including the actuator specifiers.

				- ``host``
				- ``port``
				- ``profile``
				- ``encoding``
				- ``transfer``
				- ``endpoint``
				- ``actuator`` (x-ctxd py:class:`~otupy.actuators.ctxd.actuator.Specifiers`)

"""

from otupy.actuators.ctxd.ctxd_actuator_openstack import CTXDActuator_openstack
from otupy.actuators.ctxd.ctxd_actuator_kubernetes import CTXDActuator_kubernetes
