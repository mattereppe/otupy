""" Context Discovery profile

	This module collects all public definition that are exported as part of the CTXD profile.
	All naming follows as much as possible the terminology in the CTXD Specification, by
	also applying generic otupy conventions.

	This definition also registers all extensions defined in the SLPF profile (`Args`, `Target`, `Profile`, `Results`).

"""

from otupy.profiles.ctxd.profile import Profile
from otupy.profiles.ctxd.actuator import *

from otupy import TargetEnum
from otupy.profiles.ctxd.data import *
from otupy.profiles.ctxd.targets import Context

# According to the standard, extended targets must be prefixed with the nsid
from otupy.profiles.ctxd.args import Args
from otupy.profiles.ctxd.results import Results
from otupy.profiles.ctxd.validation import AllowedCommandTarget, AllowedCommandArguments, validate_command, validate_args

# Make internal definitions available to external code
from otupy.profiles.ctxd.data.cloud import Cloud
from otupy.profiles.ctxd.data.consumer import Consumer
from otupy.profiles.ctxd.data.container import Container
from otupy.profiles.ctxd.data.pod import Pod
from otupy.profiles.ctxd.data.port import Port, IPAddress, IPInfo
from otupy.profiles.ctxd.data.execution_environment import ExecutionEnvironment
from otupy.profiles.ctxd.data.link_type import LinkType
from otupy.profiles.ctxd.data.network import Network
from otupy.profiles.ctxd.data.network_router import Router
from otupy.profiles.ctxd.data.network_nat import NAT
from otupy.profiles.ctxd.data.ethernet_network import EthernetNetwork
from otupy.profiles.ctxd.data.network_type import NetworkType
from otupy.profiles.ctxd.data.network_function import NetworkFunction
from otupy.profiles.ctxd.data.network_function_type import NetworkFunctionType
from otupy.profiles.ctxd.data.os import OS
from otupy.profiles.ctxd.data.peer import Peer
from otupy.profiles.ctxd.data.peer_role import PeerRole
from otupy.profiles.ctxd.data.service_type import ServiceType
from otupy.profiles.ctxd.data.vm import VM
from otupy.profiles.ctxd.data.vm import HyperVisorType
from otupy.profiles.ctxd.data.endpoint import Endpoint
from otupy.profiles.ctxd.data.api import API
from otupy.profiles.ctxd.data.ip_net_address import IPNetAddress
