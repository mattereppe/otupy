""" Skeleton `Actuator` for CTXD profile

	This module provides an example to create an `Actuator` for the CTXD profile.
	It only answers to the request for available features.
"""

import json
import subprocess
import os
import logging
import sys
import openstack

from otupy.actuators.ctxd.ctxd_actuator import CTXDActuator
from otupy.profiles.ctxd.actuator import Specifiers
from otupy.profiles.ctxd.data.cloud import Cloud
from otupy.profiles.ctxd.data.application import Application
from otupy.profiles.ctxd.data.consumer import Consumer
from otupy.profiles.ctxd.data.container import Container
from otupy.profiles.ctxd.data.encoding import Encoding
from otupy.profiles.ctxd.data.link_type import LinkType
from otupy.profiles.ctxd.data.os import OS
from otupy.profiles.ctxd.data.computer import Computer
from otupy.profiles.ctxd.data.peer import Peer
from otupy.profiles.ctxd.data.peer_role import PeerRole
from otupy.profiles.ctxd.data.service_type import ServiceType
from otupy.profiles.ctxd.data.transfer import Transfer
from otupy.profiles.ctxd.data.vm import VM
from otupy.types.data.hostname import Hostname
from otupy.types.data.l4_protocol import L4Protocol



from otupy import ArrayOf, Nsid, Version,Actions, Response, StatusCode, StatusCodeDescription, Features, ResponseType, Feature, actuator_implementation
import otupy.profiles.ctxd as ctxd

from otupy.profiles.ctxd.data.name import Name
from otupy.profiles.ctxd.data.service import Service
from otupy.profiles.ctxd.data.link import Link

logger = logging.getLogger(__name__)

OPENC2VERS=Version(1,0)
""" Supported OpenC2 Version """

# An implementation of the ctxd profile. 
@actuator_implementation("ctxd-openstack")
class CTXDActuator_openstack(CTXDActuator):
	""" CTXD implementation

		This class provides an implementation of the CTXD `Actuator`.
	"""

	auth: dict = None
	peers: list = None
	config: dict = None
	conn : any = None #connection to openstack
	
	def __init__(self, owner, auth, config, peers=[], **kwargs):
		self.auth = auth
		self.config = config
		self.peers = peers
		self.owner = owner

		super().__init__()

		self.connect_to_openstack()

		# This should be moved to another method
		self.discover_services()
		self.links = self.get_links()

		print("+++++= self.services: ", self.services)

	def _discover_os_services(self):
		cloud_services = self.openstack_service_list()

		# The root service: OpenStack as cloud environment
		# --------------------------------------------------
		os = Cloud(description='cloud', id=None, name='openstack', type='IaaS')
		# TODO: Fill in with Openstack version/release
		self.services.append(Service(name=Name(os.name),type=ServiceType(os), links=ArrayOf(Name)(),
				subservices=ArrayOf(Name)(), owner=self.owner, release=None))

		# Software components of openstack
		# ---------------------------------
		for service in cloud_services:
			app = (Application(description=service['description'], name=service['name'], 
						id=service['id'], owner=self.owner, app_type=service['type']))
			logger.debug("Found application: %s", str(app.name))
			# TODO: Add software release (maybe with its SBOM)
			name=Name(app.name)
			self.services.append(Service(name=name, type=ServiceType(app), links=ArrayOf(Link)(),
						subservices=ArrayOf(Service)(), owner=self.owner, release=None))
			# Paranoid check nobody modified the order of the instraction
			assert ( str(self.services[0].name) == os.name , "Wrong position of parent openstack service in array!")
			self.services[0].subservices.append(name)
		
	def _discover_os_servers(self):
		vms = self.openstack_server_list()

		# Servers (VMs) deployed by this instance of OpenStack
		# ----------------------------------------------------
		for vm in vms:
			server = VM(vm['description'],
							id= vm['id'], 
							name= vm['name'],
							image = vm['image']['id'])

			logger.debug("Found server: %s", str(server))

			self.services.append(Service(name=Name(str(server.name)), type=ServiceType(server), links=ArrayOf(Name)(),
						subservices=None, owner=self.owner, release=None))
			
	def _discover_os_hypervisors(self):
		hvs = self.openstack_hypervisor_list()

		# Hypervisors running VMs in the cloud infrastructure
		# ---------------------------------------------------
		for h in hvs:
			hyper = Computer(hostname=Hostname(h['name']), id=h['service_details']['id'])

			logger.debug("Found hypervisor: %s", str(hyper))

			self.services.append(Service(name=Name(str(h['name'])), type=ServiceType(hyper), links=ArrayOf(Name)(),
						subservices=None, owner=self.owner, release=None))

	def _discover_os_link_vms(self):
		""" Add link between nova and VMs """

		os_services = self._get_services(name=Name('nova'), filter=Application)
		os_vms = self._get_services(filter=VM)

		# There will be only 1 nova instance, since we are connected to a single openstack cloud
		for s in os_services:
			for v in os_vms:
				consumer={}
				for p in self.peers:
					if p['service_name'] == v.name.getObj():
						consumer = p['consumer']
						break
				print(">>>>>> consumer: ", consumer)
				peer = Peer(service_name= s.name,
							role= PeerRole.controlled,  #VM is controlled by Openstack
							consumer=Consumer(**consumer)) # This is the consumer running on that service.
				link_name=Name("openstack-"+v.name.getObj())
				self.links.append(Link(name = link_name, link_type=LinkType.control, peers=ArrayOf(Peer)([peer])))
				s.links.append(Link(name = link_name, link_type=LinkType.control, peers=ArrayOf(Peer)([peer])))
				


		print(">>>> Cloud services: ", os_services)

	def discover_services(self):
		self._discover_os_services()
		self._discover_os_servers()
		self._discover_os_hypervisors()		
		# TODO: Discover:
		# - networks
		# - images
		

	def get_links(self):
		self._discover_os_link_vms()
	
		#definisco il link control tra cloud e vm
#		links = ArrayOf(Link)()
#
#			service_name=Name(vm['name'])
#
#
#		# By default, each link has the format "openstack-[name of node]"
#
#		#create a dumb slpf peer
#		slpf_peer = Peer(service_name= Name('slpf'),
#						role= PeerRole(3), #The slpf is hosted by Openstack
#						consumer=Consumer(server=Server(Hostname('os-fw')),
#											port=self.port,
#											protocol= L4Protocol(self.protocol),
#											endpoint= self.endpoint,
#											transfer=Transfer(self.transfer),
#											encoding=Encoding(self.encoding)))
#				
#		links.append(Link(name = Name('os-fw'), link_type=LinkType(2), peers=ArrayOf(Peer)([slpf_peer])))
#		#end creation of dumb slpf
#		
#		return links
	
	
	def get_name_links(self, links):
		
		name_links = ArrayOf(Name)()
		
		for link in links:
			name_links.append(link.name.obj)

		return name_links
	

	def connect_to_openstack(self):

		try:
			# Get access to OpenStack (the following mechanism is largely undocumented.
			# See: https://github.com/openstack/openstacksdk/blob/3d45cecb3a897bf9bb10613bfc6ec82a395c153f/doc/source/user/transition_from_profile.rst#L154
			config_dict=openstack.config.defaults.get_defaults()
			config_dict.update(
				{'name': 'iccio', 'cacert': '/etc/ssl/certs/TNTCA2.crt'},
			)
	
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


	def openstack_service_list(self):
		self._check_connection()
		
		try:
		    # List services available in OpenStack
			services = self.conn.identity.services()
		except Exception as e:
			logger.warning("Failed to retrieve service list: %s",e)
			return Exception("Failed to retrieve service list")
		
		# Format the response as a JSON-like structure for pretty printing
		return self._format_os_data(services)
		
		
	def openstack_server_list(self):
		self._check_connection()

		try:
			# Use the OpenStack client to list active servers
			servers = self.conn.compute.servers(details=True, status="ACTIVE")
		except Exception as e:
			logger.warning("Failed to retrieve server list: %s", e)
			return Exception("Failed to retrieve server list")

      # Return the formatted server list as a pretty-printed JSON string
		return self._format_os_data(servers)
		
	def openstack_hypervisor_list(self):
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


	def openstack_server_os(self, image_id):
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
