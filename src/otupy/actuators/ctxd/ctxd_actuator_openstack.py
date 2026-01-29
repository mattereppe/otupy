""" Openstack Actuator Manager

	This module implements a simple Actuator Manager for Openstack..
	It discovers Openstack. resources by invoking its APIs. 

	The documentation of the OpenStack API to retrieve data is available at: https://docs.openstack.org/openstacksdk/latest/user/index.html.

	The actuator-specific configuration includes:
		
		- ``auth``:

			- ``username``: Username used to manage the openstack instance.
			- ``password``: Password of the openstack user.
			- ``user_domain_name``: The domain name for the authenticating user. Usually set to "Default".
			- ``project_domain_name``: The domain name where the project is created. Usually set to "Default".
			- ``project_name``: Openstack tenant/project name. Ignored if `projects` is set in `config` below.
			- ``auth_url``: Entry point of openstack identity server (``hostname:port/endpoint``).

		- ``config``:
		
			- ``dns``: DNS identifier for this installation. Used to create unique identifiers for the resources.
			- ``cacert``: Location of the CA certificate used to sign the endpoint HTTPS certificate (if not installed in the local host).
			- ``projects``:  A list of project name to be inspect. If not given, the project name specified in the authentication.
				info will be used, or all projects in case this is not given.
			- ``active_only``: Bool flag to report only active (True) VMs or all VMs (False). Default to False.
			- ``use_suffix``: Append a suffix to make service names unique. Default: False (TODO: add the possibility to define custom format from configuration).
			- ``cloud_name``: A name for the OpenStack installation. Default: 'openstack'.
			- ``securitygroups_name``: A name to export the firewalling functionality of Security Groups. Default: 'openstack-securitygropus'.


"""

import logging
import openstack
import ipaddress

from urllib.parse import urlparse


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
from otupy.profiles.ctxd.data.port import Port, IPInfo, IPAddress
from otupy.profiles.ctxd.data.peer_role import PeerRole
from otupy.profiles.ctxd.data.service_type import ServiceType
from otupy.profiles.ctxd.data.network_service import NetworkService
from otupy.profiles.ctxd.data.network import Network
from otupy.profiles.ctxd.data.network_type import NetworkType
from otupy.profiles.ctxd.data.vlan_network import VLANNetwork
from otupy.profiles.ctxd.data.ethernet_network import EthernetNetwork
from otupy.profiles.ctxd.data.endpoint import Endpoint
from otupy.profiles.ctxd.data.vm import VM
from otupy.types.data.hostname import Hostname
from otupy.types.data.l4_protocol import L4Protocol

from otupy import ArrayOf, Nsid, Version,Actions, Response, StatusCode, StatusCodeDescription, Features, ResponseType, Feature, actuator_implementation, IPv4Net, IPv6Net
from otupy.types.data import IPv4Addr, IPv6Addr
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

		self.project=auth['project_name'] if 'project_name' in auth else None
		self.domain=auth['project_domain_name'] if 'project_domain_name' in auth else None
		self.dns="."+kwargs['config']['dns'] if 'config' in kwargs and 'dns' in kwargs['config'] else  "."+urlparse(auth['auth_url']).hostname
		self.projects_config = kwargs['config']['projects'] if 'config' in kwargs and 'projects' in kwargs['config'] else None
		self.active_only = kwargs['config']['active_only'] if 'config' in kwargs and 'active_only' in kwargs['config'] else False
		self.use_suffix = kwargs['config']['use_suffix'] if 'config' in kwargs and 'use_suffix' in kwargs['config'] else False
		self.sg = kwargs['config']['securitygroups_name'] if 'config' in kwargs and 'securitygropus_name' in kwargs['config'] else  "openstack-securitygroups"
		self.cloud = kwargs['config']['cloud_name'] if 'config' in kwargs and 'cloud_name' in kwargs['config'] else  "openstack"


		self._connect_to_openstack()

	def discover_context(self):
		""" Discover services and links

			Implements the base class interface to update services and links
		"""
		# Retrieve all necessary data here, to optimize the execution
		# (OpenStack APIs take time
		self.cloud_region = self._openstack_region_list()['id']
		self.cloud_projects = self._openstack_project_list()

		self.cloud_services = self._openstack_service_list()
		self.cloud_endpoints = self._openstack_endpoint_list()
		self.cloud_hypervisors = self._openstack_hypervisor_list()
		self.cloud_vms = self._openstack_server_list()
		self.cloud_ports = self._openstack_port_list()
		self.cloud_subnets = self._openstack_subnet_list()
		self.cloud_nets = self._openstack_network_list()

		self.discover_services()
		self.discover_links()

	def discover_services(self):
		""" Discover all services related to OpenStack

			OpenStack is a complex framework, where a bundle of applications create and manage virtual resources,
			including VMs, networks, image repositories.
		"""
		self._discover_os_services()
		self._discover_os_servers()
		self._discover_os_hypervisors()		
		self._discover_os_networks()
		# TODO: Discover:
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
		self._discover_vms_link_networks()
		self._discover_sg_link_vms()


	def _discover_os_services(self):
		""" Discover Openstack as a composite service made of multiple applications """
		cloud_subservices = ArrayOf(Name)()

		# Software components of openstack
		# Map OpenStack meta-services (nova, cinder, ...) to their endpoints (URLs) 
		# -------------------------------------------------------------------------
		for service in self.cloud_services:
			eps = self._get_openstack_endpoints(service['id'])
			endpoints=ArrayOf(Endpoint)()
			for e in eps:
				endpoints.append( Endpoint(description=service['type'], endpoint_type=e['interface'],transfer="HTTP", 
					uri=e['url'], owner=service['name']) )

			srv = NetworkService(name=service['name'], description=service['description'], id=service['id'],
					type=service['type'], endpoints=endpoints)

			logger.debug("Found openstack service: %s", str(srv.name))
			# TODO: Add software release (maybe with its SBOM)
			if self.use_suffix:
				name=Name(srv.name+"@"+self.cloud_region+self.dns)
			else:
				name=Name(srv.name)
			# TODO: Add applications running on the controller/compute nodes as subservices
			# (This requires to identifies all applications and to select proper identifiers; 
			#  probably it is simpler to retrieve them from a specific actuator
			self.services.append(Service(name=name, type=ServiceType(srv), #links=ArrayOf(Link)(),
						subservices=ArrayOf(Service)(), owner=self.owner, release=None))
			cloud_subservices.append(name)

		# The root service: OpenStack as cloud environment (meta-service including concrete applications)
		# openstack = { nova, neutron, glance, ... }
		# ------------------------------------------------------------------------------------------------
		os = Cloud(description='cloud', id=None, name=self.cloud, type='IaaS')
		# TODO: Fill in with Openstack version/release
		if self.use_suffix:
			name=Name(os.name+"@"+self.cloud_region+self.dns)
		else:
			name=Name(os.name)
		self.services.append(Service(name=name,type=ServiceType(os), #links=ArrayOf(Name)(),
				subservices=cloud_subservices, owner=self.owner, release=None))

		
	def _discover_os_servers(self):
		""" Discover VMs created and controlled by this OpenStack instance.

			VMs are known as "servers" in OpenStack terminology.
		"""

		# Servers (VMs) deployed by this instance of OpenStack
		# ----------------------------------------------------
		for vm in self.cloud_vms:
			vm_ports = self._get_openstack_ports( vm['id'])
			
			ifaces = ArrayOf(Port)()
			for p in vm_ports:
				ips = ArrayOf(IPInfo)()
				for a in p['fixed_ips']:
					try:
						subnet=self._get_openstack_subnet(a['subnet_id'])
						prefix=ipaddress.ip_network(subnet['cidr']).prefixlen if 'cidr' in subnet else 32
						gw=subnet['gateway_ip'] if 'gateway_ip' in subnet else None
					except:
						prefix=None
						gw=None
					try:
						ips.append( IPInfo(ip=a['ip_address'], prefix=prefix, gw=gw))
					except Exception as e:
						logger.error("Unable to add ip address: ", e)


				ifaces.append(Port(description=p['description'], id=p['id'], iface=None, ips=ips))

			server = VM(vm['description'],
							id= vm['id'], 
							name= vm['name'],
							image = vm['image']['id'],
							ports = ifaces)

			logger.debug("Found server: %s", str(server))

			for p in self.cloud_projects:
				if vm['project_id'] == p['id']:
					project = p['name']
					domain = p['domain_id']
			if self.use_suffix:
				name=Name(server.name+"@"+self.cloud_region+self.dns)
			else:
				name=Name(str(server.name))
			self.services.append(Service(name=name, type=ServiceType(server), #links=ArrayOf(Name)(),
					domain=domain, namespace=project,
						subservices=None, owner=self.owner, release=None))


			
	def _discover_os_hypervisors(self):
		""" Discover OpenStack hypervisors

			Hypervisors are the physical servers that host VMs. It is questionable if such service 
			should be reported, since the Computer subsystem should have its own actuator describing 
			the full stack of services/software hosted.
		"""
		# Hypervisors running VMs in the cloud infrastructure
		# ---------------------------------------------------
		for h in self.cloud_hypervisors:
			hyper = Computer(hostname=Hostname(h['name']), id=h['service_details']['id'],
					description="OpenStack hypervisor")

			logger.debug("Found hypervisor: %s", str(hyper))

#			self.services.append(Service(name=Name(str(h['name'])), type=ServiceType(hyper), #links=ArrayOf(Name)(),
#						subservices=None, owner=self.owner, release=None))


	def _discover_os_networks(self):
		""" Discover OpenStack networks

			Discover networks 
		"""
		for n in self.cloud_nets:
			ip4nets = ArrayOf(IPv4Net)()
			ip6nets = ArrayOf(IPv6Net)()
			try: 
				project=self._get_openstack_project(n['project_id'])['name']
			except:
				project=None
			for sub in n['subnet_ids']:
				try:
					subnet=self._get_openstack_subnet(sub)
					if subnet['ip_version'] == 4:
						ip4nets.append(subnet['cidr'])
					else:
						ip6nets.append(subnet['cidr'])
				except:
					pass

			description="OpenStack network ("+n['description']+")"
			match n['provider_network_type']:
				case 'flat':
					eth = EthernetNetwork({'netv4nets': ip4nets, 'netv6nets': ip6nets})
					net = Network(name=n['name'], description=description,
						id=n['id'], type=NetworkType(eth))

				case 'vlan':
					vlan = VLANNetwork({'vlan_id': n['provider_segmentation_id'],
						'netv4nets': ip4nets, 'netv6nets': ip6nets})
					net = Network(name=n['name'], description=description,
						id=n['id'], type=NetworkType(vlan))

				case _:
					logger.warn("Unmanaged network type: %s", n['provider_network_type'])


			if self.use_suffix:
				name=Name(n['name']+"@"+self.cloud_region+self.dns)
			else:
				name=Name(n['name'])
			self.services.append(Service(name=name, type=ServiceType(net),
					domain=self.domain, namespace=project,
					subservices=ArrayOf(Name)(), owner=self.owner, release=n['updated_at']))




	def _discover_os_link_vms(self):
		""" Add links between nova and VMs 
		
			We create explicit links from nova because this is the software components that concretely
			manage VMs. Vulnerabilities applies to nova and other services rather than OpenStack as a whole.	
		"""

		os_services = self.get_services(filter=NetworkService)
		os_vms = self.get_services(filter=VM)

		# There will be only 1 nova instance, since we are connected to a single openstack cloud
		for s in os_services:
			if s.type.getObj().type == "compute":
				for v in os_vms:
					peer = Peer(service_name= v.name,
								role= PeerRole.controlled)  #VM is controlled by Openstack
					description="Openstack controls "+v.name.getObj()
					self.links.append(Link(name = s.name, description=description, 
								link_type=LinkType.controlling, role=PeerRole.control, peers=ArrayOf(Peer)([peer])))

				
	def _discover_os_link_sg(self):
		""" Add link between OpenStack (neutron) and Security Groups

			Security Groups implement a slpf firewall, hence they are a security function. However, they are not
			standalone software, and they are implemented by neutron.
		"""
		os_services = self.get_services(filter=NetworkService)

		# There will be only 1 nova instance, since we are connected to a single openstack cloud
		for s in os_services:
			if s.type.getObj().type == "network":
				consumer = self.get_consumer(Name(self.sg))
				if self.use_suffix:
					name=Name(self.sg+"@"+self.cloud_region+self.dns)
				else:
					name=Name(self.sg)
				if s is not None:
					peer = Peer(service_name=name,
							role=PeerRole.controlled, consumer=consumer)
					description="OpenStack Security Groups"
					self.links.append(Link(name = s.name, description=description, role=PeerRole.control,
								link_type=LinkType.controlling, peers=ArrayOf(Peer)([peer])))


	def _discover_vms_link_hypervisors(self):
		""" Add links between VMs and hypervisors that host them

			Currently these links are returned by `_discover_servers` to avoid duplicating
			the OpenStack query (which takes time)
		"""	
		hypervisors = self._openstack_hypervisor_list()
		os_vms = self.get_services(filter=VM)

		for v in os_vms:
			vmdetails = self._get_openstack_server(v.type.getObj().id)
			if vmdetails is not None:
				hp_name = vmdetails['hypervisor_hostname']
				description="OpenStack server "+str(v.name)+" hosted on "+ hp_name
				consumer = self.get_consumer(hp_name)
				peer = Peer(service_name=Name(vmdetails['hypervisor_hostname']), 
						role=PeerRole.host, consumer=consumer)

				self.links.append(Link(name=v.name, description=description, role=PeerRole.guest,
							link_type=LinkType.hosting, peers=ArrayOf(Peer)([peer])))


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
				self.links.append(Link(name = v.name, description=description, role=PeerRole.guest,
							link_type=LinkType.hosting, peers=ArrayOf(Peer)([peer])))

	def _discover_vms_link_networks(self):
		""" Add links from VMs to attached networks """

		vms = self.get_services(filter=VM)

		for v in vms:
			for p in v.type.getObj().ports:
				net_id = self._get_openstack_port(p.id)['network_id']
				try:
					net = self._get_openstack_net(net_id)
					project = self._get_openstack_project(net['project_id'])['name']
					nets = self.get_services(name=Name(net['name']), namespace=project, filter=Network)
					
				except:
					nets = None

				for n in nets:
					peer = Peer(service_name= n.name,
								role= PeerRole.forwarding,
								consumer=None) 
					description="VM " + str(v.name) + " attached to network "+str(n.name)
					self.links.append(Link(name = v.name, description=description, role=PeerRole.endpoint,
								link_type=LinkType.packet_flow, peers=ArrayOf(Peer)([peer])))


	def _discover_sg_link_vms(self):
		""" Add links from Security Groups to VMs's ports

			Automatically add a link from Security Group service and all VMs. 
			Security groups are modelled as a security function implemented by an external actuator.
			They protect all VMs hosted in OpenStack.
		"""
		os_vms = self.get_services(filter=VM)

		sg = Name(self.sg)
		for v in os_vms:
			consumer=self.get_consumer(sg)

			if consumer is not None:
				peer = Peer(service_name= v.name,
							role= PeerRole.protected,  #VM is controlled by Openstack
							consumer=consumer) # This is the consumer running on that service.
				description="OpenStack Security Groups protect "+v.name.getObj()
				self.links.append(Link(name = sg, description=description,  role=PeerRole.protect,
							link_type=LinkType.protecting, peers=ArrayOf(Peer)([peer])))




	
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
				logger.debug("Token: %s", token)
			else:
				logger.error("Authentication failed.")
    
		except Exception as e:
			logger.error(f"Connection error: {e}")
			self.conn = None

	def _check_connection(self):
		if not self.conn:
			logger.error("Connection to OpenStack is not established.")
			raise ConnectionError
	
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
			logger.warning("Failed to retrieve service list: %s", e)
			return []
		
		# Format the response as a JSON-like structure for pretty printing
		return self._format_os_data(services)
		
	def _openstack_endpoint_list(self):
		""" Retrieve list of OpenStack service endpoints """
		self._check_connection()

		try:
			# List endpoints available in OpenStack
			endpoints = self.conn.identity.endpoints()
		except Exception as e:
			logger.warn("Failed to retrieve endpoint list: %s", e)
			return []

		return self._format_os_data(endpoints)

	def _openstack_region_list(self):
		""" Retrieve region list

			Currently only one region is supported by this implementation
		"""
		print("Checking connections")
		self._check_connection()
		print("Why didn't trigger?")

		try:
			regions = self.conn.identity.regions()
		except Exception as e:
			logger.warn("Failed to retrieve region list: %s", e)
			return []

		regs = self._format_os_data(regions)
		assert len(regs) == 1 
		return regs[0]
		
	def _openstack_project_list(self):
		""" Retrieve project list

			This is highly inefficient. Future implementations should cache the 
			result for the whole duration of the discovery functions
		"""
		self._check_connection()

		try:
			all_projects = self._format_os_data(self.conn.identity.projects())
			# Filter projects according to configuration
			
			if self.projects_config is not None: # We have a specific list of projects
				projects = [x for x in all_projects if x['name'] in self.projects_config]
			elif self.project is not None: # No explicit project list given, check if a project is given in authentication
				projects = [x for x in all_projects if x['name'] == self.project]
			else: # If neither of the two is given, keep the whole project list (it will be slower to retrieve the server list)
				projects = all_projects

		except Exception as e:
			logger.warn("Failed to retrieve project list: %s", e)
			return []

		return projects
		

	def _openstack_server_list(self):
		""" Retrieve list of servers (VMs) from OpenStack APIs """
		self._check_connection()

		try:
			# Use the OpenStack client to list active servers
			# This is faster, but cannot get servers from all projects
			if self.projects_config is None and self.project is not None:
#servers = self.conn.compute.servers(details=True, status="ACTIVE")
				s = self.conn.compute.servers(details=True)
				servers = self._format_os_data(s)
			else:
			# This looks slower, but gets everything
				servers = []
				all_servers = self.conn.list_servers(all_projects=True)
				for x in all_servers:
					for p in self.cloud_projects:
						if x['project_id'] == p['id']:
							servers.append(x)
	
		except Exception as e:
			logger.warning("Failed to retrieve server list: %s", e)
			servers = []

      # Return the formatted server list as a pretty-printed JSON string
		return servers
		
	def _openstack_hypervisor_list(self):
		""" Retrieve list of hypervisors (servers) from OpenStack APIs """
		self._check_connection()

		try:
			# Use the OpenStack client to list hypervisors
			hypervisors = self.conn.compute.hypervisors(details=True) # No filters set
			# Note: this API is not documented
		except Exception as e:
			logger.warning("Failed to retrieve hypervisors list: %s", e)
			return []

     	# Return the formatted server list as a pretty-printed JSON string
		return self._format_os_data(hypervisors)

	def _openstack_network_list(self):
		""" Retrieve list of hypervisors (servers) from OpenStack APIs """
		self._check_connection()

		try:
			networks = []
			nets = self.conn.network.networks() 
			for n in self._format_os_data(nets):
				for p in self.cloud_projects:
					if n['project_id'] == p['id']:
						networks.append(n)

		except Exception as e:
			logger.warning("Failed to retrieve network list: %s", e)
			return []

     	# Return the formatted server list as a pretty-printed JSON string
		return networks
#		return self._format_os_data(nets)

	def _openstack_subnet_list(self):
		""" Retrieve list of subnets from OpenStack APIs """
		self._check_connection()

		try:
			# Use the OpenStack client to list hypervisors
			subnets = self.conn.network.subnets() # No filters set
		except Exception as e:
			logger.warning("Failed to retrieve subnet list: %s", e)
			return []

     	# Return the formatted server list as a pretty-printed JSON string
		return self._format_os_data(subnets)

	def _openstack_port_list(self):
		""" Retrieve list of subnets from OpenStack APIs """
		self._check_connection()

		try:
			# Use the OpenStack client to list hypervisors
			ports = self.conn.network.ports() # No filters set
		except Exception as e:
			logger.warning("Failed to retrieve subnet list: %s", e)
			return []

     	# Return the formatted server list as a pretty-printed JSON string
		return self._format_os_data(ports)



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

	def _get_openstack_endpoints(self, service_id):
		""" Retrieve the endpoints from a list for a specific service_id """
		ep = []
		for e in self.cloud_endpoints:
			if e['service_id'] == service_id:
				ep.append(e)
		return ep

	def _get_openstack_project(self, project_id):
		""" Retrieve the project from a list """
		for p in self.cloud_projects:
			if p['id'] == project_id:
				return p

		return None
		
	def _get_openstack_server(self, server_id):
		""" Retrieve the server from a list """
		for v in self.cloud_vms:
			print("******* ", v['id'], " -> ", server_id)
			try:
				if v['id'] == server_id:
					return v
			except Exception as e:
			 	print("katia zoccola: ", e)

		print("not found")
		return None
		
	def _get_openstack_subnet(self, subnet_id):
		""" Retrieve the subnets from a list """
		for s in self.cloud_subnets:
			if s['id'] == subnet_id:
				return s

	def _get_openstack_net(self, net_id):
		""" Retrieve the network from a list """
		for n in self.cloud_nets:
			if n['id'] == net_id:
				return n

		return None

	def _get_openstack_ports(self, vm_id):
		""" Retrieve the ports from a list for a given server (VM)"""
		ports = []
		for p in self.cloud_ports:
			if p['device_id'] == vm_id:
				ports.append(p)

		return ports

	def _get_openstack_port(self, port_id):
		""" Retrieve the port from a list """
		for p in self.cloud_ports:
			if p['id'] == port_id:
				return p

