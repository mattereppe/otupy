4. FCLM Data Types
==================

This section defines the FCLM profile data types and the FCLM extension to the
common OpenC2 ``Feature`` enumeration. References to these types elsewhere in
this profile point to the definitions in this section.

.. _fclm-type-features:

4.1 Features
------------

``Features`` is the common OpenC2 target data type used with the ``query``
Action. It is an array of requested :ref:`Feature <fclm-type-feature>` values.
FCLM retains the common container semantics and extends the permitted feature
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

.. _fclm-type-feature:

4.2 Feature
-----------

FCLM extends the common ``Feature`` enumeration so a Producer can discover
log-collection capabilities through ``query features``.

The profile extends the common OpenC2 type in
``otupy.profiles.fclm.targets.features``.

.. rubric:: Type: :py:class:`~otupy.profiles.fclm.targets.features.Feature` (Enumerated)

.. list-table:: Table 4.2-1. Feature Values Unique to FCLM
   :header-rows: 1
   :widths: 10 25 65

   * - ID
     - Name
     - Description
   * - 11
     - ``export_fields``
     - Log fields that can be included in exported records.
   * - 12
     - ``exports_config``
     - Exporter configuration values supported by the actuator, such as output
       destination or format.
   * - 13
     - ``imports_config``
     - Input-collection configuration values supported by the actuator.
   * - 14
     - ``import_controls``
     - Tunable input-collection controls, such as scan frequency and backoff
       periods.

.. _fclm-type-log-monitor:

4.3 LogMonitor
--------------

``LogMonitor`` defines the single source from which a log-collection session
reads. It is the value of the FCLM ``monitor`` target used with the ``start``
Action.

.. rubric:: Type: :py:class:`~otupy.profiles.fclm.targets.monitor.LogMonitor` (Choice)

.. list-table:: Table 4.3-1. LogMonitor Data Type
   :header-rows: 1
   :widths: 10 25 25 10 30

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1
     - ``file``
     - File
     - 0..1
     - Path of a local file from which log records are collected.
   * - 2
     - ``URI``
     - URI
     - 0..1
     - URI from which log records are collected.
   * - 3
     - ``socket``
     - :ref:`Socket <fclm-type-socket>`
     - 0..1
     - Network socket from which log records are collected.

Exactly one choice in a ``LogMonitor`` MUST be present.

.. _fclm-type-monitor-id:

4.4 MonitorID
-------------

``MonitorID`` identifies an active or scheduled log-collection session. The
Consumer returns it after creating a session, and a Producer uses it in a later
``stop`` Command.

.. rubric:: Type: :py:class:`~otupy.profiles.fclm.targets.monitor_id.MonitorID` (String)

.. list-table:: Table 4.4-1. MonitorID Data Type
   :header-rows: 1
   :widths: 25 25 50

   * - Name
     - Type
     - Description
   * - ``monitor_id``
     - String
     - Unique string identifier assigned to a log-collection session.

.. _fclm-type-exporter:

4.5 Exporter
------------

``Exporter`` defines where the log-collection actuator sends or stores
collected records.

.. rubric:: Type: :py:class:`~otupy.profiles.fclm.data.exporter.Exporter` (Record)

.. list-table:: Table 4.5-1. Exporter Data Type
   :header-rows: 1
   :widths: 10 25 25 10 30

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1
     - ``storage``
     - File
     - 0..1
     - Local file destination for collected log records.
   * - 2
     - ``collectors``
     - ArrayOf(:ref:`Collector <fclm-type-collector>`)
     - 0..1
     - Downstream collectors to which log records are transmitted.

An ``Exporter`` MUST include at least one of ``storage`` or ``collectors``.

.. _fclm-type-collector:

4.6 Collector
-------------

``Collector`` defines a remote endpoint that receives exported log records.
Its ``host`` field supports host names, IPv4 addresses, and IPv6 addresses.

.. rubric:: Type: :py:class:`~otupy.profiles.fclm.data.collector.Collector` (Record)

.. list-table:: Table 4.6-1. Collector Data Type
   :header-rows: 1
   :widths: 10 25 25 10 30

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1
     - ``host``
     - Host
     - 1
     - Address or name of the collector host.
   * - 2
     - ``port``
     - Port
     - 0..1
     - Network port on which the collector receives log records.
   * - 3
     - ``format``
     - :ref:`FileFormat <fclm-type-file-format>`
     - 0..1
     - Encoding format used for exported records.

.. _fclm-type-file-format:

4.7 FileFormat
--------------

``FileFormat`` identifies the encoding used for exported log records.

.. rubric:: Type: :py:class:`~otupy.profiles.fclm.data.file_format.FileFormat` (Enumerated)

.. list-table:: Table 4.7-1. FileFormat Data Type
   :header-rows: 1
   :widths: 15 25 60

   * - ID
     - Name
     - Description
   * - 1
     - ``text``
     - Plain-text log output.
   * - 2
     - ``json``
     - JSON-encoded structured log output.
   * - 3
     - ``yaml``
     - YAML-formatted log output.
   * - 4
     - ``csv``
     - Comma-separated-values log output.
   * - 5
     - ``xml``
     - XML-encoded log output.

.. _fclm-type-import-options:

4.8 ImportOptions
-----------------

``ImportOptions`` defines optional controls for log ingestion. These controls
determine how frequently sources are scanned and how inactive sources are
handled.

.. rubric:: Type: :py:class:`~otupy.profiles.fclm.data.import_options.ImportOptions` (Map)

.. list-table:: Table 4.8-1. ImportOptions Data Type
   :header-rows: 1
   :widths: 30 25 10 35

   * - Name
     - Type
     - #
     - Description
   * - ``scan_frequency``
     - Duration
     - 0..1
     - Interval between consecutive source scans.
   * - ``clean_inactive``
     - Duration
     - 0..1
     - Time after which an inactive source is removed from the registry.
   * - ``max_backoff``
     - Duration
     - 0..1
     - Maximum delay used for backoff when no data is available.
   * - ``close_inactive``
     - Duration
     - 0..1
     - Time after which an inactive log stream is closed.
   * - ``ignore_older``
     - Duration
     - 0..1
     - Files older than this duration are not harvested.

.. _fclm-type-ef:

4.9 EF
------

``EF`` is an export-field identifier. It specifies a field that the exporter
includes in a log record. The type is a string wrapper; the allowed values are
determined by the selected actuator and can be discovered through
``query features``.

.. rubric:: Type: :py:class:`~otupy.profiles.fclm.data.ef.EF` (String)

.. list-table:: Table 4.9-1. EF Data Type
   :header-rows: 1
   :widths: 25 25 50

   * - Name
     - Type
     - Description
   * - ``export_field``
     - String
     - Identifier of a field to export, for example a timestamp, source
       metadata, or the log payload.

.. _fclm-type-socket:

4.10 Socket
-----------

``Socket`` defines a network source for real-time log collection.

.. rubric:: Type: :py:class:`~otupy.profiles.fclm.data.socket.Socket` (Record)

.. list-table:: Table 4.10-1. Socket Data Type
   :header-rows: 1
   :widths: 10 25 25 10 30

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1
     - ``host``
     - IPv4Net
     - 1
     - IPv4 address or network from which the log stream is received.
   * - 2
     - ``port``
     - Port
     - 0..1
     - Network port used for log collection.
   * - 3
     - ``protocol``
     - L4Protocol
     - 0..1
     - Transport protocol used for collection, such as TCP or UDP.
