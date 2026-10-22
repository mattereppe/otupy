2. Command Components
=====================

This section identifies the OpenC2 Actions, Targets, Command Arguments, and
Actuator Specifiers that are meaningful for the Network Flow Monitor (NFM)
profile. NFM reuses the common OpenC2 language elements where applicable and
defines profile-specific Targets, Arguments, and Specifiers for managing flow
monitoring sessions.

2.1 Actions
-----------

2.1.1 Common Actions
^^^^^^^^^^^^^^^^^^^^

The following Actions are defined by the OpenC2 Language Specification and are
applicable to NFM. The permitted Action--Target pairs are defined in
:ref:`nfm-command-matrix`.

.. rubric:: Type: Action (Enumerated)

.. list-table:: Table 2.1.1-1. Common Actions Applicable to NFM
   :header-rows: 1
   :widths: 10 20 70

   * - ID
     - Name
     - Description
   * - 3
     - ``query``
     - Request information from the NFM actuator, including its capabilities or
       the status of an identified monitoring session.
   * - 9
     - ``start``
     - Initiate a flow-monitoring session using a ``monitor`` target.
   * - 10
     - ``stop``
     - Terminate an identified flow-monitoring session.

2.2 Targets
-----------

2.2.1 Common Targets
^^^^^^^^^^^^^^^^^^^^

.. rubric:: Type: Target (Choice)

.. list-table:: Table 2.2.1-1. Common Targets Applicable to NFM
   :header-rows: 1
   :widths: 10 25 20 45

   * - ID
     - Name
     - Type
     - Description
   * - 9
     - ``features``
     - :ref:`Features <nfm-type-features>`
     - A set of requested capability items, used with ``query`` to discover
       the NFM actuator's supported OpenC2 and NFM functions.

2.2.2 Targets Unique to NFM
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following Targets are defined by the NFM profile.

.. rubric:: Type: Target (Choice)

.. list-table:: Table 2.2.2-1. Targets Unique to NFM
   :header-rows: 1
   :widths: 10 30 20 40

   * - ID
     - Name
     - Type
     - Description
   * - 1024
     - ``monitor``
     - :ref:`FlowMonitor <nfm-type-flow-monitor>`
     - Defines optional IPv4 and IPv6 traffic filters for a monitoring session.
   * - 1025
     - ``monitor_id``
     - :ref:`MonitorID <nfm-type-monitor-id>`
     - Identifies an existing monitoring session for status retrieval or
       termination.

The ``monitor`` target carries any traffic filters. Interface selection and
Information Element selection are supplied as Command Arguments. A
``monitor_id`` is the string identifier returned when a monitoring session is
created.

2.3 Command Arguments
---------------------

Arguments provide additional precision about how or when a Command is to be
performed. Scheduling arguments retain the common OpenC2 semantics: at most two
of ``start_time``, ``stop_time``, and ``duration`` may be supplied in a Command.

2.3.1 Common Arguments
^^^^^^^^^^^^^^^^^^^^^^

.. rubric:: Type: Args (Map)

.. list-table:: Table 2.3.1-1. Common Command Arguments Applicable to NFM
   :header-rows: 1
   :widths: 8 25 20 10 37

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1
     - ``start_time``
     - Date-Time
     - 0..1
     - Specific date and time at which to initiate the Command.
   * - 2
     - ``stop_time``
     - Date-Time
     - 0..1
     - Specific date and time at which to terminate the Command.
   * - 3
     - ``duration``
     - Duration
     - 0..1
     - Length of time for which the Command is in effect.
   * - 4
     - ``response_requested``
     - Response-Type
     - 0..1
     - Requested response level: ``none``, ``ack``, ``status``, or
       ``complete``.

2.3.2 Arguments Unique to NFM
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following arguments refine a ``start monitor`` Command with monitor
selection and export-specific information.

.. rubric:: Type: Args (Map)

.. list-table:: Table 2.3.2-1. Command Arguments Unique to NFM
   :header-rows: 1
   :widths: 8 25 22 10 35

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1024
     - ``exporter``
     - :ref:`Exporter <nfm-type-exporter>`
     - 0..1
     - Specifies where or how collected flows are exported, for example to a
       collector or a local file.
   * - 1025
     - ``exporter_options``
     - :ref:`ExportOptions <nfm-type-export-options>`
     - 0..1
     - Specifies exporter tuning, such as output format, sampling,
       aggregation, or buffer settings.
   * - 1026
     - ``interfaces``
     - ArrayOf(:ref:`Interface <nfm-type-interface>`)
     - 0..1
     - Specifies the network interfaces from which traffic flows are
       collected.
   * - 1027
     - ``information_elements``
     - ArrayOf(:ref:`IE <nfm-type-ie>`)
     - 0..1
     - Specifies the flow fields to collect, such as source and destination
       addresses, bytes, and packets.

2.4 Actuator Specifiers
-----------------------

The NFM profile defines the following Actuator Specifier to select a particular
flow-monitoring actuator instance.

.. rubric:: Type: Specifiers (Map)

.. list-table:: Table 2.4-1. NFM Actuator Specifiers
   :header-rows: 1
   :widths: 8 25 20 10 37

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1
     - ``asset_id``
     - String
     - 0..1
     - Identifier of the NFM actuator instance that must execute the Command.

If ``asset_id`` is omitted, the Consumer applies its configured default NFM
actuator.

.. _nfm-command-matrix:

2.5 Command Matrix
------------------

An Action in the top row paired with a Target in the first column defines a
valid NFM Command.

.. list-table:: Table 2.5-1. NFM Command Matrix
   :header-rows: 1
   :widths: 35 20 20 20

   * - Target
     - ``query``
     - ``start``
     - ``stop``
   * - ``features``
     - valid
     -
     -
   * - ``monitor``
     -
     - valid
     -
   * - ``monitor_id``
     - valid
     -
     - valid

2.6 Command Arguments Matrix
----------------------------

An Argument in the first column is permitted for the Command shown in the
corresponding top-row column. For ``query features``, the only permitted
argument is ``response_requested`` with the value ``complete``.

.. list-table:: Table 2.6-1. NFM Command Arguments Matrix
   :header-rows: 1
   :widths: 24 19 20 19 19

   * - Argument
     - ``query features``
     - ``query monitor_id``
     - ``start monitor``
     - ``stop monitor_id``
   * - ``response_requested``
     - ``complete`` only
     - valid
     - valid
     - valid
   * - ``start_time``
     -
     -
     - valid
     -
   * - ``stop_time``
     -
     -
     - valid
     - valid
   * - ``duration``
     -
     -
     - valid
     - valid
   * - ``exporter``
     -
     -
     - valid
     -
   * - ``exporter_options``
     -
     -
     - valid
     -
   * - ``interfaces``
     -
     -
     - valid
     -
   * - ``information_elements``
     -
     -
     - valid
     -
