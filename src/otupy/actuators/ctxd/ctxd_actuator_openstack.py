""" Openstack Actuator Manager

	This module implements a simple Actuator Manager for Openstack..
	It discovers Openstack. resources by invoking its APIs. 

	The actuator-specific configuration includes:
		
		- ``auth``:

			- ``username``: Username used to manage the openstack instance
			- ``password``: Password of the openstack user
			- ``project_name``: Openstack tenant/project name (only 1 tenant supported so far)
			- ``user_domain_name``: Usually set to "Default"
			- ``project_domain_name``: Usually set to "Default"
			- ``auth_url``: Entry point of openstack identity server (``hostname:port/endpoint``)

		- ``config``:
		
			- ``cacert``: Location of the CA certificate used to sign the endpoint HTTPS certificate (if not installed in the local host).


"""

import logging
import openstack

import otupy.profiles
from otupy import Extensions
from otupy.actuators.ctxd.ctxd_actuator import CTXDActuator
from otupy.profiles.ctxd.actuator import Specifiers
from otupy.profiles.ctxd.data.cloud import Cloud
from otupy.profiles.ctxd.data.application import Application
from otupy.profiles.ctxd.data.consumer import Consumer
from otupy.profiles.ctxd.data.container import Container
from otupy.profiles.ctxd.data.link_type import LinkType
from otupy.profiles.ctxd.data.os import OS
from otupy.profiles.ctxd.data.computer import Computer
from otupy.profiles.ctxd.data.peer import Peer
from otupy.profiles.ctxd.data.peer_role import PeerRole
from otupy.profiles.ctxd.data.service_type import ServiceType
from otupy.profiles.ctxd.data.vm import VM
from otupy.types.data.hostname import Hostname
from otupy.types.data.l4_protocol import L4Protocol



from otupy import ArrayOf, Nsid, Version,Actions, Response, StatusCode, StatusCodeDescription, Features, ResponseType, Feature, actuator_implementation
import otupy.profiles.ctxd as ctxd

from otupy.profiles.ctxd.data.name import Name
from otupy.profiles.ctxd.data.service import Service
from otupy.profiles.ctxd.data.link import Link

logger = logging.getLogger(__name__)

@actuator_implementation("ctxd-openstack")
class CTXDActuator_openstack(CTXDActuator):
	""" Openstack Actuator Manager

		Extend the base `CTDXActuator` to retrieve services and links for a Openstack cluster. Currently discovery is mostly limited to vms,
		hypervisors, and OpenStack sw components. It should be extended in future releases with additional resources (e.g., networks, ports).


	"""

	def __init__(self, auth, **kwargs):
		""" Initialize the actuator

			:param auth: (mandatory) Authentication information to connect to OpenStack.
			:param config: (optional) Include additional info for configuration the OpenStack 
				connection (e.g., "cacert" certificate of a custom CA).
			:param specifiers: (optional) The identification of this Actuator.
			:param owner: (optional) Onwer of this service.
			:param peers: (optional) A list of peer services, including their consumer endpoints.
		"""
		kwargs['auth']=auth
		super().__init__(**kwargs)

		self._connect_to_openstack()

	def discover_services(self):
		""" Discover all services related to OpenStack

			OpenStack is a complex framework, where a bundle of applications create and manage virtual resources,
			including VMs, networks, image repositories.
		"""
		self._discover_os_services()
		self._discover_os_servers()
		self._discover_os_hypervisors()		
		# TODO: Discover:
		# - networks
		# - images
		

	def discover_links(self):
		""" Automatically discover links between OpenStack components

			The current implementation discovers links between:
			- OpenStack services (nove) and VMs (servers)
			- VMs (servers) and physical servers (hypervisors)
			- SLPF firewall (iptables) and VMs (servers)
			- VMs (servers) and computers (System and application software), only from a configuration file
		"""
		self._discover_os_link_vms()
		self._discover_os_link_sg()
		self._discover_vms_link_hypervisors()
		self._discover_vms_link_computers()
		self._discover_sg_link_vms()


	def _discover_os_services(self):
		""" Discover Openstack as a composite service made of multiple applications """
		cloud_services = self._openstack_service_list()

		# The root service: OpenStack as cloud environment
		# --------------------------------------------------
		os = Cloud(description='cloud', id=None, name='openstack', type='IaaS')
		# TODO: Fill in with Openstack version/release
		self.services.append(Service(name=Name(os.name),type=ServiceType(os), #links=ArrayOf(Name)(),
				subservices=ArrayOf(Name)(), owner=self.owner, release=None))

		# Software components of openstack
		# ---------------------------------
		for service in cloud_services:
			app = (Application(description=service['description'], name=service['name'], 
						id=service['id'], owner=self.owner, app_type=service['type']))
			logger.debug("Found application: %s", str(app.name))
			# TODO: Add software release (maybe with its SBOM)
			name=Name(app.name)
			self.services.append(Service(name=name, type=ServiceType(app), #links=ArrayOf(Link)(),
						subservices=ArrayOf(Service)(), owner=self.owner, release=None))
			# Paranoid check nobody modified the order of the instraction
			assert  str(self.services[0].name) == os.name , "Wrong position of parent openstack service in array!"
			self.services[0].subservices.append(name)
		
	def _discover_os_servers(self):
		""" Discover VMs created and controlled by this OpenStack instance.

			VMs are known as "servers" in OpenStack terminology.
		"""
		vms = self._openstack_server_list()

		# Servers (VMs) deployed by this instance of OpenStack
		# ----------------------------------------------------
		for vm in vms:
			server = VM(vm['description'],
							id= vm['id'], 
							name= vm['name'],
							image = vm['image']['id'])

			logger.debug("Found server: %s", str(server))

			self.services.append(Service(name=Name(str(server.name)), type=ServiceType(server), #links=ArrayOf(Name)(),
						subservices=None, owner=self.owner, release=None))

			
	def _discover_os_hypervisors(self):
		""" Discover OpenStack hypervisors

			Hypervisors are the physical servers that host VMs. It is questionable if such service 
			should be reported, since the Computer subsystem should have its own actuator describing 
			the full stack of services/software hosted.
		"""
		hvs = self._openstack_hypervisor_list()

		# Hypervisors running VMs in the cloud infrastructure
		# ---------------------------------------------------
		for h in hvs:
			hyper = Computer(hostname=Hostname(h['name']), id=h['service_details']['id'],
					description="OpenStack hypervisor")

			logger.debug("Found hypervisor: %s", str(hyper))

			self.services.append(Service(name=Name(str(h['name'])), type=ServiceType(hyper), #links=ArrayOf(Name)(),
						subservices=None, owner=self.owner, release=None))


	def _discover_os_link_vms(self):
		""" Add links between nova and VMs 
		
			We create explicit links from nova because this is the software components that concretely
			manage VMs. Vulnerabilities applies to nova and other services rather than OpenStack as a whole.	
		"""

		os_services = self.get_services(name=Name('nova'), filter=Application)
		os_vms = self.get_services(filter=VM)

		# There will be only 1 nova instance, since we are connected to a single openstack cloud
		for s in os_services:
			for v in os_vms:
				peer = Peer(service_name= v.name,
							role= PeerRole.controlled)  #VM is controlled by Openstack
				description="Openstack controls "+v.name.getObj()
				self.links.append(Link(name = s.name, description=description, 
							link_type=LinkType.control, peers=ArrayOf(Peer)([peer])))
#s.links.append(Link(name = link_name, link_type=LinkType.control, peers=ArrayOf(Peer)([peer])))

				
	def _discover_os_link_sg(self):
		""" Add link between OpenStack (neutron) and Security Groups

			Security Groups implement a slpf firewall, hence they are a security function. However, they are not
			standalone software, and they are implemented by neutron.
		"""
		os_services = self.get_services(name=Name('neutron'), filter=Application)

		# There will be only 1 nova instance, since we are connected to a single openstack cloud
		for s in os_services:
			consumer = self.get_consumer(Name("openstack-securitygroups"))
			if s is not None:
				peer = Peer(service_name=Name("openstack-securitygroups"),
						role=PeerRole.controlled, consumer=consumer)
				description="OpenStack Security Groups"
				self.links.append(Link(name = s.name, description=description, 
							link_type=LinkType.control, peers=ArrayOf(Peer)([peer])))


	def _discover_vms_link_hypervisors(self):
		""" Add links between VMs and hypervisors that host them

		"""	
		pass

	def _discover_vms_link_computers(self):
		""" Add links between VMs and the software they host

			This is something outside the OpenStack scope, which is delegated to a remote peer
			(currently read by configuration file).
		"""
		os_vms = self.get_services(filter=VM)

		for v in os_vms:
			consumer=self.get_consumer(v.name)

			if consumer is not None:
				peer = Peer(service_name= v.name,
							role= PeerRole.host,  #VM is controlled by Openstack
							consumer=consumer) # This is the consumer running on that service.
				description="System and application software installed on "+v.name.getObj()
				self.links.append(Link(name = v.name, description=description, 
							link_type=LinkType.hosting, peers=ArrayOf(Peer)([peer])))
# I don't like to replicate the link as standalone structure and embedded in Service
#s.links.append(Link(name = link_name, link_type=LinkType.control, peers=ArrayOf(Peer)([peer])))

	def _discover_sg_link_vms(self):
		""" Add links from Security Groups to VMs's ports

			Automatically add a link from Security Group service and all VMs. 
			Security groups are modelled as a security function implemented by an external actuator.
			They protect all VMs hosted in OpenStack.
		"""
		# TODO
		pass


	
	def _connect_to_openstack(self):

		try:
			# Get access to OpenStack (the following mechanism is largely undocumented.
			# See: https://github.com/openstack/openstacksdk/blob/3d45cecb3a897bf9bb10613bfc6ec82a395c153f/doc/source/user/transition_from_profile.rst#L154
			config_dict=openstack.config.defaults.get_defaults()
	
			loader = openstack.config.OpenStackConfig(
	  		  load_yaml_config=False,
	    		app_name='unused',
	    		app_version='1.0')
			cloud_region = loader.get_one_cloud(
	    		region_name='',
	    		auth_type='password',
				auth=self.auth,
				cacert=self.config['cacert'],
	    		)
			self.conn = openstack.connection.from_config(cloud_config=cloud_region)
	

        # Get the token from the connection object (it will automatically handle authentication)
			token = self.conn.authorize()

        # Verify successful authentication by checking token
			if token:
				logger.info("Authentication successful!")
				logger.debug(f"Token: {token}")
			else:
				logger.error("Authentication failed.")
    
		except Exception as e:
			logger.error(f"An error occurred: {e}")

	def _check_connection(self):
		if not self.conn:
			logger.error("Connection to OpenStack is not established.")
			raise 
	
	def _format_os_data(self, data):
			data_list = []
			for d in data:
				 data_list.append( {key: value for key, value in d.to_dict().items()} )
			return data_list


	def _openstack_service_list(self):
		""" Retrieve list of OpenStack services """
		self._check_connection()
		
		try:
		    # List services available in OpenStack
			services = self.conn.identity.services()
		except Exception as e:
			logger.warning("Failed to retrieve service list: %s",e)
			return Exception("Failed to retrieve service list")
		
		# Format the response as a JSON-like structure for pretty printing
		return self._format_os_data(services)
		
		
	def _openstack_server_list(self):
		""" Retrieve list of servers (VMs) from OpenStack APIs """
		self._check_connection()

		try:
			# Use the OpenStack client to list active servers
			servers = self.conn.compute.servers(details=True, status="ACTIVE")
		except Exception as e:
			logger.warning("Failed to retrieve server list: %s", e)
			return Exception("Failed to retrieve server list")

      # Return the formatted server list as a pretty-printed JSON string
		return self._format_os_data(servers)
		
	def _openstack_hypervisor_list(self):
		""" Retrieve list of hypervisors (servers) from OpenStack APIs """
		self._check_connection()

		try:
			# Use the OpenStack client to list hypervisors
			hypervisors = self.conn.compute.hypervisors(details=True) # No filters set
			# Note: this API is not documented
		except Exception as e:
			logger.warning("Failed to retrieve hypervisors list: %s", e)
			return Exception("Failed to retrieve hypervisors list")

     	# Return the formatted server list as a pretty-printed JSON string
		return self._format_os_data(hypervisors)


	def _openstack_server_os(self, image_id):
		""" Retrieve the image installed in a VM from OpenStack APIs """
		try:
        # Get image details using the OpenStack client
			image = self.conn.compute.get_image(image_id)

        # Check if the image is found and return the operating system name
			if image:
				return image.name  # Return the name of the image (OS name)
			else:
				logger.warning("Image with ID %s not found.", image_id)
				return None
		except Exception as e:
			logger.warning(f"Failed to retrieve OS for image ID %s: %s", image_id, e)
			return None
