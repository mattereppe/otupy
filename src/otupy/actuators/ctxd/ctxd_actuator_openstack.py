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
from otupy.profiles.ctxd.data.cloud import Cloud
from otupy.profiles.ctxd.data.consumer import Consumer
from otupy.profiles.ctxd.data.container import Container
from otupy.profiles.ctxd.data.encoding import Encoding
from otupy.profiles.ctxd.data.link_type import LinkType
from otupy.profiles.ctxd.data.os import OS
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

	my_services: ArrayOf(Service) = None # type: ignore
	""" Name of the service """
	my_links: ArrayOf(Link) = None # type: ignore
	"""It identifies the type of the service"""
	specifiers : dict = None
	consumer: dict = None
	auth: dict = None
	services: list = None
	config: dict = None
	conn : any = None #connection to openstack
	
	def __init__(self, specifiers, consumer, auth, config, services=[], **kwargs):
		self.specifiers = specifiers
		self.consumer = consumer
		self.auth = auth
		self.config = config

		self.connect_to_openstack()
		self.my_links = self.get_links()
		self.my_services = self.get_services()


		
	def get_services(self):
		#process = subprocess.Popen('openstack service list -f json', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		#stdout, stderr = process.communicate()
		cloud_services = self.openstack_service_list()
		array_cloud_services = ArrayOf(Cloud)()

		for service in cloud_services:
			if(service['name'] == 'nova'):
				array_cloud_services.append(Cloud(description='cloud', id=service['id'], name=service['id'], type=service['type']))

		openstack_service = Service(name= Name('openstack'), type=ServiceType(array_cloud_services[0]), links=self.get_name_links(self.my_links),
									 subservices=None, owner= self.asset_id, release=None, security_functions=None,
									 actuator=Consumer(**self.consumer))
		return ArrayOf(Service)([openstack_service])


	def get_links(self):
		#process = subprocess.Popen('openstack server list --status ACTIVE -f json', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		#stdout, stderr = process.communicate()
		vms = self.openstack_server_list()
		array_vms = ArrayOf(VM)()

		#definisco il link control tra cloud e vm
		links = ArrayOf(Link)()
		for vm in vms:
			print(vm['name'], vm['description'])
			tmp_vm = VM(vm['description'],
							id= vm['id'], 
							hostname= Hostname(vm['name']),
							os = OS(name=self.openstack_server_os(vm['image']['id'])))

			logger.debug("Found VM: %s", str(tmp_vm))
			array_vms.append(tmp_vm)
			
			tmp_peer = Peer(service_name= Name(vm['name']),
							role= PeerRole.client ) #VM is controlled by Openstack
#							consumer=Consumer(server=Server(Hostname(vm['name'])),
#												port=self.port,
#												protocol= L4Protocol(self.protocol),
#												endpoint= self.endpoint,
#												transfer=Transfer(self.transfer),
#												encoding=Encoding(self.encoding)))

			links.append(Link(name = Name(vm['id']), link_type=LinkType(4), peers=ArrayOf(Peer)([tmp_peer])))

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
		return links
	
	
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

	
	def openstack_service_list(self):
		if not self.conn:
			logger.error("Connection to OpenStack is not established.")
			return
		
		try:
		    # List services available in OpenStack
			services = self.conn.identity.services()
		
			# Format the response as a JSON-like structure for pretty printing
			services_list = []
			for service in services:
				service_data = {key: value for key, value in service.to_dict().items()}
				services_list.append(service_data)
			# Return the formatted services list
			return services_list
		
		except Exception as e:
			logger.warning("Failed to retrieve service list: %s",e)
			return Exception("Failed to retrieve service list")
		
	def openstack_server_list(self):
		if not self.conn:
			logger.error("Connection to OpenStack is not established.")
			return

		try:
			# Use the OpenStack client to list active servers
			servers = self.conn.compute.servers(details=True, status="ACTIVE")

			# Format the response as a JSON-like structure for pretty printing
			server_list = []
			for server in servers:
				server_data = {key: value for key, value in server.to_dict().items()}
				server_list.append(server_data)

        	# Return the formatted server list as a pretty-printed JSON string
			return server_list

		except Exception as e:
			logger.warning("Failed to retrieve server list: %s", e)
			return Exception("Failed to retrieve server list")
		

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
