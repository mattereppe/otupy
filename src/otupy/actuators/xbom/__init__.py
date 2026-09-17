""" XBOM actuators for context discovery

	This folder includes several actuators that implement the ``x-bom``profile.
	They provide indeed the function of *actuator managers*, since they use existing
	APIs of cloud management software or configuration files to retrieve the list of
	services. A base class provides common functions to implement the common openc2 methods,
	while derived classes implement specific APIs. For historical and convenience reasons, 
	the main data model used by all classes is based on ctxd, and then this is converted
	to the requested profile data model.

	The following actuators have been designed to work with the MIRANDA 
	:py:class:`~otupy.apps.connector.connector`:

	The general configuration for each actuator should include the following:

		- ``owner``: The owner of the discovery function (specific services might have their own owner).
		- ``specifiers``: This is a dictionary including the OpenC2 identification of the actuator, according to what defined in its own profile :py:class:`~otupy.profiles.xbom.actuator.Specifiers`:

			- ``domain``
			- ``asset_id``

		- ``auth``: Authentication information to connect to external API to get the bom. It is a dictionary that depends on the specific actuator.
		- ``config``: Additional configuration (e.g., CA certificates) that may be needed by the context APIs.
		- ``peers``: A list of external services and the consumers where to get their description. Each element of this list includes:

			- ``service_name``: a :py:class:`~otupy.models.ctxd.name.Name` with the identifier of the service (deprecated).
			- ``sid``: a :py:class:`~otupy.models.ctxd.service.sid` with the service identifier (alternative and preferred to `Name`)
			- ``consumer``: a :py:class:`~otupy.models.ctxd.consumer.Consumer` dictionary that identifies how to connect to the remote consumer, including the actuator specifiers.

				- ``host``
				- ``port``
				- ``profile``
				- ``encoding``
				- ``transfer``
				- ``endpoint``
				- ``actuator`` (xbom py:class:`~otupy.profiles.xbom.actuator.Specifiers`)

"""

