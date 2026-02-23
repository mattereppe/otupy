""" XBOM additional data types

	This modules defines additional data types specific for the XBOM profile.
"""

from otupy.profiles.xbom.data import *
from otupy.profiles.xbom.data.sbom_format import SbomFormat
from otupy.profiles.xbom.data.abstract_xbom import Xbom
from otupy.profiles.xbom.data.xbom import CyclonedxXbom

# Base classes
from otupy.profiles.xbom.data.xbom_object import XBOMObject
from otupy.profiles.xbom.data.host import Host
from otupy.profiles.xbom.data.execution_environment import ExecutionEnvironment

# Host-derived classes
from otupy.profiles.xbom.data.vm import VM, HyperVisorType
from otupy.profiles.xbom.data.pod import Pod
from otupy.profiles.xbom.data.iot import IOT
from otupy.profiles.xbom.data.server import Server

# ExecutionEnvironment-derived classes
from otupy.profiles.xbom.data.container import Container
from otupy.profiles.xbom.data.os import OS

# Software components
from otupy.profiles.xbom.data.library import Library
from otupy.profiles.xbom.data.package import Package

# Network types
from otupy.profiles.xbom.data.network import Network
from otupy.profiles.xbom.data.network_interface import IPAddress, IPInfo, NetworkInterface
from otupy.profiles.xbom.data.network_node import NetworkNode
from otupy.profiles.xbom.data.network_router import Router
from otupy.profiles.xbom.data.network_nat import NAT
from otupy.profiles.xbom.data.network_function import NetworkFunction
from otupy.profiles.xbom.data.network_function_type import NetworkFunctionType
from otupy.profiles.xbom.data.ip_network import IPNetwork
from otupy.profiles.xbom.data.ip_net_address import IPNetAddress
from otupy.profiles.xbom.data.ethernet_network import EthernetNetwork
from otupy.profiles.xbom.data.vlan_network import VLANNetwork
from otupy.profiles.xbom.data.mobile_network import MobileNetwork

# Service types
from otupy.profiles.xbom.data.service import Service
from otupy.profiles.xbom.data.service_type import ServiceType
from otupy.profiles.xbom.data.endpoint import Endpoint
from otupy.profiles.xbom.data.api import API
from otupy.profiles.xbom.data.port import Port
from otupy.profiles.xbom.data.cloud import Cloud
from otupy.profiles.xbom.data.application import Application
from otupy.profiles.xbom.data.web_service import WebService

# Relationship types
from otupy.profiles.xbom.data.link import Link
from otupy.profiles.xbom.data.link_type import LinkType
from otupy.profiles.xbom.data.peer import Peer, PeerRole
from otupy.profiles.xbom.data.name import Name
from otupy.profiles.xbom.data.consumer import Consumer
from otupy.profiles.xbom.data.network_type import NetworkType