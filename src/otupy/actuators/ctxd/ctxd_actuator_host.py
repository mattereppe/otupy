""" Host CTXD Actuator
	
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

from otupy import ArrayOf, actuator_implementation, Hostname, MACAddr

from otupy.actuators.ctxd.ctxd_actuator import CTXDActuator
from otupy.profiles.ctxd import *



logger = logging.getLogger(__name__)

DPKG_LIST=['dpkg','--list']
KUBELET_CONFIG_FILE='/var/lib/kubelet/config.yaml'

@actuator_implementation("ctxd-host")
class CTXDHostActuator(CTXDActuator):
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
		"""
		# Retrieve the association between pods and namespaces from scratch
		self.kube_pods=None
		# We discover again the platform at each run because packages might have changed
		self._discover_platform()
		self._discover_namespaces()

	def _discover_platform(self):
		name = platform.node()
    
		pkgs = subprocess.run(DPKG_LIST, capture_output=True)
		
		pkg_list=ArrayOf(Package)()
		for line in pkgs.stdout.splitlines():
			r = line.split(b'\t')
			if r[0].decode() == 'ii': # only report installed packages
				pkg_list.append( Package(name=r[1], version=r[2], arch=r[3], description=r[4]) )

		# TODO: Add more platform specific info for Mac, Windows, Linux, Android
		execenv = OS(name=name, description=platform.platform(), 
				family=platform.system(), version=platform.version(), release=platform.release, 
				arch=platform.machine(), pkgs=pkg_list)
		self.platform = Service(name=Name(Hostname(name)), 
					type=ServiceType(execenv), subservices=ArrayOf(Name)(),
					release=None, owner="root")
		self.services.append( self.platform )
	
		# TODO: Add a Host service for the hardware

	def _get_namespace_service_name(self, netns):
		""" Get Service name associated to a namespace

			Try to infer the external service that is using the provided namespace.
			If such Service is not found, create a Service of generic type NetworkFunction
			for the namespace (based on the fact that this is a network namespace).

			:param netns: The name of the network namespace
		"""
		if netns is None:
			return self.platform.name

		kube_service_name = self._get_namespace_service_kubernetes(netns)
		if kube_service_name is not None:
			return kube_service_name

		os_service_name = self._get_namespace_service_openstack(netns)
		if os_service_name is not None:
			return os_service_name

		netfun = self._get_namespace_function(netns)
		# If I couldn't find any service or network function associated to this namespace,
		# just keep it as a generic ExecutionEnvironment
		if netfun is None:
			netfun = self._get_namespace_execenv(netns)

		net_service = Service(name=Name(netns),
				type=ServiceType(netfun), subservices=None,
				owner=str(self.platform.name), release=None)
		self.services.append(net_service)
		self.platform.subservices.append(net_service)

		return net_service.name

	def _get_namespace_execenv(self, netns):
		""" Get the ExecutionEnvironment associated to a network namespace """
		# TODO: Scan pid/filesystems to discover what application/packages are using this namespace
		with pyroute2.IPRoute() as iprns:
			for ns in iprns.get_netns_info():
				inode=ns['inode']
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
					nsmap[netns['inode']]=netns.get_attrs('NSINFO_PATH')[0].split('/')[-1]
	
			container_list = subprocess.run(['ctr','-n','k8s.io','containers','list'],capture_output=True,text=True)
			if container_list.returncode != 0:
				logger.error("Unable to retrieve container list for Kubernetes")
				return None
			for line in container_list.stdout.split('\n'):
				r=line.split()
				if len(r) == 3 and r[2].startswith("io.containerd.runc"):
					container_info = subprocess.run(['ctr','-n','k8s.io','containers','info',r[0]],capture_output=True,text=True)
					if container_info.returncode == 0:
						jsoninfo = json.loads(container_info.stdout)
						if 'Labels' in jsoninfo and  \
							'io.kubernetes.pod.name' in jsoninfo['Labels'] and \
							'io.kubernetes.pod.namespace':
							if self.kube_namespaces is None or jsoninfo['Labels']['io.kubernetes.pod.namespace'] in self.kube_namespaces:
								pod_name=jsoninfo['Labels']['io.kubernetes.pod.name']+'.pod.'+jsoninfo['Labels']['io.kubernetes.pod.namespace']+self.kube_suffix
								linux_namespaces=jsoninfo['Spec']['linux']['namespaces']
								for ns in linux_namespaces:
									if ns['type'] == 'network':
										try:
											inode=os.stat(ns['path']).st_ino
											self.kube_pods[nsmap[inode]]=pod_name
										except Exception as e:
											# It seems some containers are still in the list even if they are not running anymore
#											logger.error("Unable to retrieve local namespace name for %s: %s", jsoninfo['Image'], e)
											pass

		if netns_name in self.kube_pods:
			return Name(Hostname(self.kube_pods[netns_name]))
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
						return Router(routes=json.dumps(routes))
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

		
	def _discover_namespaces(self):

		# Keep a list of veth links
		veths=[]
		# Loop through all workspaces
		for ns in pyroute2.netns.listnetns()+[None]: # Last element is to discover the main network stack
			ports = {}

			ns_service_name = self._get_namespace_service_name(ns)	
			with pyroute2.IPRoute(netns=ns) as iprns:
				# Retrieve the description of the interface
				if ns is None:
					description = "Default network stack"
				else:
					description = "Linux namespace"

				# Keep a map of namespace names and ids
				# Note: a numeric id is assigned to namespaces with a local scope only inside each namespace
				# Note2: a numeric id is only assigned to peer namespace (e.g., with veth links)
				# Note3: inside namespaces, the id 0 is always used for the main network stack; in the main
				# 			network stack, id 0 is used for a namespace
				# The only "global" valid identifier is the namespace name
				nsmap={}
				for netns in iprns.get_netns_info():
					nsmap[netns['netnsid']]=netns.get_attrs('NSINFO_PATH')[0].split('/')[-1]
				if ns is not None:
					nsmap[0]=None # Main network stack does not have a name, and it is referred to as '0' 

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
				
				router=None
				# Loop for all network interfaces in the container
				for link in iprns.get_links(): 
					ipnetaddrs=[]
					idx = link['index'] # The index seems the more stable identifier to use
				
					# Retrieve description and create a new port
					name = link.get_attr('IFLA_IFNAME') # The addr items do not hold iface name for interfaces without IPv4 addresses
					mac = link.get_attr('IFLA_ADDRESS')
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
						ipnetaddrs.append(IPNetAddress(ipaddress.ip_network(addr.get_attr('IFA_ADDRESS')+"/"+str(addr['prefixlen']), strict=False ) ))

					netnode.ifaces.append( port )

					# Add a router, if not done yet
					routes = []
					if (link.get_attr('IFLA_AF_SPEC').get_attr('AF_INET')['forwarding'] == 1 or \
							link.get_attr('IFLA_AF_SPEC').get_attr('AF_INET6').get_attr('IFLA_INET6_CONF')['forwarding'] == 1) and \
							router is None:
						netfun = NetworkFunction(name="Router", id=ns,
								description="Linux software router@"+str(ns_service_name),
								type=NetworkFunctionType( Router(routes=json.dumps(routes) ) ))
						router=Service(name=Name(Hostname("router."+str(ns_service_name))),
								type=ServiceType( netfun ), owner=str(ns_service_name))
						self.services.append(router)
						self.platform.subservices.append(router)
						peer=Peer(service_name=ns_service_name, role=PeerRole.host, consumer=None)
						self.links.append( Link(name=router.name, description="Router hosted in execution environment",
									link_type=LinkType.hosting, role=PeerRole.guest, peers=ArrayOf(Peer)([peer])))
	

			# Once collected all information, create the namespace service
#			self.services.append( Service(name=) # Use kubernetes id
			# netnode is a subservice of the execution environment (i.e., the container)


					peer=None
					for attr in link.get_attrs('IFLA_LINKINFO'):
						link_type=attr.get_attrs('IFLA_INFO_KIND')[0]
						match link_type:
							case 'veth':
								peer1=str(link['index'])+"@"+str(ns)
								ns2=nsmap[link.get_attrs('IFLA_LINK_NETNSID')[0]]
								peer2=str(link.get_attrs('IFLA_LINK')[0])+"@"+str(ns2)
								veth_net = (peer1, peer2)
								name=peer1+" <-> "+peer2
								if (peer1, peer2) not in veths and (peer2, peer1) not in veths:
									veths.append( (peer1, peer2) )
									ns2_service_name = self._get_namespace_service_name(ns2)
									description="Veth link between " + str(ns_service_name) + " and " + str(ns2_service_name)
									network = Network(name=name, description=description, type=NetworkType(VEthNetwork({'peers': (peer1, peer2), 'nets': ipnetaddrs})))
								
									# Create services for the virtual network (even if it is only a link)
									net_service = Service(name=Name(name), type=ServiceType(network), 
										subservices=None, owner=str(self.platform.name), release=None)
									self.platform.subservices.append(net_service.name)
									self.services.append(net_service)

									# Create links between containers and the network
									peer = Peer(service_name=net_service.name, role=PeerRole.forwarding, consumer=None)
									self.links.append( Link(name=ns_service_name, description="Connection to veth link",
												link_type=LinkType.packet_flow,
												role=PeerRole.endpoint, peers=ArrayOf(Peer)([peer])))
									self.links.append( Link(name=ns2_service_name, description="Connection to veth link",
												link_type=LinkType.packet_flow,
												role=PeerRole.endpoint, peers=ArrayOf(Peer)([peer])))
								else:
									try:
										peer = self.get_services(Name(name))[0] # There must be such service!
									except:
										peer = self.get_services(Name(peer2+" <-> "+peer1))[0]

							case 'macvlan':
								if attr.get_attrs('IFLA_INFO_DATA')[0].get_attrs('IFLA_MACVLAN_MODE')[0] == 'bridge':
									ns2=nsmap[link.get_attrs('IFLA_LINK_NETNSID')[0]]
									peer2=str(link.get_attrs('IFLA_LINK')[0])+"@"+str(ns2)
									print("********* bridge: ", peer2)
								else:
									logger.warn("Unsupported macvlan mode: ")
		
							case _:
								logger.warn("Unable to manage interface of type: %s", link_type)
								logger.warn("Add link to router for ethernet interface")

					# Add links for the router
					if (link.get_attr('IFLA_AF_SPEC').get_attr('AF_INET')['forwarding'] == 1 or \
							link.get_attr('IFLA_AF_SPEC').get_attr('AF_INET6').get_attr('IFLA_INET6_CONF')['forwarding'] == 1): 
						self.links.append( Link(name=router.name, description="Routing veth link",
									link_type=LinkType.packet_flow,
									role=PeerRole.forwarding, peers=ArrayOf(Peer)([peer])))
								
#		for service in self.services:
#			print("services: ", service.type.getObj())


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
						
