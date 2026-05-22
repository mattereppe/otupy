""" File xbom Actuator
	
	The File actuator is a generic actuator that reads context data from a 
	configuration file. It is mostly conceived for those components that do
	not have an API or a configuration file to grasp information from, and
	so need a manual configuration of their characteristics. 

	The File Actuator should mostly be used as temporary mockup for unmanaged
  	components, or as really last resort for complex unsupported components.

	The actuator-specific configuration includes:

		- ``services``: A list of service definitions, given as yaml descriptions
			of the corresponding data components in the ``Service`` class.
			
		- ``links``: A list of link definitions, given as yaml descriptions
			of the correponsing data component in the ``Links`` class.
"""	

import logging

from otupy import Encoder, actuator_implementation

from otupy.actuators.xbom.base_xbom_actuator import XBOMActuator
from otupy.models.ctxd import Service, SId, Link, ServiceType


logger = logging.getLogger(__name__)

@actuator_implementation("xbom-file")
class XBOMFileActuator(XBOMActuator):
	""" File Actuator Manager

		Extend the base `XBOMActuator` to retrieve services and links from a file
	  	description. Use for mockup only.


	"""

	def __init__(self, services: list = None, links: list = None, **kwargs):
		""" Initialize the actuator

			:param services: List of services
			:param links: List of links
		"""
		super().__init__(**kwargs)

		self._services = self._create_services(services)
		self._links = self._create_links(links)

	def discover_context(self):
		""" Discover services and links

			Services are reset any time the update_context is invoked. 
		"""
		self.services = self._services
		self.links = self._links
	
	def _create_services(self, services):

		if services is None:
			return []

		service_list = []
		for s in services:
			service_list.append(Encoder.decode(Service, s))

		return service_list
	
	def _create_links(self, links):

		if links is None:
			return []

		link_list = []
		for l in links:
			link_list.append(Encoder.decode(Link, l))

		return link_list
	
