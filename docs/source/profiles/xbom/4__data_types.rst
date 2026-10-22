4. XBOM Data Types
==================

This section defines the data types used by the XBOM Command and Response
extensions and summarizes the object model from which XBOM representations are
constructed. The Command and Response exchange carries serialized BOM strings;
the model types in later subsections describe the structured data that can be
used to create those strings.

References to a type name use the type label itself as a link to the
corresponding inline code documentation.

.. _xbom-type-boms:

4.1 XbomTarget
--------------

``XbomTarget`` is the value of the profile-defined ``boms`` target. It is a
list of component identifiers; a zero-length list asks for all BOMs available
through the addressed Consumer.

.. rubric:: Type: :py:class:`XbomTarget <otupy.profiles.xbom.targets.xbom_ctx.XbomTarget>` (ArrayOf(String))

.. list-table:: Table 4.1-1. XbomTarget Data Type
   :header-rows: 1
   :widths: 25 25 50

   * - Name
     - Type
     - Description
   * - ``boms``
     - ArrayOf(String)
     - Zero or more component identifiers that select the BOMs to retrieve.
       The identifiers have no additional format constraint in the profile.

.. _xbom-type-xbom-format:

4.2 XbomFormat
--------------

``XbomFormat`` identifies the data model used to express a BOM.

.. rubric:: Type: :py:class:`XbomFormat <otupy.profiles.xbom.data.xbom_format.XbomFormat>` (Enumerated)

.. list-table:: Table 4.2-1. XbomFormat Values
   :header-rows: 1
   :widths: 15 25 60

   * - ID
     - Name
     - Description
   * - 0
     - ``ctxd``
     - otupy native data model for context discovery.
   * - 1
     - ``cyclonedx``
     - CycloneDX data model for application security context and software
       supply-chain component analysis.

.. _xbom-type-xbom-encoding:

4.3 XbomEncoding
----------------

``XbomEncoding`` identifies the serialization encoding used to transport a BOM
as a string. An actuator selects only encodings that it supports for the
requested format.

.. rubric:: Type: :py:class:`XbomEncoding <otupy.profiles.xbom.data.xbom_encoding.XbomEncoding>` (Enumerated)

.. list-table:: Table 4.3-1. XbomEncoding Values
   :header-rows: 1
   :widths: 15 25 60

   * - ID
     - Name
     - Description
   * - 0
     - ``json``
     - JavaScript Object Notation encoding.
   * - 1
     - ``xml``
     - Extensible Markup Language encoding.
   * - 2
     - ``yaml``
     - YAML serialization.

.. _xbom-type-xbom:

4.4 XBOM Containers
-------------------

``Xbom`` is the abstract interface implemented by BOM representations. It
separates actuator code from a particular BOM standard. The current concrete
implementation is ``CyclonedxXbom``.

.. rubric:: Type: :py:class:`Xbom <otupy.profiles.xbom.data.abstract_xbom.Xbom>` (Abstract Record)

.. list-table:: Table 4.4-1. Xbom Fields
   :header-rows: 1
   :widths: 25 25 10 40

   * - Name
     - Type
     - #
     - Description
   * - ``format``
     - :ref:`XbomFormat <xbom-type-xbom-format>`
     - 1
     - Identifies the data model implemented by the container.
   * - ``bom``
     - Implementation-defined
     - 1
     - Underlying BOM object managed by the concrete implementation.

.. _xbom-type-cyclonedx-xbom:

4.4.1 CyclonedxXbom
^^^^^^^^^^^^^^^^^^^

.. rubric:: Type: :py:class:`CyclonedxXbom <otupy.profiles.xbom.data.xbom.CyclonedxXbom>` (Xbom)

``CyclonedxXbom`` wraps a CycloneDX BOM and supplies the conversion and
dependency helpers used by the XBOM implementation. Its ``format`` value
defaults to ``cyclonedx``.

4.5 Shared Identification and Service Model
-------------------------------------------

.. _xbom-type-xbom-object:

4.5.1 XBOMObject
^^^^^^^^^^^^^^^^

``XBOMObject`` provides the common descriptive properties inherited by many
model objects.

.. rubric:: Type: :py:class:`XBOMObject <otupy.profiles.xbom.data.xbom_object.XBOMObject>` (Record)

.. list-table:: Table 4.5.1-1. XBOMObject Fields
   :header-rows: 1
   :widths: 25 25 10 40

   * - Name
     - Type
     - #
     - Description
   * - ``name``
     - String
     - 0..1
     - Human-readable name of the modeled node or resource.
   * - ``id``
     - String
     - 0..1
     - Preferably globally unique identifier.
   * - ``description``
     - String
     - 0..1
     - Generic description, including the component role where useful.

.. _xbom-type-name:

4.5.2 Name
^^^^^^^^^^

``Name`` represents one identifier for a Service or Link. Exactly one choice is
used, allowing stable comparison of identifiers.

.. rubric:: Type: :py:class:`Name <otupy.profiles.xbom.data.name.Name>` (Choice)

.. list-table:: Table 4.5.2-1. Name Choices
   :header-rows: 1
   :widths: 25 25 50

   * - Name
     - Type
     - Description
   * - ``uri``
     - URI
     - URI used as an identifier; it need not be a reachable locator.
   * - ``reverse-dns``
     - String
     - Reverse-DNS-style unique identifier.
   * - ``uuid``
     - UUID
     - 128-bit UUID identifier.
   * - ``local``
     - String
     - Locally meaningful identifier with no global uniqueness requirement.

.. _xbom-type-sid:

4.5.3 SId
^^^^^^^^^

``SId`` is a structured Service Identifier. Its string representation follows
``<type>:<subtype>/<domain>/<namespace>/<name>@<version>``; unset parts may be
absent or have the value ``None``.

.. rubric:: Type: :py:class:`SId <otupy.profiles.xbom.data.service.SId>` (Record)

.. list-table:: Table 4.5.3-1. SId Fields
   :header-rows: 1
   :widths: 22 22 10 46

   * - Name
     - Type
     - #
     - Description
   * - ``type``
     - String
     - 0..1
     - Main service type, normally derived from :ref:`ServiceType <xbom-type-service-type>`.
   * - ``subtype``
     - String
     - 0..1
     - More specific type information supplied by the selected service model.
   * - ``domain``
     - String
     - 0..1
     - Administrative or provider domain.
   * - ``namespace``
     - String
     - 0..1
     - Tenant or namespace within the domain.
   * - ``name``
     - String
     - 0..1
     - Identifier used by the concrete service model.
   * - ``version``
     - String
     - 0..1
     - Service or software version.

.. _xbom-type-service:

4.5.4 Service
^^^^^^^^^^^^^

``Service`` is the general representation of a digital resource. A Service can
describe software, APIs, devices, infrastructure components, or their
subcomponents, while Links express their dependencies.

.. rubric:: Type: :py:class:`Service <otupy.profiles.xbom.data.service.Service>` (Record)

.. list-table:: Table 4.5.4-1. Service Fields
   :header-rows: 1
   :widths: 22 22 10 46

   * - Name
     - Type
     - #
     - Description
   * - ``name``
     - :ref:`Name <xbom-type-name>`
     - 0..1
     - Service identifier.
   * - ``sid``
     - :ref:`SId <xbom-type-sid>`
     - 0..1
     - Structured service identifier.
   * - ``domain`` / ``namespace``
     - String
     - 0..1 each
     - Scope in which the Service is defined.
   * - ``type``
     - :ref:`ServiceType <xbom-type-service-type>`
     - 0..1
     - Concrete service model used to describe the resource.
   * - ``subservices``
     - ArrayOf(SId)
     - 0..*
     - Identifiers of constituent subservices.
   * - ``owner`` / ``release``
     - String
     - 0..1 each
     - Service owner and release information.

.. _xbom-type-service-type:

4.5.5 ServiceType
^^^^^^^^^^^^^^^^^

.. rubric:: Type: :py:class:`ServiceType <otupy.profiles.xbom.data.service_type.ServiceType>` (Choice)

``ServiceType`` selects the detailed model used for a Service.

.. list-table:: Table 4.5.5-1. ServiceType Choices
   :header-rows: 1
   :widths: 25 30 45

   * - Name
     - Model
     - Description
   * - ``app``
     - :py:class:`Application <otupy.profiles.xbom.data.application.Application>`
     - Software application.
   * - ``execenv``
     - :py:class:`ExecutionEnvironment <otupy.profiles.xbom.data.execution_environment.ExecutionEnvironment>`
     - Software execution environment.
   * - ``host``
     - :py:class:`Host <otupy.profiles.xbom.data.host.Host>`
     - Physical or virtual host.
   * - ``netnode``
     - :py:class:`NetworkNode <otupy.profiles.xbom.data.network_node.NetworkNode>`
     - Network slice or namespace.
   * - ``api`` / ``webservice``
     - :py:class:`API <otupy.profiles.xbom.data.api.API>` / :py:class:`WebService <otupy.profiles.xbom.data.web_service.WebService>`
     - Exposed programmable or Web interface.
   * - ``cloud`` / ``network`` / ``netfun``
     - Cloud / :py:class:`Network <otupy.profiles.xbom.data.network.Network>` / :py:class:`NetworkFunction <otupy.profiles.xbom.data.network_function.NetworkFunction>`
     - Infrastructure, network, or packet-processing service.
   * - ``os`` / ``container`` / ``pod``
     - OS / Container / Pod
     - Execution or orchestration model.
   * - ``iot`` / ``vm`` / ``server``
     - IoT / VM / Server
     - Host realization.

.. _xbom-type-link:

4.5.6 Link and Peer
^^^^^^^^^^^^^^^^^^^

A ``Link`` expresses a relationship from a Service to one or more ``Peer``
services. Roles and link types make the relationship direction and purpose
explicit.

.. rubric:: Type: :py:class:`Link <otupy.profiles.xbom.data.link.Link>` (Record)

.. list-table:: Table 4.5.6-1. Link Fields
   :header-rows: 1
   :widths: 22 22 10 46

   * - Name
     - Type
     - #
     - Description
   * - ``name``
     - :ref:`Name <xbom-type-name>`
     - 0..1
     - Identifier for the relationship.
   * - ``sid``
     - :ref:`SId <xbom-type-sid>`
     - 0..1
     - Service identifier of the Link owner.
   * - ``description``
     - String
     - 0..1
     - Description of the relationship.
   * - ``link_type``
     - :py:class:`LinkType <otupy.profiles.xbom.data.link_type.LinkType>`
     - 0..1
     - Semantic type of the relationship.
   * - ``role``
     - :py:class:`PeerRole <otupy.profiles.xbom.data.peer_role.PeerRole>`
     - 0..1
     - Role of the Link owner in the relationship.
   * - ``peers``
     - ArrayOf(:py:class:`Peer <otupy.profiles.xbom.data.peer.Peer>`)
     - 0..*
     - Services at the other end of the relationship.

.. _xbom-type-peer:

.. rubric:: Type: :py:class:`Peer <otupy.profiles.xbom.data.peer.Peer>` (Record)

.. list-table:: Table 4.5.6-2. Peer Fields
   :header-rows: 1
   :widths: 25 25 10 40

   * - Name
     - Type
     - #
     - Description
   * - ``service_name``
     - :ref:`Name <xbom-type-name>`
     - 0..1
     - Identifier of the peer Service.
   * - ``sid``
     - :ref:`SId <xbom-type-sid>`
     - 0..1
     - Structured identifier of the peer Service.
   * - ``role``
     - :py:class:`PeerRole <otupy.profiles.xbom.data.peer_role.PeerRole>`
     - 0..1
     - Peer role in the relationship.
   * - ``consumer``
     - :ref:`Consumer <xbom-type-consumer>`
     - 0..1
     - OpenC2 Consumer used to reach the peer, when relevant.

.. _xbom-type-link-type:

.. rubric:: Type: :py:class:`LinkType <otupy.profiles.xbom.data.link_type.LinkType>` (Enumerated)

.. list-table:: Table 4.5.6-3. LinkType Values
   :header-rows: 1
   :widths: 12 23 65

   * - ID
     - Name
     - Description
   * - 1
     - ``api``
     - API dependency.
   * - 2
     - ``hosting``
     - Hosting relationship.
   * - 3
     - ``packet_flow``
     - Packet-flow relationship.
   * - 4
     - ``controlling``
     - Control relationship.
   * - 5
     - ``protecting``
     - Protection relationship.
   * - 6
     - ``containing``
     - Containment relationship.

.. _xbom-type-peer-role:

.. rubric:: Type: :py:class:`PeerRole <otupy.profiles.xbom.data.peer_role.PeerRole>` (Enumerated)

``PeerRole`` provides the roles ``client``, ``server``, ``guest``, ``host``,
``ingress``, ``egress``, ``both``, ``control``, ``controlled``, ``protect``,
``protected``, ``contain``, ``contained``, ``forwarding``, and ``endpoint``.
They respectively capture client/server, hosting, traffic direction, control,
protection, containment, forwarding, and endpoint semantics.

.. _xbom-type-consumer:

4.5.7 Consumer
^^^^^^^^^^^^^^

``Consumer`` describes how an XBOM peer can be reached as an OpenC2 Consumer.

.. rubric:: Type: :py:class:`Consumer <otupy.profiles.xbom.data.consumer.Consumer>` (Record)

.. list-table:: Table 4.5.7-1. Consumer Fields
   :header-rows: 1
   :widths: 22 22 10 46

   * - Name
     - Type
     - #
     - Description
   * - ``host`` / ``port`` / ``protocol``
     - String / Integer / L4-Protocol
     - 0..1 each
     - Network location and transport protocol of the Consumer.
   * - ``endpoint``
     - String
     - 0..1
     - Endpoint path, for example a well-known OpenC2 endpoint.
   * - ``transfer`` / ``encoding``
     - String
     - 0..1 each
     - Transfer protocol and message encoding.
   * - ``profile``
     - String
     - 0..1
     - Profile implemented by the Consumer; defaults to XBOM in the model.
   * - ``actuator``
     - Map
     - 0..1
     - Actuator specifier map used to address the Consumer-side implementation.

4.6 Compute, Runtime, and Software Types
-----------------------------------------

.. _xbom-type-execution-environment:

4.6.1 ExecutionEnvironment
^^^^^^^^^^^^^^^^^^^^^^^^^^

``ExecutionEnvironment`` models the software resources that allow an
application to run, including associated libraries, packages, and applications.

.. rubric:: Type: :py:class:`ExecutionEnvironment <otupy.profiles.xbom.data.execution_environment.ExecutionEnvironment>` (XBOMObject)

.. list-table:: Table 4.6.1-1. ExecutionEnvironment Fields
   :header-rows: 1
   :widths: 22 22 10 46

   * - Name
     - Type
     - #
     - Description
   * - ``version``
     - String
     - 0..1
     - Version of the execution environment.
   * - ``type``
     - :py:class:`ExecutionEnvironmentType <otupy.profiles.xbom.data.execution_environment_type.ExecutionEnvironmentType>`
     - 0..1
     - Concrete environment realization.
   * - ``libs``
     - ArrayOf(:py:class:`Library <otupy.profiles.xbom.data.library.Library>`)
     - 0..*
     - Libraries available in the environment.
   * - ``pkgs``
     - ArrayOf(:py:class:`Package <otupy.profiles.xbom.data.package.Package>`)
     - 0..*
     - Packages available in the environment.
   * - ``apps``
     - ArrayOf(:py:class:`Application <otupy.profiles.xbom.data.application.Application>`)
     - 0..*
     - Applications hosted by the environment.

.. _xbom-type-execution-environment-type:

.. rubric:: Type: :py:class:`ExecutionEnvironmentType <otupy.profiles.xbom.data.execution_environment_type.ExecutionEnvironmentType>` (Choice)

The registered choices are ``container`` (:py:class:`Container <otupy.profiles.xbom.data.container.Container>`),
``os`` (:py:class:`OS <otupy.profiles.xbom.data.os.OS>`), and ``netns``
(:py:class:`LinuxNetns <otupy.profiles.xbom.data.linux_netns.LinuxNetns>`).

.. _xbom-type-host:

4.6.2 Host
^^^^^^^^^^

``Host`` describes the hardware or virtual resource that provides resources to
an ExecutionEnvironment.

.. rubric:: Type: :py:class:`Host <otupy.profiles.xbom.data.host.Host>` (XBOMObject)

.. list-table:: Table 4.6.2-1. Host Fields
   :header-rows: 1
   :widths: 22 22 10 46

   * - Name
     - Type
     - #
     - Description
   * - ``vendor`` / ``model`` / ``release``
     - String
     - 0..1 each
     - Manufacturer, model, and release information.
   * - ``serial``
     - String
     - 0..1
     - Device serial number.
   * - ``firmware`` / ``version``
     - String
     - 0..1 each
     - Firmware name and version.
   * - ``type``
     - :py:class:`HostType <otupy.profiles.xbom.data.host_type.HostType>`
     - 0..1
     - Concrete host realization.

.. _xbom-type-host-type:

.. rubric:: Type: :py:class:`HostType <otupy.profiles.xbom.data.host_type.HostType>` (Choice)

The registered choices are ``server``, ``vm``, ``pod``, and ``iot``, represented
by :py:class:`Server <otupy.profiles.xbom.data.server.Server>`,
:py:class:`VM <otupy.profiles.xbom.data.vm.VM>`,
:py:class:`Pod <otupy.profiles.xbom.data.pod.Pod>`, and
:py:class:`IOT <otupy.profiles.xbom.data.iot.IOT>`.

4.6.3 Runtime and Software Detail Types
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table:: Table 4.6.3-1. Runtime and Software Detail Types
   :header-rows: 1
   :widths: 28 25 47

   * - Type
     - Fields
     - Description
   * - :py:class:`Application <otupy.profiles.xbom.data.application.Application>`
     - ``name``, ``id``, ``description``, ``version``, ``owner``, ``app_type``
     - Software application model.
   * - :py:class:`Package <otupy.profiles.xbom.data.package.Package>`
     - Common XBOMObject fields; ``version``, ``arch``, ``source``, ``pkg_type``
     - Software package model.
   * - :py:class:`Library <otupy.profiles.xbom.data.library.Library>`
     - Common XBOMObject fields; ``version``, ``source``, ``lib_type``
     - Software library model.
   * - :py:class:`OS <otupy.profiles.xbom.data.os.OS>`
     - ``family``, ``version``, ``release``, ``arch``
     - Operating-system execution environment.
   * - :py:class:`Container <otupy.profiles.xbom.data.container.Container>`
     - ``namespace``, ``status``, ``image``
     - Container execution environment.
   * - :py:class:`LinuxNetns <otupy.profiles.xbom.data.linux_netns.LinuxNetns>`
     - ``inode``
     - Linux network namespace, used as a lightweight execution environment.
   * - :py:class:`Server <otupy.profiles.xbom.data.server.Server>`
     - No additional fields in the current implementation
     - Physical server placeholder for future extension.
   * - :py:class:`VM <otupy.profiles.xbom.data.vm.VM>`
     - ``hypervisor``, ``hypervisor_type``, ``image``
     - Virtual-machine realization.
   * - :py:class:`Pod <otupy.profiles.xbom.data.pod.Pod>`
     - ``namespace``
     - Kubernetes Pod realization.
   * - :py:class:`IOT <otupy.profiles.xbom.data.iot.IOT>`
     - ``type``
     - IoT-device realization.
   * - :py:class:`Cloud <otupy.profiles.xbom.data.cloud.Cloud>`
     - Common XBOMObject fields; ``type``
     - Cloud service model.

.. rubric:: Type: :py:class:`HyperVisorType <otupy.profiles.xbom.data.vm.HyperVisorType>` (Enumerated)

``HyperVisorType`` has the values ``native`` (bare-metal) and ``hosted``.

4.7 APIs and Service Endpoints
------------------------------

.. _xbom-type-api:

4.7.1 API
^^^^^^^^^

``API`` represents an interface that can be invoked over the network, including
RPC, REST, SOAP, WSDL, and custom API styles.

.. rubric:: Type: :py:class:`API <otupy.profiles.xbom.data.api.API>` (XBOMObject)

.. list-table:: Table 4.7.1-1. API Fields
   :header-rows: 1
   :widths: 22 22 10 46

   * - Name
     - Type
     - #
     - Description
   * - ``type``
     - String
     - 0..1
     - API style or standard.
   * - ``endpoints``
     - ArrayOf(:ref:`Endpoint <xbom-type-endpoint>`)
     - 0..*
     - Interfaces exposed by the API.
   * - ``provider`` / ``version``
     - String
     - 0..1 each
     - API provider and version.

.. _xbom-type-endpoint:

4.7.2 Endpoint
^^^^^^^^^^^^^^

.. rubric:: Type: :py:class:`Endpoint <otupy.profiles.xbom.data.endpoint.Endpoint>` (Record)

.. list-table:: Table 4.7.2-1. Endpoint Fields
   :header-rows: 1
   :widths: 22 22 10 46

   * - Name
     - Type
     - #
     - Description
   * - ``description``
     - String
     - 0..1
     - Human-readable endpoint description.
   * - ``endpoint_type``
     - String
     - 0..1
     - Architecture or interface standard, such as REST or SOAP.
   * - ``transport`` / ``transfer`` / ``encoding``
     - String
     - 0..1 each
     - Transport protocol, message transfer protocol, and encoding.
   * - ``uri``
     - String
     - 0..1
     - Base URI used to contact the endpoint.
   * - ``provider``
     - String
     - 0..1
     - Owner of the exposed service.

.. rubric:: Type: :py:class:`WebService <otupy.profiles.xbom.data.web_service.WebService>` (Record)

``WebService`` records ``description``, ``server``, ``port``, ``endpoint``, and
``owner`` for a Web-facing service.

4.8 Network Model
-----------------

.. _xbom-type-network:

4.8.1 Network, Nodes, and Interfaces
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. rubric:: Type: :py:class:`Network <otupy.profiles.xbom.data.network.Network>` (XBOMObject)

``Network`` has a ``type`` (:py:class:`NetworkType <otupy.profiles.xbom.data.network_type.NetworkType>`) and
an optional ``version``. It represents the overall network service.

.. _xbom-type-network-type:

.. rubric:: Type: :py:class:`NetworkType <otupy.profiles.xbom.data.network_type.NetworkType>` (Choice)

The current implementation registers ``ip``, ``eth``, ``802.11``, ``802.15``,
``zigbee``, ``vlan``, ``tun``, ``veth``, ``vxlan``, ``vpn``, ``lorawan``,
``wan``, and ``5G``. It deliberately remains partial: only the types described
in :ref:`xbom-network-descriptors` provide structured configuration fields.

.. rubric:: Type: :py:class:`NetworkNode <otupy.profiles.xbom.data.network_node.NetworkNode>` (XBOMObject)

``NetworkNode`` has one additional field, ``ifaces``, an
``ArrayOf(NetworkInterface)`` describing the interfaces in a network slice.

.. rubric:: Type: :py:class:`NetworkInterface <otupy.profiles.xbom.data.network_interface.NetworkInterface>` (Record)

.. list-table:: Table 4.8.1-1. NetworkInterface Fields
   :header-rows: 1
   :widths: 22 22 10 46

   * - Name
     - Type
     - #
     - Description
   * - ``description``
     - String
     - 0..1
     - Human-readable interface description.
   * - ``id`` / ``iface``
     - String
     - 0..1 each
     - Interface identifier and operating-system interface name.
   * - ``mac``
     - MACAddr
     - 0..1
     - Layer-2 address.
   * - ``ips``
     - ArrayOf(:py:class:`IPInfo <otupy.profiles.xbom.data.network_interface.IPInfo>`)
     - 0..*
     - Addresses and gateways associated with the interface.

.. _xbom-type-ip-info:

.. rubric:: Type: :py:class:`IPInfo <otupy.profiles.xbom.data.network_interface.IPInfo>` (Record)

``IPInfo`` contains an ``ip`` value of type :py:class:`IPAddress <otupy.profiles.xbom.data.network_interface.IPAddress>`,
a prefix length, and an optional default gateway. The address itself is required.

.. _xbom-type-ip-address:

.. rubric:: Type: :py:class:`IPAddress <otupy.profiles.xbom.data.network_interface.IPAddress>` (Choice)

``IPAddress`` automatically chooses ``ipv4`` or ``ipv6`` according to the supplied
address.

.. rubric:: Type: :py:class:`IPNetAddress <otupy.profiles.xbom.data.ip_net_address.IPNetAddress>` (Choice)

``IPNetAddress`` similarly holds either an IPv4 or IPv6 network and prefix.

.. rubric:: Type: :py:class:`Port <otupy.profiles.xbom.data.port.Port>` (Record)

``Port`` is a standalone interface record with ``description``, ``id``, ``iface``,
``mac``, and ``ips`` fields. It mirrors the current NetworkInterface addressing
model.

.. _xbom-network-descriptors:

4.8.2 Network Technology Descriptors
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following Maps provide structured fields for the corresponding NetworkType
choices.

.. list-table:: Table 4.8.2-1. Network Technology Descriptors
   :header-rows: 1
   :widths: 30 30 40

   * - Type
     - Fields
     - Description
   * - :py:class:`IPNetwork <otupy.profiles.xbom.data.ip_network.IPNetwork>`
     - ``nets``: ArrayOf(IPNetAddress)
     - Generic IP network.
   * - :py:class:`EthernetNetwork <otupy.profiles.xbom.data.ethernet_network.EthernetNetwork>`
     - ``nets``, ``netv4nets``, ``netv6nets``
     - Ethernet network, including virtual or physical infrastructure.
   * - :py:class:`MobileNetwork <otupy.profiles.xbom.data.mobile_network.MobileNetwork>`
     - ``name``, ``mcc``, ``mnc``, ``region``, ``set``, ``netv4addrs``, ``netv6addrs``
     - Mobile 4G/5G network description.
   * - :py:class:`VLANNetwork <otupy.profiles.xbom.data.vlan_network.VLANNetwork>`
     - ``name``, ``vlan_id``, ``type``, ``nets``
     - Virtual LAN segment.
   * - :py:class:`VEthNetwork <otupy.profiles.xbom.data.veth_network.VEthNetwork>`
     - ``peers``: ArrayOf(VEthPeer), ``nets``
     - Virtual Ethernet point-to-point link.
   * - :py:class:`TunnelNetwork <otupy.profiles.xbom.data.tunnel_network.TunnelNetwork>`
     - ``server``, ``nets``
     - Tunnel or VPN link.
   * - :py:class:`VXLANNetwork <otupy.profiles.xbom.data.vxlan_network.VXLANNetwork>`
     - ``vni``, ``port``, ``nets``
     - Virtual eXtensible LAN descriptor.

4.8.3 Network Functions
^^^^^^^^^^^^^^^^^^^^^^^

.. rubric:: Type: :py:class:`NetworkFunction <otupy.profiles.xbom.data.network_function.NetworkFunction>` (XBOMObject)

``NetworkFunction`` adds ``type`` and ``version`` to the common XBOMObject
fields. It represents forwarding or security functionality implemented on
hardware, general-purpose hosts, or virtualized environments.

.. rubric:: Type: :py:class:`NetworkFunctionType <otupy.profiles.xbom.data.network_function_type.NetworkFunctionType>` (Choice)

The registered function types are ``router``, ``vpn``, ``nat``, ``bridge``, and
``fw``. The current definition is explicitly partial.

.. list-table:: Table 4.8.3-1. Network Function Descriptor Types
   :header-rows: 1
   :widths: 30 30 40

   * - Type
     - Fields
     - Description
   * - :py:class:`Router <otupy.profiles.xbom.data.network_router.Router>`
     - ``routes``: String
     - Routing configuration; its internal table structure is not yet defined.
   * - :py:class:`Bridge <otupy.profiles.xbom.data.network_bridge.Bridge>`
     - ``table``: String; ``ifaces``: ArrayOf(NetworkInterface)
     - Ethernet bridge or switch configuration.
   * - :py:class:`NAT <otupy.profiles.xbom.data.network_nat.NAT>`
     - ``rules``: ArrayOf(String)
     - Network address translation rules.
   * - :py:class:`Firewall <otupy.profiles.xbom.data.network_firewall.Firewall>`
     - ``rules``: String
     - Firewall configuration placeholder; rule structure is not yet defined.

