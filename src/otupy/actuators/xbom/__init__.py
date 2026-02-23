""" XBOM actuators

	This folder includes several actuators that implement the ``x-xbom`` profile.
	They provide indeed the function of *actuator managers*, since they use existing
	APIs of cloud management software or configuration files to retrieve the list of
	services.

	The following actuators have been designed to work with the MIRANDA 
	:py:class:`~otupy.apps.connector.connector`:

	The general configuration for each xbom actuator should include the following:

		- ``owner``: The owner of the xbom function (specific services might have their own owner).
		- ``specifiers``: This is a dictionary including the OpenC2 identification of the actuator, according to what defined in its own profile :py:class:`~otupy.profiles.xbom.actuator.Specifiers`:

			- ``domain``
			- ``asset_id``

		- ``auth``: Authentication information to connect to external API to get the xbom. It is a dictionary that depends on the specific xbom actuator.
		- ``config``: Additional configuration (e.g., CA certificates) that may be needed by the context APIs.
		- ``peers``: A list of external services and the consumers where to get their description. Each element of this list includes:

			- ``service_name``: a :py:class:`~otupy.profiles.xbom.data.name.Name` with the identifier of the service.
			- ``consumer``: a :py:class:`~otupy.profiles.xbom.data.consumer.Consumer` dictionary that identifies how to connect to the remote consumer, including the actuator specifiers.

				- ``host``
				- ``port``
				- ``profile``
				- ``encoding``
				- ``transfer``
				- ``endpoint``
				- ``actuator`` (x-xbom py:class:`~otupy.actuators.xbom.actuator.Specifiers`)

"""

from otupy.actuators.xbom.xbom_actuator_openstack import XBOMActuator_openstack
from otupy.actuators.xbom.xbom_actuator_kubernetes import XBOMActuator_kubernetes
from otupy.actuators.xbom.xbom_actuator_file import XBOMActuator_file
from otupy.actuators.xbom.xbom_actuator_open5gs import XBOMActuator_open5gs
