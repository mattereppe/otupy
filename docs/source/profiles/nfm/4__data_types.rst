4. NFM Data Types
=================

This section defines the NFM profile data types and the NFM extension to the
common OpenC2 ``Feature`` enumeration. References to these types elsewhere in
this profile point to the definitions in this section.

.. _nfm-type-features:

4.1 Features
------------

``Features`` is the common OpenC2 target data type used with the ``query``
Action. It is an array of requested :ref:`Feature <nfm-type-feature>` values.
NFM retains the common container semantics and extends the permitted feature
values in the following subsection.

.. rubric:: Type: ``Features`` (ArrayOf(Feature){0..10} unique)

.. list-table:: Table 4.1-1. Features Data Type
   :header-rows: 1
   :widths: 25 30 45

   * - Type Name
     - Type Definition
     - Description
   * - ``Features``
     - ArrayOf(Feature){0..10} unique
     - Zero to ten distinct capability items requested from an actuator.

.. _nfm-type-feature:

4.2 Feature
-----------

NFM extends the common ``Feature`` enumeration so a Producer can discover
flow-monitoring capabilities through ``query features``.

The profile extends the common OpenC2 type in
``otupy.profiles.nfm.targets.features``.

.. rubric:: Type: :py:class:`~otupy.profiles.nfm.targets.features.Feature` (Enumerated)

.. list-table:: Table 4.2-1. Feature Values Unique to NFM
   :header-rows: 1
   :widths: 10 25 65

   * - ID
     - Name
     - Description
   * - 5
     - ``interfaces``
     - Network interfaces available for flow monitoring.
   * - 6
     - ``information_elements``
     - Supported flow fields, such as source and destination addresses, ports,
       bytes, and packets.
   * - 7
     - ``exports``
     - Supported exporter types, such as file or collector.
   * - 8
     - ``export_options``
     - Configurable exporter parameters, such as sampling rate or output
       format.
   * - 9
     - ``flow_format``
     - Supported output formats for exported flows.
   * - 10
     - ``filters``
     - Available IPv4, IPv6, or protocol-level capture filters.

.. _nfm-type-flow-monitor:

4.3 FlowMonitor
---------------

``FlowMonitor`` defines optional IPv4 and IPv6 connection filters for a
monitoring session. It is the value of the NFM ``monitor`` target used with the
``start`` Action. Interface selection and Information Element selection are
defined by Command Arguments.

.. rubric:: Type: :py:class:`~otupy.profiles.nfm.targets.monitor.FlowMonitor` (Record)

.. list-table:: Table 4.3-1. FlowMonitor Data Type
   :header-rows: 1
   :widths: 8 24 25 10 33

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1
     - ``filter_v4``
     - ArrayOf(IPv4Connection)
     - 0..*
     - IPv4 connection filters that limit captured traffic.
   * - 2
     - ``filter_v6``
     - ArrayOf(IPv6Connection)
     - 0..*
     - IPv6 connection filters that limit captured traffic.

Both fields are optional. A Producer uses the ``interfaces`` and
``information_elements`` Command Arguments to select the flow source and fields
to collect.

.. _nfm-type-monitor-id:

4.4 MonitorID
-------------

``MonitorID`` identifies an active or scheduled monitoring session. The
Consumer returns it after creating a session, and a Producer uses it in later
``query`` or ``stop`` Commands.

.. rubric:: Type: :py:class:`~otupy.profiles.nfm.targets.monitor_id.MonitorID` (String)

.. list-table:: Table 4.4-1. MonitorID Data Type
   :header-rows: 1
   :widths: 25 25 50

   * - Name
     - Type
     - Description
   * - ``monitor_id``
     - String
     - Unique alphanumeric identifier assigned to a monitoring session.

.. _nfm-type-exporter:

4.5 Exporter
------------

``Exporter`` defines where the monitoring actuator sends or stores collected
flow data.

.. rubric:: Type: :py:class:`~otupy.profiles.nfm.data.exporter.Exporter` (Record)

.. list-table:: Table 4.5-1. Exporter Data Type
   :header-rows: 1
   :widths: 10 25 25 10 30

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 401
     - ``storage``
     - File
     - 0..1
     - Local file destination for exported flow data.
   * - 402
     - ``collectors``
     - ArrayOf(:ref:`Collector <nfm-type-collector>`)
     - 0..1
     - Downstream collectors to which flow data is transmitted.

An ``Exporter`` MUST include at least one of ``storage`` or ``collectors``.

.. _nfm-type-collector:

4.6 Collector
-------------

``Collector`` defines a remote endpoint that receives exported flow records.

.. rubric:: Type: :py:class:`~otupy.profiles.nfm.data.collector.Collector` (Record)

.. list-table:: Table 4.6-1. Collector Data Type
   :header-rows: 1
   :widths: 10 25 25 10 30

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1
     - ``address``
     - IPv4Net
     - 1
     - Destination address of the collector in CIDR notation.
   * - 2
     - ``port``
     - Port
     - 1
     - Network port that receives exported flow records.

.. _nfm-type-export-options:

4.7 ExportOptions
-----------------

``ExportOptions`` defines optional parameters that tune exporter behaviour.

.. rubric:: Type: :py:class:`~otupy.profiles.nfm.data.export_options.ExportOptions` (Record)

.. list-table:: Table 4.7-1. ExportOptions Data Type
   :header-rows: 1
   :widths: 10 25 25 10 30

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1
     - ``sampling``
     - Integer
     - 0..1
     - Sampling rate applied to packet or flow capture.
   * - 2
     - ``aggregate``
     - Boolean
     - 0..1
     - Indicates whether flow aggregation is enabled.
   * - 3
     - ``buffer``
     - Integer
     - 0..1
     - Buffer size, in records, before exporter data is flushed.
   * - 4
     - ``timeout``
     - Integer
     - 0..1
     - Timeout, in seconds, for exporter flush or rotation.
   * - 5
     - ``format``
     - :ref:`FlowFormat <nfm-type-flow-format>`
     - 0..1
     - Format used to export flow records.

.. _nfm-type-ie:

4.8 IE
------

``IE`` is an Information Element: a single flow field to collect during
monitoring, such as a source address, destination address, byte count, or
packet count.

.. rubric:: Type: :py:class:`~otupy.profiles.nfm.data.ie.IE` (String)

.. list-table:: Table 4.8-1. IE Data Type
   :header-rows: 1
   :widths: 15 25 60

   * - ID
     - Name
     - Description
   * - 501
     - ``IE``
     - String identifying a specific flow attribute or metric collected by the
       actuator.

.. _nfm-type-interface:

4.9 Interface
-------------

``Interface`` describes a network interface that can be monitored by the
actuator.

.. rubric:: Type: :py:class:`~otupy.profiles.nfm.data.interface.Interface` (Record)

.. list-table:: Table 4.9-1. Interface Data Type
   :header-rows: 1
   :widths: 8 22 25 10 35

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1
     - ``name``
     - String
     - 1
     - Interface name, such as ``eth0`` or ``ens33``.
   * - 2
     - ``description``
     - String
     - 0..1
     - Optional textual description of the interface.
   * - 3
     - ``if_id``
     - Integer
     - 0..1
     - Unique system identifier of the interface.
   * - 4
     - ``ipv4_addr``
     - ArrayOf(IPv4Addr)
     - 0..*
     - IPv4 addresses assigned to the interface.
   * - 5
     - ``ipv6_addr``
     - ArrayOf(IPv6Addr)
     - 0..*
     - IPv6 addresses assigned to the interface.
   * - 6
     - ``mac_addr``
     - MACAddr
     - 0..1
     - MAC address of the interface.
   * - 7
     - ``iface_type``
     - :ref:`IfaceType <nfm-type-iface-type>`
     - 0..1
     - Layer-2 category of the interface.
   * - 8
     - ``active``
     - String
     - 0..1
     - Current interface state, for example ``UP`` or ``DOWN``.

.. _nfm-type-iface-type:

4.10 IfaceType
--------------

``IfaceType`` identifies the underlying layer-2 category of a network
interface.

.. rubric:: Type: :py:class:`~otupy.profiles.nfm.data.iface_type.IfaceType` (Enumerated)

.. list-table:: Table 4.10-1. IfaceType Enumeration
   :header-rows: 1
   :widths: 12 25 63

   * - Value
     - Name
     - Description
   * - 1
     - ``ethernet``
     - Standard Ethernet interface.
   * - 2
     - ``loopback``
     - Virtual loopback interface.
   * - 3
     - ``tunnel``
     - Encapsulated tunnel interface, such as GRE or IPsec.
   * - 4
     - ``vlan``
     - VLAN subinterface.
   * - 5
     - ``bridge``
     - Network bridge interface.
   * - 6
     - ``wireless``
     - Wi-Fi or other wireless interface.
   * - 7
     - ``unknown``
     - Undefined or vendor-specific interface type.

.. _nfm-type-flow-format:

4.11 FlowFormat
---------------

``FlowFormat`` identifies the encoding used to export flow records.

.. rubric:: Type: :py:class:`~otupy.profiles.nfm.data.flow_format.FlowFormat` (Enumerated)

.. list-table:: Table 4.11-1. FlowFormat Enumeration
   :header-rows: 1
   :widths: 12 25 63

   * - Value
     - Name
     - Description
   * - 1
     - ``netflow5``
     - Legacy NetFlow v5 export format.
   * - 2
     - ``netflow9``
     - NetFlow v9 template-based export format.
   * - 3
     - ``ipfix``
     - IETF IP Flow Information Export format.
   * - 4
     - ``json``
     - JSON-based format for file or API outputs.
   * - 5
     - ``csv``
     - Comma-separated format for testing and analysis.
