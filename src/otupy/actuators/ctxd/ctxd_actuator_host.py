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

from otupy import ArrayOf, actuator_implementation, Hostname, MACAddr

from otupy.actuators.ctxd.ctxd_actuator import CTXDActuator
from otupy.profiles.ctxd import Service, ServiceType, Link, Package, OS, Name, IPAddress, IPInfo, Port, NetworkNode



logger = logging.getLogger(__name__)

DPKG_LIST=['dpkg','--list']

@actuator_implementation("ctxd-host")
class CTXDHostActuator(CTXDActuator):
	""" Host Actuator Manager

		Extend the base `CTDXActuator` to retrieve the description of the Operating System
        environment. This includes the connections between its (network) namespaces


	"""

	def __init__(self, **kwargs):
		""" Initialize the actuator

		"""

	def discover_context(self):
		""" Discover services and links

			Services are reset any time the update_context is invoked. 
		"""
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
		self.services.append( Service(name=Name(Hostname(name)), 
					type=ServiceType(execenv), release=None, owner="root"))
	
		# TODO: Add a Host service for the hardware

	def _discover_namespaces(self):

		# Keep a map of namespace names and ids
		iprns = pyroute2.IPRoute() # Mind ids are only visible from the host, not inside namespaces!!!
		nsmap={}
		for ns in iprns.get_netns_info():
			nsmap[ns['netnsid']]=ns.get_attrs('NSINFO_PATH')[0].split('/')[-1]
		nsmap[None]=0 # Main network stack does not have a name, and it is referred to as '0' 

		# Keep a list of veth links
		veths={}
		# Loop through all workspaces
		for ns in pyroute2.netns.listnetns()+[None]: # Last element is to discover the main network stack
			ports = {}

			with pyroute2.IPRoute(netns=ns) as ipr:
				# Retrieve the description of the interface
				if ns is None:
					description = "Default network stack"
				else:
					description = "Linux namespace"

				# Create the NetworkNode object associated to this namespace
				netnode = NetworkNode(name=ns, description=description, id=None, # Kubernetes id,
					ports=ArrayOf(Port)())

				# Retrieve the default gateway for this container
				gws={}
				for route in ipr.get_routes():
					# Routes including gateways have the RTA_GATEWAY attribute; other routes are local only
					# Currently, we only look for the default gateway (netmask 0.0.0.0 or prefixlen=0) and assume
					# there is at most one default gateway, because the data model only expects 1 gw
					# However, we create a list to account for at least v4/v6 gateways
					if route.get_attrs('RTA_GATEWAY') != [] and route['dst_len'] == 0: 
						if route.get_attr('RTA_OIF') not in gws:
							gws[route.get_attr('RTA_OIF')] = []
						gws[route.get_attr('RTA_OIF')].append(route.get_attr('RTA_GATEWAY'))
				# Loop for all network interfaces in the container
				for link in ipr.get_links(): 
					idx = link['index'] # The index seems the more stable identifier to use
				
					# Retrieve description and create a new port
					name = link.get_attr('IFLA_IFNAME') # The addr items do not hold iface name for interfaces without IPv4 addresses
					mac = link.get_attr('IFLA_ADDRESS')
					port = Port(id=link['index'], iface=name, mac=mac, ips = ArrayOf(IPInfo)())

					# Retrieve IP addresses associated to this interface and add to the port
					for addr in ipr.get_addr(index=idx):
						# Find correct gw for this interface. We currently assume at most 1 gw per IP family
						gw=None
						if idx in gws:
							for g in gws[idx]:
								if ipaddress.ip_network(addr.get_attr('IFA_ADDRESS')).version == ipaddress.ip_address(g).version:
									gw=g
						port.ips.append( IPInfo(ip=IPAddress(addr.get_attr('IFA_ADDRESS')), prefix=addr['prefixlen'], gw=gw) )

					netnode.ports.append( port )

#					print("Added node: ", netnode)


			# Once collected all information, create the namespace service
#			self.services.append( Service(name=) # Use kubernetes id

					for attr in link.get_attrs('IFLA_LINKINFO'):
						link_type=attr.get_attrs('IFLA_INFO_KIND')[0]
						match link_type:
							case 'veth':
								peerns = nsmap[link.get_attrs('IFLA_LINK_NETNSID')[0]] if ns == None else None
								peer1=(link['index'], ns)
								peer2=(link.get_attrs('IFLA_LINK')[0],  ns2)
#								print("Peer: ", link['index'], "/", ns, " <-> ", link.get_attrs('IFLA_LINK')[0], "/", nsmap[link.get_attrs('IFLA_LINK_NETNSID')[0]] if ns == None else None )
								print("peers: ", peer1, ", ", peer2)
								name=ns+"<->"+ns2
								description="Veth link between " + ns + " and " + ns2 if ns2 is not None else " host"
								id=hash(str(peer1)+str(peer2))

								
							case 'macvlan':
								pass
		
							case _:
#logger.warn("Unable to manage interface of type: %s", link_type)
								pass

#			# Create pseudo networks for veth links
#			veths={}
#			for links in ipr.get_links():
#				if links.get_attr('IFLA_LINKINFO') is not None and 
#						links.get_attr('IFLA_LINKINFO').get_attr('IFLA_INFO_KIND') == 'veth':
#					if	(links['index'], links.get_attr('IFLA_LINK')) in veths:
#						if veths[(links['index'], links.get_attr('IFLA_LINK'))]['namespace'] == (


						
