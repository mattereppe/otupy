""" Host XBOM Actuator
	
    The Host actuaotr is intended to discover the host hardware and its 
    operating system. It it designed to run in the execution environment 
    itself, because there is no other way to query the OS's APIs.

    The current implementation is for demonstration purposes only and makes
    intensive usage of shell commands. Future releases should improve
    by using better Python libraries for the same purpose. 

    We currently do not discover harware components. This is left for future
    work, since we do not cover hardware vulnerabilities in MIRANDA.

	The actuator-specific configuration includes:

		- ``services``: A list of service definitions, given as yaml descriptions
			of the corresponding data components in the ``Service`` class.
			
		- ``links``: A list of link definitions, given as yaml descriptions
			of the correponsing data component in the ``Links`` class.
"""	

import logging
import subprocess
import platform
import pyroute2
import ipaddress
import json
import yaml
import os
import pybrctl
import copy
import datetime
import grpc

from containerd.services.containers.v1 import containers_pb2_grpc, containers_pb2

from otupy import ArrayOf, actuator_implementation, Hostname, MACAddr

from otupy.actuators.xbom.xbom_actuator import XBOMActuator
from otupy.profiles.xbom import *



logger = logging.getLogger(__name__)

DPKG_LIST=['dpkg','--list']
KUBELET_CONFIG_FILE='/var/lib/kubelet/config.yaml'

@actuator_implementation("xbom-host")
class XBOMActuator_host(XBOMActuator):
	""" Host Actuator Manager

		Extend the base `CTDXActuator` to retrieve the description of the Operating System
        environment. This includes the connections between its (network) namespaces


	"""

	def __init__(self, **kwargs):
		""" Initialize the actuator

		"""
		self.platform = None # Keep an internal reference to the ExecutionEnvironment of this host

		self.kube_namespaces = kwargs['kubernetes']['namespaces'] if 'kubernetes' in kwargs and 'namespaces' in kwargs['kubernetes'] else None
		kube_use_suffix = kwargs['kubernetes']['use_suffix'] if 'kubernetes' in kwargs and 'use_suffix' in kwargs['kubernetes'] else True # This is the safe option to link to external service names
		kube_kubelet_config = kwargs['kubernetes']['kubelet_config'] if 'kubernetes' in kwargs and 'kubelet_config' in kwargs['kubernetes'] else KUBELET_CONFIG_FILE
		if kube_use_suffix is True:
			self.kube_suffix = "."+kwargs['kubernetes']['suffix'] if 'kubernetes' in kwargs and 'suffix' in kwargs['kubernetes'] else self._get_kube_suffix(kube_kubelet_config)
		else:
			self.kube_suffix = ""

		# Ensure the platform service is always available
		self.services = ArrayOf(Service)()
		self._discover_platform()


	def discover_context(self):
		""" Discover services and links

			Services are reset any time the update_context is invoked. 

			Discovering the properties and connections between namespaces is tricky, especially due to
			the large number of different virtual network relationships and the way they are retrieved 
			with netlink. To optimize the code, we save
			namespace-related properties and links in an internal structure as soon as they are discovered.

			Most of the information is kept in the self._namespaces member, which is organized in this way
			(yaml-like syntax):

			self._namespaces:
				<name>:
					name:					# This is a duplication of the main key, but it is necessary to give
						<name>			# a name to the main ExecutionEnvironment (key=``None``)
					netnsmap: 			# A mapping between ids and netns names. This map has local-scope only,
						<id>				# since the ids are different in each namespace, and each namespace
							<name>		# has only visibility over other namespaces it is connected to.
					ifaces:				# A mapping between idx and inteface names. This map has local-scope
						<idx>				# only, since the idx are not unique.
							<name>
					ifaces_idx:			# Similar maps as before, but reversed (get idx from name)
						<name>
							<idx>
					networks:			# Keep a list of network service names connected to this namespace,
						- <idx>			# organized according to the interface giving access.
							<netname>
					service_name:		# The service name of the service associated to this namespace. It might
						<name>			# be external (e.g., in case of Kubernetes pods).
					service:				# The service instance associated to this namespace (if locally created).
						<name>			# It could be retrieved by ``get_services()``, but this link is faster.
					router:				
						service_name:  # Service name associated to this router
							<name>
						ifaces:			# It contains the interface indexes of the interfaces being routed
							- <idx>
					bridge:				# List of bridges and network interfaces
						<name>			# The internal name of the bridge and the interface bound to it
							service_name: # The service name associated to the bridge
								<name>
							net:			# A bridge will be part of a network (subservice)
								<netname>
							ifaces:
								- <idx>

		"""
		try:
			logger.debug("Starting discover_context")
			# Retrieve the association between pods and namespaces from scratch
			self.kube_pods=None
			# We discover again the platform at each run because packages might have changed
			logger.debug("Calling _discover_platform")
			self._discover_platform()
			logger.debug("Calling _discover_network_namespaces")
			self._discover_network_namespaces()
			logger.debug("Calling _discover_networks")
			self._discover_networks()
			logger.debug("Calling _discover_network_functions")
			self._discover_network_functions()
			logger.debug("Calling _discover_links_networks")
			self._discover_links_networks()
			logger.debug("Calling _discover_links_net_functions")
			self._discover_links_net_functions()
			logger.debug("discover_context completed successfully")
		except Exception as e:
			logger.error("Error in discover_context: %s", e, exc_info=True)
			raise

	def _discover_platform(self):
		logger.debug("Starting platform discovery")
		name = platform.node()
    
		pkgs = subprocess.run(DPKG_LIST, capture_output=True)
		
		pkg_list=ArrayOf(Package)()
		for line_num, line in enumerate(pkgs.stdout.splitlines(), 1):
			try:
				# dpkg --list uses space-separated columns, not tabs
				r = line.split()  # Split on any whitespace
				if len(r) < 5:
					logger.debug("Line %d has insufficient fields (%d): %s", line_num, len(r), line[:100])
					continue
				if r[0].decode() == 'ii': # only report installed packages
					# r[0] = status (ii)
					# r[1] = package name
					# r[2] = version
					# r[3] = architecture
					# r[4:] = description (may contain spaces)
					pkg_list.append( Package(
						name=r[1].decode('utf-8', errors='replace'), 
						version=r[2].decode('utf-8', errors='replace'), 
						description=b' '.join(r[4:]).decode('utf-8', errors='replace')
					))
			except Exception as e:
				logger.error("Error processing dpkg line %d: %s. Line: %s", line_num, e, line[:100], exc_info=True)

		# TODO: Add more platform specific info for Mac, Windows, Linux, Android
		execenv = OS(name=name, description=platform.platform(), 
				family=platform.system(), version=platform.version(), release=platform.release, 
				arch=platform.machine(), pkgs=pkg_list)
		self.platform = Service(name=Name(Hostname(name)), 
					type=ServiceType(execenv), subservices=ArrayOf(Name)(),
					release=None, owner="root")
		self.services.append( self.platform )
	
		# TODO: Add a Host service for the hardware

	def _get_namespace_service(self, netns):
		""" Get Service name associated to a namespace

			Try to infer the external service that is using the provided namespace.
			If such Service is not found, create a Service of generic type NetworkFunction
			for the namespace (based on the fact that this is a network namespace).

			:param netns: The name of the network namespace
			:return: The namespace service name and the service itself (None if not instantiated
					in this scope.
		"""
		if netns is None:
			return self.platform.name, self.platform

		kube_service_name = self._get_namespace_service_kubernetes(netns)
		if kube_service_name is not None:
			return kube_service_name, None

		os_service_name = self._get_namespace_service_openstack(netns)
		if os_service_name is not None:
			return os_service_name, None

		netfun = self._get_namespace_function(netns)
		# If I couldn't find any service or network function associated to this namespace,
		# just keep it as a generic ExecutionEnvironment
		if netfun is None:
			netfun = self._get_namespace_execenv(netns)

		net_service = Service(name=Name("netns:"+netns),
				type=ServiceType(netfun), subservices=ArrayOf(Name)(),
				owner=str(self.platform.name), release=None)
		self.services.append(net_service)
		self.platform.subservices.append(net_service)

		return net_service.name, net_service

	def _get_namespace_execenv(self, netns):
		""" Get the ExecutionEnvironment associated to a network namespace """
		# TODO: Scan pid/filesystems to discover what application/packages are using this namespace
		inode = None
		with pyroute2.IPRoute() as iprns:
			for ns in iprns.get_netns_info():
				try:
					nsinfo_path_attrs = ns.get_attrs('NSINFO_PATH')
					if nsinfo_path_attrs and nsinfo_path_attrs[0].split('/')[-1] == netns:
						inode = ns.get('inode')
						break
				except Exception as e:
					logger.debug("Could not process netns info: %s", e)
		return ExecutionEnvironment(name=netns, id=inode, description="Linux network namespace")

	def _get_namespace_service_kubernetes(self, netns_name):
		""" Infer the kubernetes service name based on container name

			This implementation uses the ctr command to extract data from 
			local kubelet, if installed.

			Indeed, there is also a Python containerd package which implements the 
			GRPC API, but the code is outdates and there is no clear documentation
			apart from the simple example (which does not work with latest grpc package).
		"""
		if self.kube_pods is None:
			self.kube_pods = {}

			# Create a map between inodes and netns names
			with pyroute2.IPRoute() as iprns:
				nsmap={}
				for netns in iprns.get_netns_info():
					try:
						nsinfo_path_attrs = netns.get_attrs('NSINFO_PATH')
						if nsinfo_path_attrs:
							nsmap[netns['inode']] = nsinfo_path_attrs[0].split('/')[-1]
					except Exception as e:
						logger.debug("Could not process netns info: %s", e)
	
			with grpc.insecure_channel('unix:///run/containerd/containerd.sock') as channel:
				containersv1 = containers_pb2_grpc.ContainersStub(channel)
				containers = containersv1.List(
					containers_pb2.ListContainersRequest(),
					metadata=(('containerd-namespace', 'k8s.io'),)).containers

				for container in containers:
					try:
						# Check if labels is dict or list
						if not isinstance(container.labels, dict):
							logger.error("container.labels is not a dict, it's a %s: %s", type(container.labels), container.labels)
							continue
							
						if self.kube_namespaces is None or container.labels.get('io.kubernetes.pod.namespace') in self.kube_namespaces:
							pod_name=container.labels.get('io.kubernetes.pod.name', '')+'.pod.'+container.labels.get('io.kubernetes.pod.namespace', '')+self.kube_suffix
							try:
								jsondata=json.loads(container.spec.value)
								
								# Type checking
								if not isinstance(jsondata, dict):
									logger.error("jsondata is not a dict, it's a %s", type(jsondata))
									continue
								if 'linux' not in jsondata or not isinstance(jsondata.get('linux'), dict):
									logger.debug("jsondata['linux'] missing or not a dict")
									continue
								if 'namespaces' not in jsondata['linux']:
									logger.debug("jsondata['linux']['namespaces'] missing")
									continue
									
								linux_namespaces=jsondata['linux']['namespaces']
								
								if not isinstance(linux_namespaces, list):
									logger.error("linux_namespaces is not a list, it's a %s: %s", type(linux_namespaces), linux_namespaces)
									continue
									
								for ns in linux_namespaces:
									if not isinstance(ns, dict):
										logger.error("namespace entry is not a dict, it's a %s: %s", type(ns), ns)
										continue
									if ns.get('type') == 'network':
										try:
											inode=os.stat(ns['path']).st_ino
											self.kube_pods[nsmap[inode]]=pod_name
										except Exception as e:
											logger.debug("Could not stat namespace path %s: %s", ns.get('path', 'unknown'), e)
							except json.JSONDecodeError as e:
								logger.error("Error decoding JSON for container %s: %s", container.id[:12], e)
							except Exception as e:
								logger.error("Error processing container %s: %s", container.id[:12], e, exc_info=True)
					except Exception as e:
						logger.error("Error processing container: %s", e, exc_info=True)
	def _get_kube_suffix(self, kube_config_file):
		""" Automatically retrieve the cluster domain name from kubelet configuration """
		try:
			with open(kube_config_file,'r') as config:
				yamlconfig = yaml.safe_load(config)
				suffix="."+yamlconfig['clusterDomain']
		except Exception as e:
			logger.warn("Unable to get cluster domain name from kubelet configuration file: %s", e)
			suffix=""

		return suffix


	def _get_namespace_service_openstack(self, netns):
		""" Infer the OpenStack network function name based on container name """
		pass

	def _get_namespace_function(self, netns):
		""" Model the container as a network function """
		with pyroute2.IPRoute(netns=netns) as iprns:
			for link in iprns.get_links(): 
				# Check if this namespace routes packets
				try:
					routes = []
					if link.get_attr('IFLA_AF_SPEC').get_attr('AF_INET')['forwarding'] == 1 or \
							link.get_attr('IFLA_AF_SPEC').get_attr('AF_INET6').get_attr('IFLA_INET6_CONF')['forwarding'] == 1:
						routes = self._get_namespace_routes(iprns)
					if len(routes) > 0:
						return NetworkFunction(name="router:"+netns, description="Linux router", type=NetworkFunctionType(Router(routes=json.dumps(routes))))
					# TODO: Check if the namespace performs other kind of network functions (NAT, DHCP?)
				except:
					return None

	def _get_namespace_routes(self, iprns):
		""" Get network routes for namespace/execution environment

			@:param iprns: IPRoute2 handler for the namespace.
			@:return: A list of routes
		"""
		routes = []
		for route in iprns.get_routes():
			routes.append({'dst': route.get_attr('RTA_DST') if route.get_attr('RTA_DST') is not None else 'default',
					'via': route.get_attr('RTA_GATEWAY') if route.get_attr('RTA_GATEWAY') is not None else 'local',
					'iface': route.get_attr('RTA_OIF')})

		return routes

	def _get_namespace_ifaces(self, netns):
		""" Get a dictionary of interface idx and names

			@:param netns: name of the network namespace (None for main network stack
			@:return: A map between interface index and names 
		"""
		ifaces = {}
		with pyroute2.IPRoute(netns=netns) as ipr:
			for iface in ipr.get_links():
				ifaces[iface['index']]=iface.get_attr('IFLA_IFNAME')
		return ifaces
		
	def _get_namespace_ifaces_no(self, netns):
		""" Get a dictionary of interface names and idx

			@:param netns: name of the network namespace (None for main network stack
			@:return: A map between interface names and indexes 
		"""
		ifaces = {}
		with pyroute2.IPRoute(netns=netns) as ipr:
			for iface in ipr.get_links():
				ifaces[iface.get_attr('IFLA_IFNAME')]=iface['index']
		return ifaces


	def _discover_network_namespaces(self):
		""" Discover the network namespaces and their properties
			
			This function:
				1) discovers all namespaces 
				2) retrieves their service names (and create the services if necessary)
				3) discover all network interfaces in namespaces (idx, name)
				4) discover peer namespaces (idx, name)
			A special namepsace is given by the main ExecutionEnvironment, which is the "None" namespace.

		"""
		self._namespaces = {}
		for ns in pyroute2.netns.listnetns()+[None]: # Last element is to discover the main network stack
			self._namespaces[ns] = {'name': ns, 'netnsmap': {}, 'ifaces': {}, 'ifaces_idx': {}, 
				'service_name': None, 'service': None, 'networks': [], 'router': {} , 'bridges': {} }
			if ns is None:
				self._namespaces[ns]['name']=str(self.platform.name)

			ports = {}
			self._namespaces[ns]['service_name'], self._namespaces[ns]['service'] = self._get_namespace_service(ns)	
			with pyroute2.IPRoute(netns=ns) as iprns:
				# Retrieve the description of the interface
				if ns is None:
					description = "Default network stack"
				else:
					description = "Linux namespace"

				# Keep a map of namespace names and ids
				# Note: a numeric id is assigned to namespaces with a local scope only inside each namespace
				# Note2: a numeric id is only assigned to peer namespace (e.g., with veth links)
				# Note3: inside namespaces, the id 0 is always used for the main network stack (???) ; 
				# 			in the main network stack, id 0 is used for a namespace
				# The only "global" valid identifier is the namespace name
				for netns in iprns.get_netns_info():
					try:
						nsinfo_path_attrs = netns.get_attrs('NSINFO_PATH')
						if nsinfo_path_attrs:
							self._namespaces[ns]['netnsmap'][netns['netnsid']] = nsinfo_path_attrs[0].split('/')[-1]
					except Exception as e:
						logger.debug("Could not process netns info for namespace %s: %s", ns, e)
				if ns is not None:
					self._namespaces[ns]['netnsmap'][0]=None # Main network stack does not have a name, and it is referred to as '0' 

				# Create the NetworkNode object associated to this namespace
				netnode = NetworkNode(name="Ports", description=description, id=None, # Kubernetes id,
					ifaces=ArrayOf(NetworkInterface)())

				# Retrieve the default gateway for this container
				gws={}
				for route in iprns.get_routes():
					# Routes including gateways have the RTA_GATEWAY attribute; other routes are local only
					# Currently, we only look for the default gateway (netmask 0.0.0.0 or prefixlen=0) and assume
					# there is at most one default gateway, because the data model only expects 1 gw
					# However, we create a list to account for at least v4/v6 gateways
					if route.get_attrs('RTA_GATEWAY') != [] and route['dst_len'] == 0: 
						if route.get_attr('RTA_OIF') not in gws:
							gws[route.get_attr('RTA_OIF')] = []
						gws[route.get_attr('RTA_OIF')].append(route.get_attr('RTA_GATEWAY'))
				
				# Loop for all network interfaces in the container
				for link in iprns.get_links(): 
					idx = link['index'] 
					name = link.get_attr('IFLA_IFNAME') # The addr items do not hold iface name for interfaces without IPv4 addresses
					mac = link.get_attr('IFLA_ADDRESS')
					
					self._namespaces[ns]['ifaces'][idx]=name
					self._namespaces[ns]['ifaces_idx'][name]=idx
					port = NetworkInterface(id=link['index'], iface=name, mac=mac, ips = ArrayOf(IPInfo)())

					# Retrieve IP addresses associated to this interface and add to the port
					for addr in iprns.get_addr(index=idx):
						# Find correct gw for this interface. We currently assume at most 1 gw per IP family
						gw=None
						if idx in gws:
							for g in gws[idx]:
								if ipaddress.ip_network(addr.get_attr('IFA_ADDRESS')).version == ipaddress.ip_address(g).version:
									gw=g
						port.ips.append( IPInfo(ip=IPAddress(addr.get_attr('IFA_ADDRESS')), prefix=addr['prefixlen'], gw=gw) )

					netnode.ifaces.append( port )

				port_service = Service(namespace=ns, name=Name(self._namespaces[ns]['name']+".ports"),
						type=ServiceType(netnode), subservices=None, owner=str(self._namespaces[ns]['service_name']))
				self.services.append(port_service)
				if self._namespaces[ns]['service'] is not None:
					self._namespaces[ns]['service'].subservices.append(port_service)

	def _add_net_service(self, name:Name = None, namespace:str = None, id:str=None, description:str = "Network", ipnetaddrs:ArrayOf(IPNetAddress)=ArrayOf(IPNetAddress)(), nettype:object= IPNetwork):
		""" Add a network service
		"""
		net_name=str(ipnetaddrs[0]) if len(ipnetaddrs) > 0 else None
		ipnet = Network(name=net_name, id=id, description=description,
				type=NetworkType( nettype({'nets': ipnetaddrs } )))
		net_service= Service(name=name, namespace=namespace, type=ServiceType(ipnet), subservices=ArrayOf(Name)(), owner=str(self.platform.name))
		self.services.append(net_service)
		self.platform.subservices.append(net_service)
		
		return net_service

	def _discover_networks(self):
		""" Discover internal and external networks

			This includes meta-networks like veth links.
		"""
		veths = []
		tuns = {}
		tuns_servers = {}
		for ns in self._namespaces.keys():
			with pyroute2.IPRoute(netns=ns) as iprns:
				for link in iprns.get_links(): 
					link_idx=link['index']
					link_name=link.get_attr('IFLA_IFNAME') 

					ipnetaddrs = ArrayOf(IPNetAddress)()
					peer1=(link_idx, self._namespaces[ns]['name'])
					for addr in self._get_net_addrs(netns=self._namespaces[ns]['name'], if_idx=peer1[0]):
						ipnetaddrs.append(addr)

					for attr in link.get_attrs('IFLA_LINKINFO'):
						link_type=attr.get_attrs('IFLA_INFO_KIND')[0]

						match link_type:
							case 'veth':
								netnsid2=link.get_attrs('IFLA_LINK_NETNSID')
								if len(netnsid2) > 0:
									ns2=self._namespaces[ns]['netnsmap'][netnsid2[0]]
								else: # Same namespace
									ns2=ns
								peer2=(link.get_attrs('IFLA_LINK')[0], self._namespaces[ns2]['name'])
								net_id="veth:if"+str(peer1[0])+'.'+str(peer1[1])+"@"+"if"+str(peer2[0])+"."+str(peer2[1])
								if [(peer1, peer2)] not in veths and [(peer2, peer1)] not in veths:
									veths.append( [(peer1, peer2)] )
									peer1_service_name = self._namespaces[ns]['service_name']
									peer2_service_name = self._namespaces[ns2]['service_name']
									description="Veth link between " + str(peer1_service_name) + " and " + str(peer2_service_name)
									# Default: try with peer1
									net_name = self._create_net_name(netns=self._namespaces[ns]['name'], if_idx=peer1[0])
									if net_name is None: # If peer1 has not got a valid ip address, try with ip2 (may be None as well)
										net_name = self._create_net_name(netns=self._namespaces[ns2]['name'], if_idx=peer2[0])
								
									for addr in self._get_net_addrs(netns=self._namespaces[ns2]['name'], if_idx=peer2[0]):
										ipnetaddrs.append(addr)
									network = Network(name=net_name, id=net_id, description=description, type=NetworkType(VEthNetwork({'peers': (peer1, peer2), 'nets': ipnetaddrs})))
								
									# Create services for the virtual network (even if it is only a link)
									net_service = Service(name=Name(net_id), type=ServiceType(network), 
										subservices=None, owner=str(self.platform.name), release=None)
									self.platform.subservices.append(net_service.name)
									self.services.append(net_service)

									# Save network service name in the connected namespaces (used later to create links)
									self._namespaces[ns]['networks'].append({peer1[0]: net_service.name})
									self._namespaces[ns2]['networks'].append({peer2[0]: net_service.name})

#									# Create links between containers and the network
#									peer = Peer(service_name=net_service.name, role=PeerRole.forwarding, consumer=None)
#									self.links.append( Link(name=ns_service_name, description="Connection to veth link",
#												link_type=LinkType.packet_flow,
#												role=PeerRole.endpoint, peers=ArrayOf(Peer)([peer])))
#									self.links.append( Link(name=ns2_service_name, description="Connection to veth link",
#												link_type=LinkType.packet_flow,
#												role=PeerRole.endpoint, peers=ArrayOf(Peer)([peer])))
#								else:
#									try:
#										peer = self.get_services(Name(net_id))[0] # There must be such service!
#									except:
#										peer = self.get_services(Name(peer2+" <-> "+peer1))[0]
#
							case 'macvlan':
								if attr.get_attrs('IFLA_INFO_DATA')[0].get_attrs('IFLA_MACVLAN_MODE')[0] == 'bridge':
									ns2=self._namespaces[ns]['netnsmap'][link.get_attrs('IFLA_LINK_NETNSID')[0]]
#									net_id=self._get_namespace_ifaces(ns2)[link.get_attrs('IFLA_LINK')[0]]+"@"+str(ns2)
									net_id="ipnet:"+self._namespaces[ns2]['ifaces'][link.get_attrs('IFLA_LINK')[0]]+"@"+self._namespaces[ns2]['name']
									try:
										net_service=self.get_services(name=Name(net_id), filter=Network)[0]
										for ip in ipnetaddrs:
											net_service.type.getObj().type.getObj()['nets'].append(ip)
									except:
										net_service=self._add_net_service(name=Name(net_id), ipnetaddrs=ipnetaddrs, id=net_id) 

									self._namespaces[ns]['networks'].append({peer1[0]: net_service.name})

								else:
									logger.warn("Unsupported macvlan mode: %s", attr.get_attrs('IFLA_INFO_DATA')[0].get_attrs('IFLA_MACVLAN_MODE')[0] )

		
							case 'tun':
								# The ned_id will be iface.client@iface.server. We create a partial name here, and will update it later on
								net_id=self._namespaces[ns]['ifaces'][link_idx]+"."+self._namespaces[ns]['name']
								net_service=None
								if len(ipnetaddrs) > 0:
									netaddr = ipnetaddrs[0]
									# There should be only 1 IP address assigned to a tunnel interface...
									ip = ipaddress.ip_network(netaddr.getObj())
									old_net_name=None
									for i, s in tuns.items():
										if ip.subnet_of(ipaddress.ip_network(i)): # The new element is a client of an existing element
											tuns_server[i]=copy.deepcopy(s)
											net_service=s
											net_service.name=Name("tun:"+net_id+"@"+net_service.name.getObj())
											net_service.type.getObj().name=str(ipnetaddrs[0])
											net_service.type.getObj().type.getObj()['nets']=ipnetaddrs
											# Is it possible to be client of multiple servers???
										elif ip.supernet_of(ipaddress.ip_network(i)): # The new element is a server of the current element
											net_service=s
											old_net_name=net_service.name
											net_service.name=Name("tun:"+net_service.name.getObj()+"@"+net_id)
											net_service.type.getObj().id=net_id
											net_service.type.getObj().type.getObj()['server']=net_id
											tuns_servers[str(ip)]=copy.deepcopy(s)
											tuns_servers[str(ip)].name=Name(net_id)
											# Do not break the loop, because it might be the server of many clients
								if net_service is None:
									# Create a network service, we will change its name later on when we discover its client/server
									net_service=self._add_net_service(name=Name(net_id), description="Tunnel network", ipnetaddrs=ipnetaddrs,  id=net_id, nettype=TunnelNetwork) 
									tuns[str(ip)]=net_service
									for i, s in tuns_servers.items():
										if ip.subnet_of(ipaddress.ip_network(i)): # Another client of a previously-seen server
											net_service.name=Name("tun:"+net_id+"@"+s.name.getObj())
											net_service.type.getObj().id=s.type.getObj().id
											net_service.type.getObj().type.getObj()['server']=s.type.getObj().id
								else:
									self._namespaces[ns]['networks'].append({peer1[0]: net_service.name})

							case 'bridge':
								net_id="brnet:"+self._namespaces[ns]['ifaces'][link_idx]+"."+self._namespaces[ns]['name']
								net_service=self._add_net_service(name=Name(net_id), description="Bridged network", ipnetaddrs=ipnetaddrs,  id=net_id, nettype=EthernetNetwork) 
								# This is a virtual ethernet network with one bridge as subservice with the same name of the interface
								if link_name not in self._namespaces[ns]['bridges']:
									self._namespaces[ns]['bridges'][link_name] = {}
								self._namespaces[ns]['bridges'][link_name]['net']=net_service.name
								# Do not add the bridge interface to the list of its interfaces, otherwise this will create a recursive link between the bridge network and the bridge
#								self._namespaces[ns]['bridges'][link_name]['ifaces']=[link_idx]
								self._namespaces[ns]['bridges'][link_name]['ifaces']=[]
								self._namespaces[ns]['networks'].append({peer1[0]: net_service.name})
								

							case _:
								logger.warn("Unable to manage interface %s of type: %s", link_name, link_type)


					if len(link.get_attrs('IFLA_LINKINFO')) == 0 and link_name != "lo":
						# These interfaces provide direct access to an IP network
						net_id="ipnet:"+link_name+"."+self._namespaces[ns]['name']
						try:
							net_service=self.get_services(name=Name(net_id), filter=Network)[0] # There might already be the network, if other interfaces created it (e.g., macvlan)
							if net_service.type.getObj().name is None:
								net_service.type.getObj().name=str(ipnetaddrs[0]) # We use the first IP address as network identifier
						except:
							net_service=self._add_net_service(name=Name(net_id), ipnetaddrs=ipnetaddrs, id=net_id) 
						self._namespaces[ns]['networks'].append({peer1[0]: net_service.name})

#						peer = Peer(service_name=net_service.name, role=PeerRole.forwarding, consumer=None)

						for ip in ipnetaddrs:
							net_service.type.getObj().type.getObj()['nets'].append(ip)



	def _create_net_name(self, netns, if_idx):
		""" Create a network name based on IP network address of the interface """
		netnodes = self.get_services(name=Name(netns+".ports"), filter=NetworkNode)
		for netnode in netnodes:
			for iface in netnode.type.getObj().ifaces:
				if iface.id == str(if_idx):
					for ip in iface.ips:
						if not ipaddress.ip_address(str(ip.ip)).is_link_local:
							ipnetaddr = ipaddress.ip_network(str(ip.ip)+"/"+str(ip.prefix), strict=False)
							return str(ipnetaddr)
		return None

	def _get_net_addrs(self, netns, if_idx):
		""" Retrieve the list of network addresses associated to an interface """
		ipnetaddrs = []
		netnodes = self.get_services(name=Name(netns+".ports"), filter=NetworkNode)
		for netnode in netnodes:
			for iface in netnode.type.getObj().ifaces:
				if iface.id == str(if_idx):
					for ip in iface.ips:
						ipnetaddr = ipaddress.ip_network(str(ip.ip)+"/"+str(ip.prefix), strict=False)
						ipnetaddrs.append(ipnetaddr)

		return ipnetaddrs

	


	def _discover_network_functions(self):
		""" Discover network functions

			This includes routers and bridges implemented by the Linux kernel
			and external software (e.g., openvswitch).
		"""
		for ns in pyroute2.netns.listnetns()+[None]: # Last element is to discover the main network stack
			self._discover_routers(ns)
			self._discover_bridges(ns)

									
	def _discover_routers(self, ns):
		""" Discover routers
			
			@:param ns: Network namespace name
		"""
		ns_service_name=self._namespaces[ns]['service_name']
		with pyroute2.IPRoute(netns=ns) as iprns:
			# Discover router
			router=None
			# Loop for all network interfaces in the container
			for link in iprns.get_links(): 
				idx = link['index'] 
				# Add a router, if not done yet
				routes = []
				if (link.get_attr('IFLA_AF_SPEC').get_attr('AF_INET')['forwarding'] == 1 or \
						link.get_attr('IFLA_AF_SPEC').get_attr('AF_INET6').get_attr('IFLA_INET6_CONF')['forwarding'] == 1): 
					if router is None:
						self._namespaces[ns]['router']['ifaces'] = []
						netfun = NetworkFunction(name="Router", id=ns,
								description="Linux software router@"+str(ns_service_name),
								type=NetworkFunctionType( Router(routes=json.dumps(routes) ) ))
						router=Service(namespace=ns, name=Name("router:"+str(ns_service_name)),
								type=ServiceType( netfun ), owner=str(ns_service_name))
						self.services.append(router)
						self.platform.subservices.append(router)
						peer=Peer(service_name=ns_service_name, role=PeerRole.host, consumer=None)
						self.links.append( Link(name=router.name, description="Router hosted in "+self._namespaces[ns]['name'],
									link_type=LinkType.hosting, role=PeerRole.guest, peers=ArrayOf(Peer)([peer])))
					self._namespaces[ns]['router']['service_name']=router.name
					self._namespaces[ns]['router']['ifaces'].append(idx)


	def _discover_bridges(self, ns):
		""" Discover bridges 
			
			@:param ns: Network namespace name
		"""

		ns_service_name=self._namespaces[ns]['service_name']
		if ns is None:
			cmd=['brctl',  'show']
		else:
			cmd=['ip', 'netns',  'exec', ns, 'brctl',  'show']
		brctl = subprocess.run(cmd, capture_output=True)
		wlist = map(str.split, brctl.stdout.decode().splitlines()[1:])
		brwlist = filter(lambda x: len(x) != 1, wlist)
		brlist = map(lambda x: x[0], brwlist)
		for br in brlist:
			cmdbr = cmd + [br]
			brctl = subprocess.run(cmdbr, capture_output=True)
			brid = brctl.stdout.decode().split()[1]
			ifaces = brctl.stdout.decode().split()[10:]
			netfun=NetworkFunction(name=br, id=brid, description="Linux bridge", type=NetworkFunctionType( Bridge({'ifaces': ArrayOf(NetworkInterface)()}) ))
			if 'ifaces' not in self._namespaces[ns]['bridges'][br]: # An interface should be already present, but just to be sure
				self._namespaces[ns]['bridges'][br]['ifaces'] = []
			for iface in ifaces:
				# A bridged interface is no more available to the namespace; it is replaced by the bridge interface
				# If there are other interfaces connected to the network of a bridged interface (veth), they must be now connected to the bridge network
				self._namespaces[ns]['bridges'][br]['ifaces'].append(self._namespaces[ns]['ifaces_idx'][iface])
				cur_idx=None
				for net in self._namespaces[ns]['networks']:
					for k,v in net.items():
						if k==self._namespaces[ns]['ifaces_idx'][iface]:
							cur_idx=self._namespaces[ns]['networks'].index(net)
					if cur_idx is not None:
						break
				cur=self._namespaces[ns]['networks'].pop(cur_idx)
				for k, v in cur.items():
					cur_iface_net=v
				# Look for the removed network in the current and other namespaces
				for ns2 in self._namespaces:
					for net in self._namespaces[ns2]['networks']:
						for k,v in net.items():
							if v==cur_iface_net:
								net[k]=self._namespaces[ns]['bridges'][br]['net'] 
				port = NetworkInterface(id=self._namespaces[ns]['ifaces_idx'][iface], iface=iface, mac=None, ips = None)
				netfun.type.getObj()['ifaces'].append(port)

			net_service = Service(namespace=ns, name=Name("bridge:"+br+"."+str(ns_service_name)), type=ServiceType(netfun), owner=str(self.platform.name))
			self.services.append(net_service)
			self.platform.subservices.append(net_service.name)
			self._namespaces[ns]['bridges'][br]['service_name']=net_service.name
			

			# Add this bridge as a subservice of its main network
			br_net_service = self.get_services(name=self._namespaces[ns]['bridges'][br]['net'], filter=Network)
			assert len(br_net_service) == 1
			br_net_service[0].subservices.append(net_service.name)
			
			peer=Peer(service_name=ns_service_name, role=PeerRole.host, consumer=None)
			self.links.append( Link(name=net_service.name, description="Bridge hosted in "+self._namespaces[ns]['name'],
						link_type=LinkType.hosting, role=PeerRole.guest, peers=ArrayOf(Peer)([peer])))



	def _discover_links_networks(self):
		""" Discover links between networks and network namespaces """
		for ns in self._namespaces:
			print("namespace: ", ns)
			print("nets: ", self._namespaces[ns]['networks'])
			for net in self._namespaces[ns]['networks']:
				for idx, net_service in net.items():
					peer = Peer(service_name=Name(net_service), role=PeerRole.forwarding, consumer=None)
					self.links.append( Link(name=self._namespaces[ns]['service_name'], description="Connection to network",
									link_type=LinkType.packet_flow,
									role=PeerRole.endpoint, peers=ArrayOf(Peer)([peer])))

	def _discover_links_net_functions(self):
		""" Discover links between networks and network functions """
		for ns in self._namespaces:
			self._discover_links_routers(ns)
			self._discover_links_bridges(ns)

	def _discover_links_routers(self, ns):
		""" Discover links between routers and networks
			
			@:param ns: Network namespace name
		"""
		if 'service_name' in self._namespaces[ns]['router']:
			peer = Peer(service_name=(self._namespaces[ns]['router']['service_name']), role=PeerRole.forwarding, consumer=None)
			# TODO: Use maps and lambda functions to optimise the code
			for iface_idx in self._namespaces[ns]['router']['ifaces']:
				for net in self._namespaces[ns]['networks']:
					for idx, net_service in net.items():
						if iface_idx == idx:
							self.links.append( Link(name=net_service, description="Connection to router",
										link_type=LinkType.packet_flow,
										role=PeerRole.endpoint, peers=ArrayOf(Peer)([peer])))
						
	def _discover_links_bridges(self, ns):
		""" Discover links between bridges and networks
			 (A bridge is also a subservice of a network)
			
			@:param ns: Network namespace name
		"""
		for br in self._namespaces[ns]['bridges']:
			peer = Peer(service_name=self._namespaces[ns]['bridges'][br]['service_name'], role=PeerRole.forwarding, consumer=None)
			for iface_idx in self._namespaces[ns]['bridges'][br]['ifaces']:
				for net in self._namespaces[ns]['networks']:
					for idx, net_service in net.items():
						if iface_idx == idx:
							self.links.append( Link(name=net_service, description="Connection to bridge",
										link_type=LinkType.packet_flow,
										role=PeerRole.endpoint, peers=ArrayOf(Peer)([peer])))
			




	def _get_service_role(self, service_name):
		""" Get the network role of a service

			This is based on the function it implements (e.g., Router)
		"""
		service_role = PeerRole.endpoint # default value is service is not described locally
		services = self.get_services(name=service_name)
		for service in services: # There should be only 1 item!
			if service.type.getObj() == Router:
				service_role=PeerRole.fowarding
			else:
				service_role=PeerRole.endpoint
	
		return service_role
						
