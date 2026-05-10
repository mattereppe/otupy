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
import re

from urllib.parse import urlparse, urlsplit


import otupy.profiles
from otupy import Extensions

from otupy.actuators.xbom.base_xbom_actuator import XBOMActuator
from otupy.models.ctxd import *

from otupy.profiles.ctxd import *

from otupy import ArrayOf, Nsid, Version,Actions, Response, StatusCode, StatusCodeDescription, Features, ResponseType, Feature, actuator_implementation, IPv4Net, IPv6Net, Hostname, L4Protocol, IPv4Addr, IPv6Addr
import otupy.profiles.ctxd as ctxd


logger = logging.getLogger(__name__)

@actuator_implementation("xbom-openstack")
class XBOMOpenStackActuator(XBOMActuator):
	""" Openstack Actuator Manager

		Extend the base `XBOMActuator` to retrieve services and links for a Openstack cluster. Currently discovery is mostly limited to vms,
		hypervisors, and OpenStack sw components. It should be extended in future releases with additional resources (e.g., networks, ports).


	"""

	def __init__(self, auth, **kwargs):
		""" Initialize the actuator

			:param auth: (mandatory) Authentication information to connect to OpenStack.
			:param config: (optional) Include additional info for configuration the OpenStack 
				connection (e.g., "cacert" certificate of a custom CA).
			:param specifiers: (optional) The identification of this Actuator.
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

		self.conn = None
		try:
			self._connect_to_openstack()
		except Exception as e:
			logger.error(f"Connection to OpenStack failed: {e}")


	def discover_context(self):
		""" Discover services and links

			Implements the base class interface to update services and links
		"""
		# Retrieve all necessary data here, to optimize the execution
		# (OpenStack APIs take time
		self.cloud_region = self._openstack_region_list()['id']
		self.cloud_projects = self._openstack_project_list()
		self.cloud_domains = self._openstack_domain_list()

		self.cloud_services = self._openstack_service_list()
		self.cloud_endpoints = self._openstack_endpoint_list()
		self.cloud_hypervisors = self._openstack_hypervisor_list()
		self.cloud_vms = self._openstack_server_list()
		self.cloud_ports = self._openstack_port_list()
		self.cloud_subnets = self._openstack_subnet_list()
		self.cloud_nets = self._openstack_network_list()
		self.cloud_routers = self._openstack_router_list()

		self.discover_services()
		self.discover_links()

	def discover_services(self):
		""" Discover all services related to OpenStack

			OpenStack is a complex framework, where a bundle of applications create and manage virtual resources,
			including VMs, networks, image repositories.
		"""
		logger.debug("Discovering services...")
		self._discover_os_services()
		logger.debug("Discovering servers...")
		self._discover_os_servers()
		logger.debug("Discovering hypervisors...")
		self._discover_os_hypervisors()		
		logger.debug("Discovering networks...")
		self._discover_os_networks()
		logger.debug("Discovering routers...")
		self._discover_os_routers()
		# TODO: Discover:
		# - images
		

	def discover_links(self):
		""" Automatically discover links between OpenStack components

			The current implementation discovers links between:
			- OpenStack services (nove) and VMs (servers)
			- VMs (servers) and physical servers (hypervisors)
			- SLPF firewall (iptables) and VMs (servers)
			- VMs (servers) and ExecutionEnvironment (System and application software), only from a configuration file
		"""
		logger.debug("Discovering OpenStack links to servers...")
		self._discover_os_link_vms()
		logger.debug("Discovering OpenStack links to security group...")
		self._discover_os_link_sg()
		logger.debug("Discovering OpenStack links to networks...")
		self._discover_os_link_networks()
		logger.debug("Discovering OpenStack links to network functions...")
		self._discover_os_link_networkfunctions()
		logger.debug("Discovering OpenStack links to hypervisors...")
		self._discover_vms_link_hypervisors()
		logger.debug("Discovering server links to networks...")
		self._discover_vms_link_networks()
		logger.debug("Discovering routers links to controllers and networks...")
		self._discover_routers_link_controllers_and_networks()
		logger.debug("Discovering networks links to controllers...")
		self._discover_networks_link_controllers()
		logger.debug("Discovering execenvs links to servers...")
		self._discover_execenvs_link_vms()
		logger.debug("Discovering security group links to servers...")
		self._discover_sg_link_vms()


	def _discover_os_services(self):
		""" Discover Openstack as a composite service made of multiple applications """
		cloud_subservices = ArrayOf(SId)()

		# Software components of openstack
		# Map OpenStack meta-services (nova, cinder, ...) to their endpoints (URLs) 
		# -------------------------------------------------------------------------
		for service in self.cloud_services:
			eps = self._get_openstack_endpoints(service['id'])
			version = self._get_openstack_versions(service['id'])
			endpoints=ArrayOf(Endpoint)()
			for e in eps:
				endpoints.append( Endpoint(description=service['type'], endpoint_type=e['interface'],transfer="HTTP", 
					uri=e['url'], provider=service['name']) )

			srv = API(name=service['name'], description=service['description'], id=service['id'],
					type=service['type'], endpoints=endpoints)
			# TODO: Discover service versions (_openstack_versions_show())

			logger.debug("Found openstack service: %s", str(srv.name))
			# TODO: Add software release (maybe with its SBOM)
			name=Name(self._os_dns_name(srv.name))
			sid=SId.create_from_service_type(srv, domain=self.cloud_region)
			# TODO: Add applications running on the controller/compute nodes as subservices
			# (This requires to identifies all applications and to select proper identifiers; 
			#  probably it is simpler to retrieve them from a specific actuator
			self.services.append(Service(name=name, sid=sid, type=ServiceType(srv), 
						subservices=ArrayOf(SId)(), owner=self.owner, release=None))
			cloud_subservices.append(sid)

		# The root service: OpenStack as cloud environment (meta-service including concrete applications)
		# openstack = { nova, neutron, glance, ... }
		# ------------------------------------------------------------------------------------------------
		os = Cloud(description='cloud', id=None, name=self.cloud, type='os')
		# TODO: Fill in with Openstack version/release
		name=Name(self._os_dns_name(os.name))
		self.services.append(Service(name=name, sid=SId.create_from_service_type(os), type=ServiceType(os), 
				subservices=cloud_subservices, owner=self.owner, release=None))

		
	def _discover_os_servers(self):
		""" Discover VMs created and controlled by this OpenStack instance.

			VMs are known as "servers" in OpenStack terminology.
		"""

		# Servers (VMs) deployed by this instance of OpenStack
		# ----------------------------------------------------
		for vm in self.cloud_vms:
			vm_ports = self._get_openstack_ports( vm['id'])
			
			ifaces = ArrayOf(NetworkInterface)()
			for p in vm_ports:
				ips = ArrayOf(IPInfo)()
				for a in p['fixed_ips']:
					prefix, gw = self._parse_openstack_fixed_ips(a)
					try:
						ips.append( IPInfo(ip=a['ip_address'], prefix=prefix, gw=gw))
					except Exception as e:
						logger.error("Unable to add ip address: ", e)


				ifaces.append(NetworkInterface(description=p['description'], id=p['id'], iface=None, ips=ips))

			netnode = NetworkNode(name=vm['name'], description="Openstack ports", ifaces=ifaces)

			server = Host(name= vm['name'],
							id= vm['id'], 
							description=vm['description'],
							type=HostType(VM(image = vm['image']['id'])))
			

			logger.debug("Found server: %s", str(server))
			logger.debug("with ports: %s", str(netnode))

			project, domain = self._get_openstack_project_and_domain(vm['project_id'])

			name=Name(self._os_dns_name(server.name))
			netnode_name=Name(server.name+".ports")
			netnode_sid=SId.create_from_service_type(netnode, domain=domain, namespace=project)
			
			vm_service = Service(name=name, sid=SId.create_from_service_type(server, domain=domain, namespace=project), 
					domain=domain, namespace=project,
					type=ServiceType(server), 
						subservices=ArrayOf(SId)(), owner=self.owner, release=None)
			self.services.append(vm_service)

			# Add ports service
			self.services.append(Service(name=netnode_name, sid=netnode_sid,
						domain=domain, namespace=project,
						type=ServiceType(netnode),
						subservices=ArrayOf(SId)(), owner=str(name), release=None))
			vm_service.subservices.append(netnode_sid)
			


			
	def _discover_os_hypervisors(self):
		""" Discover OpenStack hypervisors

			Hypervisors are the physical servers that host VMs. 
		"""
		# Hypervisors running VMs in the cloud infrastructure
		# ---------------------------------------------------
		for h in self.cloud_hypervisors:
			hyper = ExecutionEnvironment(name=Hostname(h['name']), id=h['service_details']['id'],
					description="OpenStack hypervisor", type=ExecutionEnvironmentType(OS()) )

			logger.debug("Found hypervisor: %s", str(hyper))

			self.services.append(Service(name=Name(str(h['name'])), sid=SId.create_from_service_type(hyper),
						type=ServiceType(hyper), 
						subservices=None, owner=self.owner, release=None))


	def _discover_os_networks(self):
		""" Discover OpenStack networks

			Discover networks 
		"""
		for n in self.cloud_nets:
			ipnets = ArrayOf(IPNetAddress)()
#			ip4nets = ArrayOf(IPv4Net)()
#			ip6nets = ArrayOf(IPv6Net)()
			project, domain = self._get_openstack_project_and_domain(n['project_id'])
			for sub in n['subnet_ids']:
				try:
					subnet=self._get_openstack_subnet(sub)
					ipnets.append(ipaddress.ip_network(subnet['cidr']))
#					if subnet['ip_version'] == 4:
#						ip4nets.append(subnet['cidr'])
#					else:
#						ip6nets.append(subnet['cidr'])
				except:
					pass

			description="OpenStack network ("+n['description']+")"
			match n['provider_network_type']:
				case 'flat':
					eth = EthernetNetwork({'nets': ipnets})
#					eth = EthernetNetwork({'netv4nets': ip4nets, 'netv6nets': ip6nets})
					net = Network(name=n['name'], description=description,
						id=n['id'], type=NetworkType(eth))

				case 'vlan':
					vlan = VLANNetwork({'vlan_id': n['provider_segmentation_id'],
						'nets': ipnets})
					net = Network(name=n['name'], description=description,
						id=n['id'], type=NetworkType(vlan))

				case _:
					logger.warn("Unmanaged network type: %s", n['provider_network_type'])


			name=Name(self._os_dns_name(n['name']))
			self.services.append(Service(name=name, sid=SId.create_from_service_type(net, domain=domain, namespace=project),
					domain=domain, namespace=project,
					type=ServiceType(net),
					subservices=ArrayOf(SId)(), owner=self.owner, release=n['updated_at']))


	def _discover_os_routers(self):
		""" Add a network service for each router
		"""
		for r in self.cloud_routers:
		
			# The "gateway" is a default router not explicitely listed
			ips = ArrayOf(IPInfo)()
			routes = []
			for a in r['external_gateway_info']['external_fixed_ips']:
				prefix, gw = self._parse_openstack_fixed_ips(a)
				routes.append("Default via "+gw+" src "+a['ip_address'])
			routes.append(r['routes'])
			
			# First, create network function for the router
			router = NetworkFunction(name=r['name'], id=r['id'], description=r['description'],
				type=NetworkFunctionType(Router({'routes': routes})), version=r['revision_number'] )
			project, domain = self._get_openstack_project_and_domain(r['project_id'])

			router_name=Name(self._os_dns_name(r['name']))
			router_service=Service(name=router_name, sid=SId.create_from_service_type(router, domain=domain, namespace=project),
					domain=domain, namespace=project,
					type=ServiceType(router),
					subservices=ArrayOf(SId)(), owner=self.owner, release=r['updated_at'])
			self.services.append(router_service)

			# Second, create a network node that hosts the network function
			ifaces = ArrayOf(NetworkInterface)()
			router_ports = self._get_openstack_ports( r['id'])
			ports_name=Name(self._os_dns_name(r['name']+".ports"))
			for p in router_ports:
				ips = ArrayOf(IPInfo)()
				for a in p['fixed_ips']:
					prefix, gw = self._parse_openstack_fixed_ips(a)
					try:
						ips.append( IPInfo(ip=a['ip_address'], prefix=prefix, gw=gw))
					except Exception as e:
						logger.error("Unable to add ip address for router: ", e)
				ifaces.append(NetworkInterface(description=p['description'], id=p['id'], iface=None, ips=ips))

			node = NetworkNode(name=r['name'],
							id=None, 
							description="Network ports of Router "+str(router_name),
							ifaces = ifaces)
			ports_sid=SId.create_from_service_type(node, domain=domain, namespace=project)

			self.services.append(Service(name=ports_name, sid=ports_sid,
					domain=domain, namespace=project,
					type=ServiceType(node),
					subservices=None, owner=self.owner, release=r['updated_at']))

			# Add ports as subservice of the Router 
			router_service.subservices.append(ports_sid)


	def _discover_os_link_vms(self):
		""" Add links between nova and VMs 
		
			We create explicit links from nova because this is the software components that concretely
			manage VMs. Vulnerabilities applies to nova and other services rather than OpenStack as a whole.	
		"""

		os_services = self.get_services(filter=API)
#os_vms = self.get_services(filter=VM)
		os_vms = self.get_services_by_sid(SId(type=ServiceType.get_type_name(Host), subtype=HostType.get_type_name(VM)))

		# There will be only 1 nova instance, since we are connected to a single openstack cloud
		for s in os_services:
			if s.type.getObj().type == "compute":
				for v in os_vms:
					peer = Peer(service_name= v.name, sid=v.sid,
								role= PeerRole.controlled)  #VM is controlled by Openstack
					description="Openstack controls "+v.name.getObj()
					self.links.append(Link(name = s.name, sid=s.sid, description=description, 
								link_type=LinkType.controlling, role=PeerRole.control, peers=ArrayOf(Peer)([peer])))


	def _discover_os_link_networks(self):
		""" Add links between neutron and networks

			We create explicit links from neutron because it controls network configuration.
		"""
		os_services = self.get_services(filter=API)
		os_networks = self.get_services(filter=Network)

		# There will be only 1 nova instance, since we are connected to a single openstack cloud
		for s in os_services:
			if s.type.getObj().type == "network":
				for n in os_networks:
					peer = Peer(service_name= n.name, sid=n.sid,
								role= PeerRole.controlled)  #VM is controlled by Openstack
					description="Openstack controls "+n.name.getObj()
					self.links.append(Link(name = s.name, sid=s.sid,  description=description, 
								link_type=LinkType.controlling, role=PeerRole.control, peers=ArrayOf(Peer)([peer])))


	def _discover_os_link_networkfunctions(self):
		""" Add links between neutron and network functions

			We create explicit links from neutron because it controls network functions.
		"""
		os_services = self.get_services(filter=API)
		os_networkfunctions = self.get_services(filter=NetworkFunction)

		# There will be only 1 nova instance, since we are connected to a single openstack cloud
		for s in os_services:
			if s.type.getObj().type == "network":
				for n in os_networkfunctions:
					peer = Peer(service_name= n.name, sid=n.sid,
								role= PeerRole.controlled)  #VM is controlled by Openstack
					description="Openstack controls "+n.name.getObj()
					self.links.append(Link(name = s.name, sid=s.sid, description=description, 
								link_type=LinkType.controlling, role=PeerRole.control, peers=ArrayOf(Peer)([peer])))




	def _discover_os_link_sg(self):
		""" Add link between OpenStack (neutron) and Security Groups

			Security Groups implement a slpf firewall, hence they are a security function. However, they are not
			standalone software, and they are implemented by neutron.
		"""
		os_services = self.get_services(filter=API)

		# There will be only 1 nova instance, since we are connected to a single openstack cloud
		for s in os_services:
			if s.type.getObj().type == "network":
				consumer = self.get_consumer(Name(self.sg))
				name=Name(self._os_dns_name(self.sg))
				if s is not None:
					peer = Peer(service_name=name, sid=self._os_sg_sid(self.sg),
							role=PeerRole.controlled, consumer=consumer)
					description="OpenStack Security Groups"
					self.links.append(Link(name = s.name, sid=s.sid,  description=description, role=PeerRole.control,
								link_type=LinkType.controlling, peers=ArrayOf(Peer)([peer])))



	def _discover_vms_link_hypervisors(self):
		""" Add links between VMs and hypervisors that host them

			Currently these links are returned by `_discover_servers` to avoid duplicating
			the OpenStack query (which takes time)
		"""	
#		hypervisors = self._openstack_hypervisor_list()
#		os_vms = self.get_services(filter=VM)
		os_vms = self.get_services_by_sid(SId(type=ServiceType.get_type_name(Host), subtype=HostType.get_type_name(VM)))

		for v in os_vms:
			vmdetails = self._get_openstack_server(v.type.getObj().id)
			if vmdetails is not None:
				hp_name = vmdetails['hypervisor_hostname']
				description="OpenStack server "+str(v.name)+" hosted on "+ hp_name
				consumer = self.get_consumer(hp_name)
				peer = Peer(service_name=Name(vmdetails['hypervisor_hostname']), 
						sid=SId.create_from_service_type(ExecutionEnvironment(name=vmdetails['hypervisor_hostname'], type=ExecutionEnvironmentType(OS()))),
						role=PeerRole.host, consumer=consumer)

				self.links.append(Link(name=v.name, sid=v.sid, description=description, role=PeerRole.guest,
							link_type=LinkType.hosting, peers=ArrayOf(Peer)([peer])))




	def _discover_vms_link_networks(self):
		""" Add links from VMs to attached networks """

#vms = self.get_services(filter=VM)
		vms = self.get_services_by_sid(SId(type=ServiceType.get_type_name(Host), subtype=HostType.get_type_name(VM)))

		for v in vms:
			if v.subservices is not None:
				for subsid in v.subservices:
					subsrv=self.get_services_by_sid(SId(sid=subsid, domain=v.domain, namespace=v.namespace))
					assert len(subsrv) <= 1
					for s in subsrv:
						if type(s.type.getObj())==NetworkNode:
							for p in s.type.getObj().ifaces:
								net_id = self._get_openstack_port(p.id)['network_id']
								try:
									net = self._get_openstack_net(net_id)
									project = self._get_openstack_project(net['project_id'])['name']
									nets = self.get_services(name=Name(self._os_dns_name(net['name'])), namespace=project, filter=Network)
									
								except:
									nets = None

								for n in nets:
									peer = Peer(service_name= n.name, sid=n.sid,
												role= PeerRole.forwarding,
												consumer=None) 
									description="VM " + str(v.name) + " attached to network "+str(n.name)
									self.links.append(Link(name = v.name, sid=v.sid, description=description, role=PeerRole.endpoint,
												link_type=LinkType.packet_flow, peers=ArrayOf(Peer)([peer])))

		

	def _discover_routers_link_controllers_and_networks(self):
		""" Add links from routers to hosting network nodes 
				Add links from routers to servers hosting the neutron service
		"""
		netfuns = self.get_services_by_sid(SId(type=ServiceType.get_type_name(NetworkFunction)))
		nodes = self.get_services_by_sid(SId(type=ServiceType.get_type_name(NetworkNode)))

		os_services = self.get_services_by_sid(SId(type=ServiceType.get_type_name(API)))

		# There will be only 1 nova instance, since we are connected to a single openstack cloud
		neutron_controllers = []
		for s in os_services:
			if s.type.getObj().type == "network":
				# We assume neutron runs in the node identified by the API (i.e., no proxy)
				for e in s.type.getObj().endpoints:
					hostname=urlsplit(e.uri).hostname
					if hostname not in neutron_controllers:
						neutron_controllers.append(hostname)

		controller_peers = []
		for n in neutron_controllers:
			controller_name=Name(Hostname(n))
			consumer=self.get_consumer(controller_name)
			controller_peers.append( Peer(service_name= controller_name,
						sid=SId.create_from_service_type(ExecutionEnvironment(name=n, type=ExecutionEnvironmentType(OS()))),
						role= PeerRole.host,
						consumer=consumer))

		for r in netfuns:
			if type(r.type.getObj().type.getObj()) == Router:
				if r.subservices is not None:
					for subsid in r.subservices:
						subsrvs = self.get_services_by_sid(subsid)
						assert len(subsrvs) <= 1
						for s in subsrvs:
							if type(s.type.getObj())==NetworkNode:
#					
								# Add link to networks
								for p in s.type.getObj().ifaces:
									net_id = self._get_openstack_port(p.id)['network_id']
									try:
										net = self._get_openstack_net(net_id)
										project = self._get_openstack_project(net['project_id'])['name']
										nets = self.get_services(name=Name(self._os_dns_name(net['name'])), namespace=project, filter=Network)
										
										for w in nets:
											peer = Peer(service_name= w.name, sid=w.sid,
														role= PeerRole.forwarding,
														consumer=None) 
											description="Router " + str(r.name) + " attached to network "+str(w.name)
											self.links.append(Link(name = r.name, sid=r.sid, description=description, role=PeerRole.forwarding,
														link_type=LinkType.packet_flow, peers=ArrayOf(Peer)([peer])))
									except:
										logger.warn("Unable to find net: %s", net_id)

								# Add a link for the underlying network node too
								for p in controller_peers:
									description="Router " + str(r.name) + " hosted on "+str(p.service_name)
									self.links.append(Link(name = r.name, sid=r.sid, description=description, 
												link_type=LinkType.hosting, role=PeerRole.guest, peers=ArrayOf(Peer)([p])))
			

	def _discover_networks_link_controllers(self):
		""" Create link between networks and underlying controllers """

		os_services = self.get_services(filter=API)
		os_nets = self.get_services(filter=Network)

		# There will be only 1 nova instance, since we are connected to a single openstack cloud
		neutron_controllers = []
		for s in os_services:
			if s.type.getObj().type == "network":
				# We assume neutron runs in the node identified by the API (i.e., no proxy)
				for e in s.type.getObj().endpoints:
					hostname=urlsplit(e.uri).hostname
					if hostname not in neutron_controllers:
						neutron_controllers.append(hostname)

		controller_peers = []
		for n in neutron_controllers:
			controller_name=Name(Hostname(n))
			consumer=self.get_consumer(controller_name)
			controller_peers.append( Peer(service_name= controller_name, 
						sid=SId.create_from_service_type(ExecutionEnvironment(name=n, type=ExecutionEnvironmentType(OS()))),
						role= PeerRole.host,
						consumer=consumer))

		for n in os_nets:
			for p in controller_peers:
				description="Network " + str(n.name) + " hosted on "+str(p.service_name)
				self.links.append(Link(name = n.name, sid=n.sid,  description=description, 
							link_type=LinkType.hosting, role=PeerRole.guest, peers=ArrayOf(Peer)([p])))
			

	def _discover_execenvs_link_vms(self):
		""" Add links between VMs and the software they host

			This is something outside the OpenStack scope, which is delegated to a remote peer
			(currently read by configuration file).
		"""
		os_vms = self.get_services_by_sid(SId(type=ServiceType.get_type_name(Host), subtype=HostType.get_type_name(VM)))

		for v in os_vms:
			log = self._openstack_console_show(v.type.getObj().id)
			if log is not None:
				# Look for hostname
				match_host = re.search('^(.*) login', log, re.M)
				if match_host is not None:
					hostname=Name(Hostname(match_host.group(1)))
					# Look for Linux version
					# TODO: Add support for more OSs
					match_version = re.search('.*Linux version ([^ ]*) .*', log, re.M)
					if match_version is not None:
						version=match_version.group(1)
					else:
						version=None
					sid=SId.create_from_service_type(ExecutionEnvironment(name=match_host.group(1), version=version, type=ExecutionEnvironmentType(OS())))
					consumer=self.get_consumer(hostname)
					peer = Peer(service_name=hostname, sid=sid,
							role=PeerRole.guest,
							consumer=consumer)
					# Create the link
					self.links.append(Link(name=v.name, sid=v.sid, description=str(hostname)+" running in "+str(v.name),
								link_type=LinkType.hosting, role=PeerRole.host, peers=ArrayOf(Peer)([peer])))
					# and add as subservice
					v.subservices.append(sid)
			else:
				logger.info("Unable to retrieve execenv for %s (shutdown?)", v.sid)

					



	def _discover_sg_link_vms(self):
		""" Add links from Security Groups to VMs's ports

			Automatically add a link from Security Group service and all VMs. 
			Security groups are modelled as a security function implemented by an external actuator.
			They protect all VMs hosted in OpenStack.
		"""
		os_vms = self.get_services_by_sid(SId(type=ServiceType.get_type_name(Host), subtype=HostType.get_type_name(VM)))

		sg = Name(self.sg)
		for v in os_vms:
			consumer=self.get_consumer(sg)

			peer = Peer(service_name=sg, sid=self._os_sg_sid(self.sg),
								role = PeerRole.protect, consumer=consumer)
			description="OpenStack Security Groups protect "+v.name.getObj()
			self.links.append(Link(name = v.name, sid=v.sid,
						description=description,  role=PeerRole.protected,
						link_type=LinkType.protecting, peers=ArrayOf(Peer)([peer])))



	
	def _connect_to_openstack(self):
		""" Connect to OpenStack

			Get an authentication token from the Identity server that will be used to authenticate requests to OpenStack
			endpoints. 

			This method is designed to be called multiple times (e.g., before invoking any API), so it can recover from
			temporary connection errors. If a connection is already established, it does not waste time to create a new connection.
		"""

		if self.conn is None:
			error = None
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
				error = e
				self.conn = None

		if not self.conn:
			# The rest of the code should be ready to deal with connection errors
			raise ConnectionError(f"Connection to OpenStack failed: {error}")
	
	def _format_os_data(self, data):
			data_list = []
			for d in data:
				 data_list.append( {key: value for key, value in d.to_dict().items()} )
			return data_list


	def _openstack_service_list(self):
		""" Retrieve list of OpenStack services """
		self._connect_to_openstack()
		
		try:
		    # List services available in OpenStack
			services = self.conn.identity.services()
		except Exception as e:
			logger.warning("Failed to retrieve service list: %s", e)
			return []
		
		# Format the response as a JSON-like structure for pretty printing
		return self._format_os_data(services)
		
	def _openstack_versions_show(self):
		""" Retrieve list of OpenStack services """
		self._connect_to_openstack()

		# TODO: what api to get service versions (openstack versions show)???
		
	def _openstack_endpoint_list(self):
		""" Retrieve list of OpenStack service endpoints """
		self._connect_to_openstack()

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
		self._connect_to_openstack()

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

			We need to keep a hidden list of all projects, to get the project name for 
			shared resources that do not belong to the projects selected by configuration
		"""
		self._connect_to_openstack()

		try:
			all_projects = self._format_os_data(self.conn.identity.projects())
			# Filter projects according to configuration
			
			if self.projects_config is not None: # We have a specific list of projects
				projects = [x for x in all_projects if x['name'] in self.projects_config]
			elif self.project is not None: # No explicit project list given, check if a project is given in authentication
				projects = [x for x in all_projects if x['name'] == self.project]
			else: # If neither of the two is given, keep the whole project list (it will be slower to retrieve the server list)
				projects = all_projects
			# Keep track of hidden projects
			self.cloud_hidden_projects = [x for x in all_projects if x not in projects]

		except Exception as e:
			logger.warn("Failed to retrieve project list: %s", e)
			return []

		return projects
		
	def _openstack_domain_list(self):
		self._connect_to_openstack()

		return self._format_os_data(self.conn.identity.domains())

	def _openstack_server_list(self):
		""" Retrieve list of servers (VMs) from OpenStack APIs """
		self._connect_to_openstack()

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
		return [x for x in servers if self.active_only == False or x['status'] == 'ACTIVE']
		
	def _openstack_hypervisor_list(self):
		""" Retrieve list of hypervisors (servers) from OpenStack APIs """
		self._connect_to_openstack()

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
		self._connect_to_openstack()

		try:
			networks = []
			nets = self.conn.network.networks() 
			for n in self._format_os_data(nets):
				for p in self.cloud_projects:
					# Must include shared networks!!!
					if n['project_id'] == p['id'] or n['is_shared']:
						networks.append(n) if n not in networks else networks

		except Exception as e:
			logger.warning("Failed to retrieve network list: %s", e)
			return []

     	# Return the formatted server list as a pretty-printed JSON string
		return networks
#		return self._format_os_data(nets)

	def _openstack_subnet_list(self):
		""" Retrieve list of subnets from OpenStack APIs """
		self._connect_to_openstack()

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
		self._connect_to_openstack()

		try:
			# Use the OpenStack client to list hypervisors
			ports = self.conn.network.ports() # No filters set
		except Exception as e:
			logger.warning("Failed to retrieve subnet list: %s", e)
			return []

     	# Return the formatted server list as a pretty-printed JSON string
		return self._format_os_data(ports)

	def _openstack_console_show(self, server):
		""" Retrieve the messages sent to the console when the VM boots up """
		self._connect_to_openstack()

		try:
			console_log = self.conn.get_server_console(server)
		except Exception as e:
			logger.debug("Failed to get console output for server %s (not running?)", server)
			return None

		return console_log

	def _openstack_router_list(self):
		""" Retrieve list of routers from OpenStack APIs """
		self._connect_to_openstack()

		try:
			routers = []
			rs = self._format_os_data(self.conn.network.routers()) # No filters set
			for r in rs:
				for p in self.cloud_projects:
					if r['project_id'] == p['id']:
						routers.append(r)
		except Exception as e:
			logger.warning("Failed to retrieve router list: %s", e)
			return []

     	# Return the formatted server list as a pretty-printed JSON string
		return routers


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

	def _get_openstack_versions(self, serviceid):
		""" Retrieve the version number of a service id """
		return None
		

	def _get_openstack_project(self, project_id):
		""" Retrieve the project from a list """
		for p in self.cloud_projects:
			if p['id'] == project_id:
				return p
		for p in self.cloud_hidden_projects:
			if p['id'] == project_id:
				return p

		return None
		
	def _get_openstack_domain(self, domain_id):
		""" Retrieve the domain from a list """
		for d in self.cloud_domains:
			if d['id'] == domain_id:
				return d

		return None

	def _get_openstack_server(self, server_id):
		""" Retrieve the server from a list """
		for v in self.cloud_vms:
			if v['id'] == server_id:
				return v

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

	def _parse_openstack_fixed_ips(self, fips):
		""" Parse the fixed_ips structure and returns prefix and gateway """
		try:
			subnet=self._get_openstack_subnet(fips['subnet_id'])
			prefix=ipaddress.ip_network(subnet['cidr']).prefixlen if 'cidr' in subnet else 32
			gw=subnet['gateway_ip'] if 'gateway_ip' in subnet else None

			return prefix, gw
		except:
			return None, None
	
	def _get_openstack_project_and_domain(self, project_id):
		""" Get project and domain name from project_id """
		try: 
			project_data=self._get_openstack_project(project_id)
			project=project_data['name']
			domain=self._get_openstack_domain(project_data['domain_id'])['name']
			return project, domain
		except:
			logger.warning("Unable to find project: %s", r['project_id'])
			return None, None
		
	def _os_dns_name(self, base):
		""" Add common dns suffix according to configuration file """

		if self.use_suffix:
			name=base+"@"+self.cloud_region+self.dns
		else:
			name=base

		return name

	def _os_sg_sid(self, sg):
		""" Provide a common sid for OpenStack security groups """
		return SId.create_from_service_type(NetworkFunction(name=str(sg), type=NetworkFunctionType(Firewall())))
