2. Command Components
=====================

This section identifies the OpenC2 Actions, Targets, Command Arguments, and
Actuator Specifiers that are meaningful for the File Collection Log Monitoring
(FCLM) profile. FCLM reuses the common OpenC2 language elements where
applicable and defines profile-specific Targets, Arguments, and Specifiers for
managing log-collection sessions.

2.1 Actions
-----------

2.1.1 Common Actions
^^^^^^^^^^^^^^^^^^^^

The following Actions are defined by the OpenC2 Language Specification and are
applicable to FCLM. The permitted Action--Target pairs are defined in
:ref:`fclm-command-matrix`.

.. rubric:: Type: Action (Enumerated)

.. list-table:: Table 2.1.1-1. Common Actions Applicable to FCLM
   :header-rows: 1
   :widths: 10 20 70

   * - ID
     - Name
     - Description
   * - 3
     - ``query``
     - Request the FCLM actuator's supported capabilities.
   * - 9
     - ``start``
     - Initiate a log-collection session using a ``monitor`` target.
   * - 10
     - ``stop``
     - Terminate an identified log-collection session.

2.2 Targets
-----------

2.2.1 Common Targets
^^^^^^^^^^^^^^^^^^^^

.. rubric:: Type: Target (Choice)

.. list-table:: Table 2.2.1-1. Common Targets Applicable to FCLM
   :header-rows: 1
   :widths: 10 25 20 45

   * - ID
     - Name
     - Type
     - Description
   * - 9
     - ``features``
     - :ref:`Features <fclm-type-features>`
     - A set of requested capability items, used with ``query`` to discover
       the FCLM actuator's supported OpenC2 and FCLM functions.

2.2.2 Targets Unique to FCLM
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following Targets are defined by the FCLM profile.

.. rubric:: Type: Target (Choice)

.. list-table:: Table 2.2.2-1. Targets Unique to FCLM
   :header-rows: 1
   :widths: 10 30 20 40

   * - ID
     - Name
     - Type
     - Description
   * - 1024
     - ``monitor``
     - :ref:`LogMonitor <fclm-type-log-monitor>`
     - Defines one log source: a file, URI, or network socket.
   * - 1025
     - ``monitor_id``
     - :ref:`MonitorID <fclm-type-monitor-id>`
     - Identifies an existing log-collection session for termination.

A ``monitor`` target contains exactly one source choice. A ``monitor_id`` is
the string identifier returned when a collection session is created.

2.3 Command Arguments
---------------------

Arguments provide additional precision about how or when a Command is to be
performed. Scheduling arguments retain the common OpenC2 semantics: at most two
of ``start_time``, ``stop_time``, and ``duration`` may be supplied in a Command.

2.3.1 Common Arguments
^^^^^^^^^^^^^^^^^^^^^^

.. rubric:: Type: Args (Map)

.. list-table:: Table 2.3.1-1. Common Command Arguments Applicable to FCLM
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

2.3.2 Arguments Unique to FCLM
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following arguments refine a ``start monitor`` Command with log-export and
input-collection configuration.

.. rubric:: Type: Args (Map)

.. list-table:: Table 2.3.2-1. Command Arguments Unique to FCLM
   :header-rows: 1
   :widths: 8 25 22 10 35

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1024
     - ``exporter``
     - :ref:`Exporter <fclm-type-exporter>`
     - 0..1
     - Specifies where collected logs are stored or forwarded.
   * - 1025
     - ``export_fields``
     - ArrayOf(:ref:`EF <fclm-type-ef>`)
     - 0..1
     - Specifies which fields are included in exported log records.
   * - 1026
     - ``import_controls``
     - :ref:`ImportOptions <fclm-type-import-options>`
     - 0..1
     - Specifies input-collection controls such as scan frequency and backoff
       periods.

2.4 Actuator Specifiers
-----------------------

The FCLM profile defines the following Actuator Specifier. It is an opaque
identifier that allows the OpenC2 Consumer to route a Command to the intended
FCLM actuator instance.

.. rubric:: Type: Specifiers (Map)

.. list-table:: Table 2.4-1. FCLM Actuator Specifiers
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
     - Identifier of the FCLM actuator instance that must execute the Command.

.. _fclm-command-matrix:

2.5 Command Matrix
------------------

An Action in the top row paired with a Target in the first column defines a
valid FCLM Command.

.. list-table:: Table 2.5-1. FCLM Command Matrix
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
     -
     -
     - valid

2.6 Command Arguments Matrix
----------------------------

An Argument in the first column is permitted for the Command shown in the
corresponding top-row column.

.. list-table:: Table 2.6-1. FCLM Command Arguments Matrix
   :header-rows: 1
   :widths: 24 25 25 25

   * - Argument
     - ``query features``
     - ``start monitor``
     - ``stop monitor_id``
   * - ``response_requested``
     - valid
     - valid
     - valid
   * - ``start_time``
     -
     - valid
     -
   * - ``stop_time``
     -
     - valid
     - valid
   * - ``duration``
     -
     - valid
     - valid
   * - ``exporter``
     -
     - valid
     -
   * - ``export_fields``
     -
     - valid
     -
   * - ``import_controls``
     -
     - valid
     -
