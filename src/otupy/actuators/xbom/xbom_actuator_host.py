""" Host xbom Actuator
	
    The Host actuaotr is intended to discover the host hardware and its 
    operating system. Despite of the name, this actuator is concieved to 
	 describe the execution environment 
    itself, because there is no other way to query the OS's APIs.

    The current implementation is for demonstration purposes only and makes
    intensive usage of shell commands. Future releases should improve
    by using better Python libraries for the same purpose. 

    We currently do not discover harware components. This is left for future
    work, since we do not cover hardware vulnerabilities in MIRANDA.

	The actuator-specific configuration includes:

		- ``kubernetes``: Kubernetes-related configuration to link local
			components with kubernetes resources. Specific fields are:

			- ``use_suffix``: Use kubernetes suffix when reporting names.
			- ``kubelet_config``: Config file uselet by the kubelet daemon.
			- ``namespaces``: List of namespaces to be reported
			
			
		- ``host``: The service identifier (`sid`) of the ``Host`` that host
			this execution environment. It can be specified in the compact form
			as string(`sid: type:subtype/domain/namespace/name@version`) or 
			by its parameters (type, subtype, name, domain, namespace, version).
			Examples:
				host:
					sid: "host:vm/Default/tenant1/vm0@None"
				host:
					type: host
					subtype: vm
					...
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
import ovs.db.idl
import ovs.dirs

from containerd.services.containers.v1 import containers_pb2_grpc, containers_pb2

from otupy import Array, ArrayOf, actuator_implementation, Hostname, MACAddr

from otupy.actuators.xbom.base_xbom_actuator import XBOMActuator
from otupy.models.ctxd import *



logger = logging.getLogger(__name__)

KUBELET_CONFIG_FILE='/var/lib/kubelet/config.yaml'
DEFAULT_OVS_HOST='127.0.0.1'
DEFAULT_OVS_PORT=6640

@actuator_implementation("xbom-host")
class XBOMHostActuator(XBOMActuator):
	""" Host Actuator Manager

		Extend the base `XBOMActuator` to retrieve the description of the Operating System
        environment. This includes the connections between its (network) namespaces


	"""

	def __init__(self, **kwargs):
		""" Initialize the actuator

		"""
		super().__init__(**kwargs)
		self.platform = None # Keep an internal reference to the ExecutionEnvironment of this host

		self.kube_namespaces = kwargs['kubernetes']['namespaces'] if 'kubernetes' in kwargs and 'namespaces' in kwargs['kubernetes'] else None
		kube_use_suffix = kwargs['kubernetes']['use_suffix'] if 'kubernetes' in kwargs and 'use_suffix' in kwargs['kubernetes'] else True # This is the safe option to link to external service names
		kube_kubelet_config = kwargs['kubernetes']['kubelet_config'] if 'kubernetes' in kwargs and 'kubelet_config' in kwargs['kubernetes'] else KUBELET_CONFIG_FILE
		if kube_use_suffix is True:
			self.kube_suffix = kwargs['kubernetes']['suffix'] if 'kubernetes' in kwargs and 'suffix' in kwargs['kubernetes'] else self._get_kube_suffix(kube_kubelet_config)
		else:
			self.kube_suffix = ""
		self.ovs_host = kwargs['ovs']['host'] if 'ovs' in kwargs and 'host' in kwargs['ovs'] else DEFAULT_OVS_HOST
		self.ovs_port = kwargs['ovs']['port'] if 'ovs' in kwargs and 'port' in kwargs['ovs'] else DEFAULT_OVS_PORT
		self.ovs_discover = kwargs['ovs']['discover'] if 'ovs' in kwargs and 'discover' in kwargs['ovs'] else False
		self.host = kwargs.get('host')
		self.brctl_exe = kwargs.get('brctl_exe', '/sbin/brctl')
		self.dpkg_exe = kwargs.get('dpkg_exe', '/usr/bin/dpkg')

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
					networks:			# Keep a list of network service sids connected to this namespace,
						- <idx>			# organized according to the interface giving access.
							<netsid>
					service_name:		# The service name of the service associated to this namespace. It might
						<name>			# be external (e.g., in case of Kubernetes pods).
					service_sid			# The service sid associated to this namespace.
						<sid>
					service:				# The service instance associated to this namespace (if locally created).
						<name>			# It could be retrieved by ``get_services()``, but this link is faster.
					router:				
						service_name:  # Service name associated to this router
							<name>
						ifaces:			# It contains the interface indexes of the interfaces being routed
							- <idx>
					bridges:				# List of bridges and network interfaces
						<name>			# The internal name of the bridge and the interface bound to it
							service_name: # The service name associated to the bridge
								<name>
							net:			# A bridge will be part of a network (subservice)
								<netname>
							ifaces:
								- <idx>
					ovs:					# List of OpenVSwitches and network interfaces
						...				# Same as bridges

			An additional structure is kept to store network dependencies (e.g., virtual networks
			hosted on other physical networks).

			self._net_deps:
				<idx, ns>:				# Interfaces index and namespace of the hosting network
					- <netsid>			# Network service sid
											# (assuming the corresponding service might have not been created yet)
		"""

		# Retrieve the association between pods and namespaces from scratch
		self.kube_pods=None
		self.domain=None
		self._net_deps={}
		# We discover again the platform at each run because packages might have changed
		logger.debug("Discovering services...")
		logger.debug("Discovering platform...")
		self._discover_platform()
		logger.debug("Discovering namespaces...")
		self._discover_network_namespaces()
		logger.debug("Discovering networks...")
		self._discover_networks()
		logger.debug("Discovering network functions...")
		self._discover_network_functions()
		logger.debug("Discovering links...")
		logger.debug("Discovering host links...")
		self._discover_link_host()
		logger.debug("Discovering network links...")
		self._discover_links_networks()
		logger.debug("Discovering network function links...")
		self._discover_links_net_functions()

	def _discover_platform(self):
		name = platform.node()
		self.domain = name
    
		pkgs = subprocess.run([self.dpkg_exe, '--list'], capture_output=True)
		
		pkg_list=ArrayOf(Package)()
		for line in pkgs.stdout.splitlines():
			r = line.split(b'\t')
			if r[0].decode() == 'ii': # only report installed packages
				pkg_list.append( Package(name=r[1], version=r[2], arch=r[3], description=r[4]) )

		# TODO: Add more platform specific info for Mac, Windows, Linux, Android
		# Note: platform.version() and platform.release() are swapped because platform.release()
		# is more suitable to represent a compact version of the kernel.
		execenv = ExecutionEnvironment(name=name, description=platform.platform(),  
							version=platform.release(), pkgs=pkg_list,
							type=ExecutionEnvironmentType(OS(family=platform.system(), 
																		release=platform.version(), 
																		version=platform.release, 
																		arch=platform.machine() )))
		self.platform = Service(name=Name(Hostname(name)), 
					sid=SId.create_from_service_type(execenv, domain=self.domain),
					domain=self.domain,
					type=ServiceType(execenv), subservices=ArrayOf(SId)(),
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
			return self.platform.sid, self.platform

		kube_service_sid = self._get_namespace_service_kubernetes(netns)
		if kube_service_sid is not None:
			return kube_service_sid, None

		os_service_sid = self._get_namespace_service_openstack(netns)
		if os_service_sid is not None:
			return os_service_sid, None

		netfun = self._get_namespace_execenv(netns)

		net_service = Service(name=Name(netns),
				sid=SId.create_from_service_type(netfun),
				type=ServiceType(netfun), subservices=ArrayOf(SId)(),
				owner=str(self.platform.name), release=None)
		self.services.append(net_service)
		self.platform.subservices.append(net_service.sid)

		return net_service.sid, net_service

	def _get_namespace_execenv(self, netns):
		""" Get the ExecutionEnvironment associated to a network namespace """
		# TODO: Scan pid/filesystems to discover what application/packages are using this namespace
		with pyroute2.IPRoute() as iprns:
			for ns in iprns.get_netns_info():
				inode=ns['inode']
		return ExecutionEnvironment(name=netns, id=inode, description="Linux network namespace", 
												type=ExecutionEnvironmentType(LinuxNetns(inode=inode)))

	def _get_namespace_service_kubernetes(self, netns_name):
		""" Infer the kubernetes service name based on container name

			The current implementation builds an internal map between namespaces and their pod names,
			and then returns the value from this map at next calls (this speed up the execution).

			This implementation previously used the ctr command to extract data from 
			local kubelet, if installed, but this turned to be too slow.

			Now, it leverages a Python containerd package which implements the 
			GRPC API, even if the code is outdates and there is no clear documentation
			apart from the simple example (which does not work with latest grpc package).
		"""
		if self.kube_pods is None:
			self.kube_pods = {}

			# Create a map between inodes and netns names
			with pyroute2.IPRoute() as iprns:
				nsmap={}
				for netns in iprns.get_netns_info():
					nsmap[netns['inode']]=netns.get_attrs('NSINFO_PATH')[0].split('/')[-1]
	
			with grpc.insecure_channel('unix:///run/containerd/containerd.sock') as channel:
				containersv1 = containers_pb2_grpc.ContainersStub(channel)
				containers = containersv1.List(
					containers_pb2.ListContainersRequest(),
					metadata=(('containerd-namespace', 'k8s.io'),)).containers

				for container in containers:
					if self.kube_namespaces is None or container.labels['io.kubernetes.pod.namespace'] in self.kube_namespaces:
						# currently pod_name is not used, but I keep it in case it should be restored in the future
						pod_name=container.labels['io.kubernetes.pod.name']+'.pod.'+container.labels['io.kubernetes.pod.namespace']+self.kube_suffix
						pod_sid=SId(name=container.labels['io.kubernetes.pod.name'], 
											domain=self.kube_suffix, 
											namespace=container.labels['io.kubernetes.pod.namespace'],
											type=ServiceType.get_type_name(ExecutionEnvironment),
											subtype=HostType.get_type_name(Pod))
						jsondata=json.loads(container.spec.value)
						linux_namespaces=jsondata['linux']['namespaces']
					else:
						linux_namespaces = []
					for ns in linux_namespaces:
						if ns['type'] == 'network':
							try:
								inode=os.stat(ns['path']).st_ino
								self.kube_pods[nsmap[inode]]=pod_sid
							except:
								pass

		if netns_name in self.kube_pods:
			return self.kube_pods[netns_name]
		else:
			return None	

# I do not create Container here (already created in Kubernetes actuator. I just manage the internals of the Container execenv (NetworkNode)
# and create a link from NetworkNode to Container (I need to know the consumer of kubernetes to correctly reference the external component.
# sudo ctr -n k8s.io  container   info ea89d69788ee5a3aab15fa59a9122e7a7d0f89bc4af55825b017de0fb5ce778a | grep pod

	def _get_kube_suffix(self, kube_config_file):
		""" Automatically retrieve the cluster domain name from kubelet configuration """
		try:
			with open(kube_config_file,'r') as config:
				yamlconfig = yaml.safe_load(config)
				suffix=yamlconfig['clusterDomain']
		except Exception as e:
			logger.warn("Unable to get cluster domain name from kubelet configuration file: %s", e)
			suffix=""

		return suffix


	def _get_namespace_service_openstack(self, netns):
		""" Infer the OpenStack network function name based on container name """
		pass


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
				'service_name': None, 'service_id': None, 'service': None, 'networks': [], 'router': {} , 'bridges': {} , 'ovs': {}}
			if ns is None:
				self._namespaces[ns]['name']=str(self.platform.name)

			ports = {}
			self._namespaces[ns]['service_sid'], self._namespaces[ns]['service'] = self._get_namespace_service(ns)	
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
					self._namespaces[ns]['netnsmap'][netns['netnsid']]=netns.get_attrs('NSINFO_PATH')[0].split('/')[-1]
				if ns is not None:
					self._namespaces[ns]['netnsmap'][0]=None # Main network stack does not have a name, and it is referred to as '0' 

				# Create the NetworkNode object associated to this namespace
				netnode = NetworkNode(name=ns, description=description, id=None, # Kubernetes id,
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
						sid=SId.create_from_service_type(netnode, namespace=ns),
						type=ServiceType(netnode), subservices=None, owner=str(self._namespaces[ns]['service_sid']))
				self.services.append(port_service)
				if self._namespaces[ns]['service'] is not None:
					self._namespaces[ns]['service'].subservices.append(port_service.sid)

	def _add_net_service(self, service_name:Name = None, 
			net_name:str = None, 
			domain:str = None,
			namespace:str = None, 
			id:str=None, 
			description:str = "Network", 
			ipnetaddrs:ArrayOf(IPNetAddress)=ArrayOf(IPNetAddress)(), 
			nettype:object= IPNetwork,
			**kwargs): # Additional arguments to be passed to nettype
		""" Add a network service
		"""
		if net_name is None:
			net_name=str(ipnetaddrs[0]) if len(ipnetaddrs) > 0 else None
		ipnet = Network(name=net_name, id=id, description=description,
				type=NetworkType( nettype({'nets': ipnetaddrs, **kwargs } )))
		net_service= Service(name=service_name, domain=domain, namespace=namespace, 
				sid=SId.create_from_service_type(ipnet, domain=domain, namespace=namespace),
				type=ServiceType(ipnet), subservices=ArrayOf(SId)(), owner=str(self.platform.sid))
		self.services.append(net_service)
		self.platform.subservices.append(net_service.sid)
		
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
						link_type=None
						if attr.get_attrs('IFLA_INFO_KIND'):
							link_type=attr.get_attrs('IFLA_INFO_KIND')[0]
#						if attr.get_attrs('IFLA_INFO_SLAVE_KIND'):
#						    link_type=attr.get_attrs('IFLA_INFO_SLAVE_KIND')[0]

						match link_type:
							case 'veth':
								netnsid2=link.get_attrs('IFLA_LINK_NETNSID')
								if len(netnsid2) > 0:
									try:
										ns2=self._namespaces[ns]['netnsmap'][netnsid2[0]]
									except:
										continue
								else: # Same namespace
									ns2=ns
								peer2=(link.get_attrs('IFLA_LINK')[0], self._namespaces[ns2]['name'])
								net_id="if"+str(peer1[0])+'.'+str(peer1[1])+"+"+"if"+str(peer2[0])+"."+str(peer2[1])
								if [(peer1, peer2)] not in veths and [(peer2, peer1)] not in veths:
									veths.append( [(peer1, peer2)] )
									peer1_service_sid = self._namespaces[ns]['service_sid']
									peer2_service_sid = self._namespaces[ns2]['service_sid']
									description="Veth link between " + peer1_service_sid.name + " and " + peer2_service_sid.name
									# Default: try with peer1
									net_name = self._create_net_name(netns=self._namespaces[ns]['name'], if_idx=peer1[0])
#									if net_name is None: # If peer1 has not got a valid ip address, try with ip2 (may be None as well)
#										net_name = self._create_net_name(netns=self._namespaces[ns2]['name'], if_idx=peer2[0])
#										if net_name is None:
#											net_name=net_id
#
									if ns == ns2:
										use_namespace=ns # Veth is fully contained in a specific namespace
									else:
										use_namespace=None # Veth across multiple namespaces
								
									for addr in self._get_net_addrs(netns=self._namespaces[ns2]['name'], if_idx=peer2[0]):
										ipnetaddrs.append(addr)
								
									# Create services for the virtual network (even if it is only a link)
									net_service=self._add_net_service(service_name=Name(net_id), 
#																					net_name=net_name,
																					domain=self.domain, # Veth are always internal networks
																					net_name=net_id,
																					description=description,
																					ipnetaddrs=ipnetaddrs, 
																					id=net_id, 
																					nettype=VEthNetwork,
																					peers=ArrayOf(Array)([Array(peer1), Array(peer2)]))


									# Save network service name in the connected namespaces (used later to create links)
									self._namespaces[ns]['networks'].append({peer1[0]: net_service.sid})
									self._namespaces[ns2]['networks'].append({peer2[0]: net_service.sid})

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
									link_idx2 = link.get_attrs('IFLA_LINK')[0]
									ns2=self._namespaces[ns]['netnsmap'][link.get_attrs('IFLA_LINK_NETNSID')[0]]
#									net_id=self._get_namespace_ifaces(ns2)[link.get_attrs('IFLA_LINK')[0]]+"@"+str(ns2)
#net_id="ipnet:"+self._namespaces[ns2]['ifaces'][link.get_attrs('IFLA_LINK')[0]]+"@"+self._namespaces[ns2]['name']
									net_id="if"+str(peer1[0])+'.'+str(peer1[1])
									try:
										net_service=self.get_services(name=Name(net_id), filter=Network)[0]
										for ip in ipnetaddrs:
											net_service.type.getObj().type.getObj()['nets'].append(ip)
									except:
										# Macvlan is an external network, so don't set the domain here
										net_service=self._add_net_service(service_name=Name(net_id), net_name=net_id, ipnetaddrs=ipnetaddrs, id=net_id) 

									self._namespaces[ns]['networks'].append({peer1[0]: net_service.sid})

									# Add link to hosting interface
									if (link_idx2, ns2) not in self._net_deps:
										self._net_deps[(link_idx2, ns2)] = []
									self._net_deps[(link_idx2, ns2)].append(net_service.sid)
	
								else:
									logger.warn("Unsupported macvlan mode: %s", attr.get_attrs('IFLA_INFO_DATA')[0].get_attrs('IFLA_MACVLAN_MODE')[0] )

		
							case 'tun':
								net_id="tuntap:"+self._namespaces[ns]['ifaces'][link_idx]+"."+self._namespaces[ns]['name']
								net_service=self._add_net_service(service_name=Name(net_id), 
																				net_name=self._namespaces[ns]['ifaces'][link_idx], 
																				domain=self.domain, 
																				namespace=ns, description="Tun/Tap network", 
																				ipnetaddrs=ipnetaddrs,  
																				id=net_id, 
																				nettype=TunTapNetwork) 
								self._namespaces[ns]['networks'].append({peer1[0]: net_service.sid})
								

							case 'bridge':
								net_id="brnet:"+self._namespaces[ns]['ifaces'][link_idx]+"."+self._namespaces[ns]['name']
								# Bridge metanetworks are always "internal" to the ExecEnv, so set the domain name
								net_service=self._add_net_service(service_name=Name(net_id), 
																				net_name=self._namespaces[ns]['ifaces'][link_idx], 
																				domain=self.domain, 
																				namespace=ns, description="Bridged network", 
																				ipnetaddrs=ipnetaddrs,  
																				id=net_id, 
																				nettype=EthernetNetwork) 
								# This is a virtual ethernet network with one bridge as subservice with the same name of the interface
								if link_name not in self._namespaces[ns]['bridges']:
									self._namespaces[ns]['bridges'][link_name] = {}
								self._namespaces[ns]['bridges'][link_name]['net']=net_service.sid
								# Do not add the bridge interface to the list of its interfaces, otherwise this will create a recursive link between the bridge network and the bridge
#								self._namespaces[ns]['bridges'][link_name]['ifaces']=[link_idx]
								self._namespaces[ns]['bridges'][link_name]['ifaces']=[]
								self._namespaces[ns]['networks'].append({peer1[0]: net_service.sid})
								
							case 'openvswitch':
								print("########### found ovs iface: ", link_name)
								net_id="ovs:"+self._namespaces[ns]['ifaces'][link_idx]+"."+self._namespaces[ns]['name']
								# OVS metanetworks are always "internal" to the ExecEnv, so set the domain name
								net_service=self._add_net_service(service_name=Name(net_id), 
																				net_name=self._namespaces[ns]['ifaces'][link_idx], 
																				domain=self.domain, 
																				namespace=ns, description="Bridged ovs network", 
																				ipnetaddrs=ipnetaddrs,  
																				id=net_id, 
																				nettype=EthernetNetwork) 
								# This is a virtual ethernet network with one ovs as subservice with the same name of the interface
								if link_name not in self._namespaces[ns]['ovs']:
									self._namespaces[ns]['ovs'][link_name] = {}
								self._namespaces[ns]['ovs'][link_name]['net']=net_service.sid
								# Do not add the bridge interface to the list of its interfaces, otherwise this will create a recursive link between the bridge network and the bridge
#								self._namespaces[ns]['ovs'][link_name]['ifaces']=[link_idx]
								self._namespaces[ns]['ovs'][link_name]['ifaces']=[]
								self._namespaces[ns]['networks'].append({peer1[0]: net_service.sid})
								
							case 'vxlan':
								for a in attr.get_attrs('IFLA_INFO_DATA'):
									# I did not check the presence of the following attributes. I prefer to get the error
									# and to manage them when I know how to do that
									vni = a.get_attrs('IFLA_VXLAN_ID')[0]
									fw_iface_idx = a.get_attrs('IFLA_VXLAN_LINK')[0] if a.get_attrs('IFLA_VXLAN_LINK') else link_idx
									port=a.get_attrs('IFLA_VXLAN_PORT')[0]
								net_id="vxlan:"+self._namespaces[ns]['ifaces'][link_idx]+"."+self._namespaces[ns]['name']
								net_service=self._add_net_service(service_name=Name(net_id), 
																				net_name=str(vni), 
#													namespace=peer1[1],
																				description="VXLAN interface "+link_name, 
																				ipnetaddrs=ipnetaddrs, 
																				id=net_id, 
																				nettype=VXLANNetwork,
																				vni=vni,
																				port=port)
								self._namespaces[ns]['networks'].append({peer1[0]: net_service.sid})
								if (fw_iface_idx, ns) not in self._net_deps:
									self._net_deps[(fw_iface_idx, ns)] = []
								self._net_deps[(fw_iface_idx, ns)].append(net_service.sid)

							case _:
								logger.warn("Unable to manage interface %s of type: %s", link_name, link_type)


					if len(link.get_attrs('IFLA_LINKINFO')) == 0 and link_name != "lo":
						# These interfaces provide direct access to an IP network
						net_id=link_name+"."+self._namespaces[ns]['name']
						try:
							net_service=self.get_services(name=Name(net_id), filter=Network)[0] # There might already be the network, if other interfaces created it (e.g., macvlan)
#							if net_service.type.getObj().name is None:
#								net_service.type.getObj().name=str(ipnetaddrs[0]) # We use the first IP address as network identifier
						except:
							net_service=self._add_net_service(service_name=Name(net_id), net_name=net_id, ipnetaddrs=ipnetaddrs, id=net_id) 
						self._namespaces[ns]['networks'].append({peer1[0]: net_service.sid})

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
#		for ns in pyroute2.netns.listnetns()+[None]: # Last element is to discover the main network stack
# The following is better, because namespaces may have changed in the meanwhile (new namespace added)
		for ns in self._namespaces.keys():
			self._discover_routers(ns)
			self._discover_bridges(ns)
			self._discover_ovses(ns)

									
	def _discover_routers(self, ns):
		""" Discover routers
			
			@:param ns: Network namespace name
		"""
		ns_service_sid=self._namespaces[ns]['service_sid']
		with pyroute2.IPRoute(netns=ns) as iprns:
			# Discover router
			router=None
			# Loop for all network interfaces in the container
			for link in iprns.get_links(): 
				idx = link['index'] 
				# Add a router, if not done yet
				if (link.get_attr('IFLA_AF_SPEC').get_attr('AF_INET')['forwarding'] == 1 or \
						link.get_attr('IFLA_AF_SPEC').get_attr('AF_INET6').get_attr('IFLA_INET6_CONF')['forwarding'] == 1): 
					if router is None:
						self._namespaces[ns]['router']['ifaces'] = []
						routes = self._get_namespace_routes(iprns)
						netfun = NetworkFunction(name="Router", id=ns,
								description="Linux software router@"+str(ns_service_sid.name),
								type=NetworkFunctionType( Router(routes=json.dumps(routes) ) ))
						router=Service(namespace=ns, name=Name(ns_service_sid.name),
								sid=SId.create_from_service_type(netfun, namespace=ns),
								type=ServiceType( netfun ), owner=str(ns_service_sid))
						self.services.append(router)
						self.platform.subservices.append(router.sid)
						peer=Peer(service_name=ns_service_sid.name, sid=ns_service_sid, role=PeerRole.host, consumer=None)
						self.links.append( Link(name=router.name, description="Router hosted in "+self._namespaces[ns]['name'],
									sid=router.sid,
									link_type=LinkType.hosting, role=PeerRole.guest, peers=ArrayOf(Peer)([peer])))
					self._namespaces[ns]['router']['service_sid']=router.sid
					self._namespaces[ns]['router']['ifaces'].append(idx)


	def _discover_bridges(self, ns):
		""" Discover bridges 
			
			@:param ns: Network namespace name
		"""

		ns_service_sid=self._namespaces[ns]['service_sid']
		if ns is None:
			cmd=[self.brctl_exe,  'show']
		else:
			cmd=['ip', 'netns',  'exec', ns, self.brctl_exe,  'show']
		try:
	 		brctl = subprocess.run(cmd, capture_output=True)
		except Exception as e: # This may happen when brctl is not installed
		    logger.warn("No linux bridge found: %s", e) 
		    return

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
				for net in self._namespaces[ns]['networks']: # net is the {if_idx, netsid}
					for k,v in net.items(): # k=iface_idx; v=network sid
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

			net_service = Service(namespace=ns, name=Name(br+"."+str(ns_service_sid)), 
					sid=SId.create_from_service_type(netfun, namespace=ns),
					type=ServiceType(netfun), owner=str(self.platform.sid))
			self.services.append(net_service)
			self.platform.subservices.append(net_service.sid)
			self._namespaces[ns]['bridges'][br]['service_sid']=net_service.sid
			

			# Add this bridge as a subservice of its main network
			br_net_service = self.get_services_by_sid(self._namespaces[ns]['bridges'][br]['net'])
			assert len(br_net_service) == 1
			br_net_service[0].subservices.append(net_service.sid)
			
			peer=Peer(service_name=ns_service_sid.name, sid=ns_service_sid, role=PeerRole.host, consumer=None)
			self.links.append( Link(name=net_service.name, sid=net_service.sid, 
						description="Bridge hosted in "+self._namespaces[ns]['name'],
						link_type=LinkType.hosting, role=PeerRole.guest, peers=ArrayOf(Peer)([peer])))

	def _discover_ovses(self, ns):
		""" Discover OpenVSwitch bridges
			
			As far as I could understand, ovs always runs in the parent network namespace.
			I keep the same definition as for bridges just in case the ns name were necessary.

			@:param ns: Network namespace name
		"""
		if not self.ovs_discover:
			return

		ns_service_sid=self._namespaces[ns]['service_sid']

		remote = "tcp:" + self.ovs_host + ":" + str(self.ovs_port)
		logger.debug("Connecting to ovs %s", remote)
		error, stream = ovs.stream.Stream.open_block(
 			ovs.stream.Stream.open(remote)
 		)
		if error:
			logger.warn("Unable to connect to OpenVSwitch, skipping discovery")
			return

		conn = ovs.jsonrpc.Connection(stream)

		request = ovs.jsonrpc.Message.create_request(
			"get_schema",
			['Open_vSwitch']
		)

		error, reply = conn.transact_block(request)
		conn.close()

		if error:
			logger.warn("Unable to retrieve OpenVSwitch database, skipping discovery")

		if reply.error:
			logger.warn("OpenVSwith runtime error: %s", reply.error)
			return
		schema = reply.result

		schema_helper = ovs.db.idl.SchemaHelper(schema_json=schema)
		for table in ("Open_vSwitch", "Bridge", "Port", "Interface"):
			schema_helper.register_table(table)

		idl = ovs.db.idl.Idl(remote, schema_helper)
		while not idl.has_ever_connected():
			poller = ovs.poller.Poller()
			idl.wait(poller)
			poller.block()
			idl.run()

		print("iface: ", self._namespaces[ns]['networks'])
		# Print bridges, ports and interfaces, à la 'ovs-vsctl show'.
		for br in idl.tables['Bridge'].rows.values():
			print(f'Bridge {br.name}')

			netfun=NetworkFunction(name=br.name, id=br.uuid, description="OpenVSwitch bridge", type=NetworkFunctionType( Bridge({'ifaces': ArrayOf(NetworkInterface)()}) ))
			if 'ifaces' not in self._namespaces[ns]['ovs'][br.name]: # An interface should be already present, but just to be sure
				self._namespaces[ns]['ovs'][br.name]['ifaces'] = []
			for ovsport in br.ports: # OVS uses ports as a mean to bond interfaces. The CTXD model only works on interfaces
				for iface in ovsport.interfaces:
					print("iface: ", iface.name)
					match iface.type:
						case 'internal' | '':
							# A bridged interface is no more available to the namespace; it is replaced by the bridge interface
							# If there are other interfaces connected to the network of a bridged interface (veth), they must be now connected to the bridge network
							self._namespaces[ns]['ovs'][br.name]['ifaces'].append(self._namespaces[ns]['ifaces_idx'][iface.name])
							cur_idx=None
							for net in self._namespaces[ns]['networks']:
								for k,v in net.items():
									if k==self._namespaces[ns]['ifaces_idx'][iface.name]:
										cur_idx=self._namespaces[ns]['networks'].index(net)
								if cur_idx is not None:
									break
							print("Chiara pompinara")
							cur=self._namespaces[ns]['networks'].pop(cur_idx)
							print("Il culo della Miola")
							for k, v in cur.items():
								cur_iface_net=v
							# Look for the removed network in the current and other namespaces
							for ns2 in self._namespaces:
								for net in self._namespaces[ns2]['networks']:
									for k,v in net.items():
										if v==cur_iface_net:
											net[k]=self._namespaces[ns]['ovs'][br.name]['net'] 
							# Mind this is the CTXD concept of port, not related to ovs ports!!!
							if len( iface.mac ):
								mac = iface.mac[0]
							elif len(iface.mac_in_use):
								mac = iface.mac_in_use[0]
							else:
							 	mac = None
							port = NetworkInterface(id=self._namespaces[ns]['ifaces_idx'][iface.name], iface=iface.name, mac=mac, ips = None)
							print(port)
							print("done")
#				netfun.type.getObj()['ifaces'].append(port)
#
#			net_service = Service(namespace=ns, name=Name(br+"."+str(ns_service_sid)), 
#					sid=SId.create_from_service_type(netfun, namespace=ns),
#					type=ServiceType(netfun), owner=str(self.platform.sid))
#			self.services.append(net_service)
#			self.platform.subservices.append(net_service.sid)
#			self._namespaces[ns]['bridges'][br]['service_sid']=net_service.sid
#			
#
#			# Add this bridge as a subservice of its main network
#			br_net_service = self.get_services_by_sid(self._namespaces[ns]['bridges'][br]['net'])
#			assert len(br_net_service) == 1
#			br_net_service[0].subservices.append(net_service.sid)
#			
#			peer=Peer(service_name=ns_service_sid.name, sid=ns_service_sid, role=PeerRole.host, consumer=None)
#			self.links.append( Link(name=net_service.name, sid=net_service.sid, 
#						description="Bridge hosted in "+self._namespaces[ns]['name'],
#						link_type=LinkType.hosting, role=PeerRole.guest, peers=ArrayOf(Peer)([peer])))
#
						case _:
							logger.warn("Unhandled ovs interface %s", iface.type)

	def _discover_link_host(self):
		""" Discover host hosting this ExecEnv

			Since there is no way from an ExecEnv to discover its hosting hardware,
			we create this fictius link with the information provided by configuration.
			Providing this information is optional, and the owner will decide whether to
			expose this further detail.
		"""
		if self.host:
			if 'sid' in self.host:
				sid=SId.from_str(self.host['sid'])
			else:
				sid = SId(**self.host)
			
			peer=Peer(service_name=sid.name, sid=sid, role=PeerRole.host, 
					consumer=self.get_consumer(sid=sid))
			self.links.append( Link(name=self.platform.name, sid=self.platform.sid,
										description="Platform hosted on "+(str(sid)),
										link_type=LinkType.hosting, role=PeerRole.guest,
										peers=ArrayOf(Peer)([peer])))

	

	def _discover_links_networks(self):
		self._discover_links_networks_to_namespaces()
		self._discover_links_networks_hosted()
		
	def _discover_links_networks_hosted(self):
		""" Discover links between virtual networks hosted on physical interfaces """
		for k, v in self._net_deps.items():
			for net in self._namespaces[k[1]]['networks']:
				if k[0] in net:	
					peer=Peer(service_name=net[k[0]].name, sid=net[k[0]], role=PeerRole.host, consumer=None)
					for sid in v:
						self.links.append( Link(name=sid.name, 
									sid=sid,
									description="Virtual network "+sid.name+ " hosted on "+str(sid),
									link_type=LinkType.hosting, role=PeerRole.guest, 
									peers=ArrayOf(Peer)([peer])))
			

	def _discover_links_networks_to_namespaces(self):
		""" Discover links between networks and network namespaces """
		for ns in self._namespaces:
			for net in self._namespaces[ns]['networks']:
				for idx, net_service_sid in net.items():
#					peer = Peer(service_name=Name(net_service_sid.name), sid=net_service_sid, role=PeerRole.forwarding, consumer=None)
					peer = Peer(service_name=Name(self._namespaces[ns]['service_sid'].name), sid=self._namespaces[ns]['service_sid'], 
										role=PeerRole.endpoint, consumer=self.get_consumer(sid=self._namespaces[ns]['service_sid']))
#					self.links.append( Link(name=Name(self._namespaces[ns]['service_sid'].name),
#									sid=self._namespaces[ns]['service_sid'], 
#									description="Connection to network",
#									link_type=LinkType.packet_flow,
#									role=PeerRole.endpoint, peers=ArrayOf(Peer)([peer])))
					self.links.append( Link(name=Name(net_service_sid.name),
									sid=net_service_sid,
									description="Connection to network",
									link_type=LinkType.packet_flow,
									role=PeerRole.forwarding, peers=ArrayOf(Peer)([peer])))


	def _discover_links_net_functions(self):
		""" Discover links between networks and network functions """
		for ns in self._namespaces:
			logger.debug(" - router links...")
			self._discover_links_routers(ns)
			logger.debug(" - bridge links...")
			self._discover_links_bridges(ns)
			logger.debug("   done!")

	def _discover_links_routers(self, ns):
		""" Discover links between routers and networks
			
			@:param ns: Network namespace name
		"""
		if 'service_sid' in self._namespaces[ns]['router']:
			peer = Peer(service_name=Name(self._namespaces[ns]['router']['service_sid'].name), 
								sid=self._namespaces[ns]['router']['service_sid'],
								role=PeerRole.forwarding, consumer=None)
			# TODO: Use maps and lambda functions to optimise the code
			for iface_idx in self._namespaces[ns]['router']['ifaces']:
				for net in self._namespaces[ns]['networks']:
					for idx, net_service_sid in net.items():
						if iface_idx == idx:
							self.links.append( Link(name=Name(net_service_sid.name), 
									  	sid=net_service_sid,
										description="Connection to router",
										link_type=LinkType.packet_flow,
										role=PeerRole.endpoint, peers=ArrayOf(Peer)([peer])))
						
	def _discover_links_bridges(self, ns):
		""" Discover links between bridges and networks
			 (A bridge is also a subservice of a network)
			
			@:param ns: Network namespace name
		"""
		for br in self._namespaces[ns]['bridges']:
			peer = Peer(service_name=Name(self._namespaces[ns]['bridges'][br]['service_sid'].name),
								sid=self._namespaces[ns]['bridges'][br]['service_sid'],
							  	role=PeerRole.forwarding, consumer=None)
			for iface_idx in self._namespaces[ns]['bridges'][br]['ifaces']:
				for net in self._namespaces[ns]['networks']:
					for idx, net_service_sid in net.items():
						if iface_idx == idx:
							self.links.append( Link(name=Name(net_service_sid.name), 
										sid=net_service_sid, 
										description="Connection to bridge",
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
						
