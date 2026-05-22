""" XBOM profile

	This module collects all public definition that are exported as part of the XBOM profile.
	All naming follows as much as possible the terminology in the XBOM Specification, by
	also applying generic otupy conventions.

	This definition also registers all extensions defined in the XBOM profile (`Args`, `Target`, `Profile`, `Results`).

"""

from otupy.profiles.xbom.profile import Profile
from otupy.profiles.xbom.actuator import *

from otupy import TargetEnum
from otupy.profiles.xbom.data import *
from otupy.profiles.xbom.data.xbom_format import XbomFormat
from otupy.profiles.xbom.data.xbom_encoding import XbomEncoding
from otupy.profiles.xbom.data.xbom import CyclonedxXbom
from otupy.profiles.xbom.targets import XbomTarget


# According to the standard, extended targets must be prefixed with the nsid
from otupy.profiles.xbom.args import Args
from otupy.profiles.xbom.results import Results
from otupy.profiles.xbom.validation import AllowedCommandTarget, AllowedCommandArguments, validate_command, validate_args

# Make internal definitions available to external code
from otupy.profiles.xbom.data.service import Service, SId
from otupy.profiles.xbom.data.service_type import ServiceType
from otupy.profiles.xbom.data.link import Link
from otupy.profiles.xbom.data.link_type import LinkType
from otupy.profiles.xbom.data.cloud import Cloud
from otupy.profiles.xbom.data.name import Name
from otupy.profiles.xbom.data.consumer import Consumer
from otupy.profiles.xbom.data.port import Port, IPAddress, IPInfo
from otupy.profiles.xbom.data.execution_environment import ExecutionEnvironment
from otupy.profiles.xbom.data.execution_environment_type import ExecutionEnvironmentType
from otupy.profiles.xbom.data.os import OS
from otupy.profiles.xbom.data.linux_netns import LinuxNetns
from otupy.profiles.xbom.data.container import Container
from otupy.profiles.xbom.data.host import Host
from otupy.profiles.xbom.data.host_type import HostType
from otupy.profiles.xbom.data.vm import VM
from otupy.profiles.xbom.data.pod import Pod
from otupy.profiles.xbom.data.iot import IOT
from otupy.profiles.xbom.data.network import Network
from otupy.profiles.xbom.data.network_node import NetworkNode
from otupy.profiles.xbom.data.network_interface import NetworkInterface
from otupy.profiles.xbom.data.network_router import Router
from otupy.profiles.xbom.data.network_bridge import Bridge
from otupy.profiles.xbom.data.network_nat import NAT
from otupy.profiles.xbom.data.network_firewall import Firewall
from otupy.profiles.xbom.data.ethernet_network import EthernetNetwork
from otupy.profiles.xbom.data.ip_network import IPNetwork
from otupy.profiles.xbom.data.mobile_network import MobileNetwork
from otupy.profiles.xbom.data.veth_network import VEthNetwork
from otupy.profiles.xbom.data.tunnel_network import TunnelNetwork
from otupy.profiles.xbom.data.vlan_network import VLANNetwork
from otupy.profiles.xbom.data.vxlan_network import VXLANNetwork
from otupy.profiles.xbom.data.network_type import NetworkType
from otupy.profiles.xbom.data.network_function import NetworkFunction
from otupy.profiles.xbom.data.network_function_type import NetworkFunctionType
from otupy.profiles.xbom.data.peer import Peer
from otupy.profiles.xbom.data.peer_role import PeerRole
from otupy.profiles.xbom.data.service_type import ServiceType
from otupy.profiles.xbom.data.service import Service, SId
from otupy.profiles.xbom.data.vm import VM
from otupy.profiles.xbom.data.vm import HyperVisorType
from otupy.profiles.xbom.data.endpoint import Endpoint
from otupy.profiles.xbom.data.api import API
from otupy.profiles.xbom.data.ip_net_address import IPNetAddress
from otupy.profiles.xbom.data.package import Package
from otupy.profiles.xbom.data.server import Server
from otupy.profiles.xbom.data.web_service import WebService

# Backward compatibility aliases for old names
#SbomCtx = XbomCtx
#SbomFormat = XbomFormat

