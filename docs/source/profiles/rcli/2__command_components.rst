2. Command Components
=====================

This section identifies the OpenC2 Actions, Targets, Command Arguments, and
Actuator Specifiers that are meaningful for the Remote Command-Line Interface
(RCLI) profile. RCLI reuses the common OpenC2 Actions and common Targets where
applicable, and defines profile-specific Targets and an Argument for controlled
file and process management.

2.1 Actions
-----------

2.1.1 Common Actions
^^^^^^^^^^^^^^^^^^^^

The following Actions are defined by the OpenC2 Language Specification and are
applicable to RCLI. The permitted Action--Target pairs are defined in
:ref:`rcli-command-matrix`.

.. rubric:: Type: Action (Enumerated)

.. list-table:: Table 2.1.1-1. Common Actions Applicable to RCLI
   :header-rows: 1
   :widths: 10 20 70

   * - ID
     - Name
     - Description
   * - 3
     - ``query``
     - Request RCLI capabilities, the status of tracked processes, or the
       metadata of stored files.
   * - 9
     - ``start``
     - Start one or more allowlisted command-line processes.
   * - 10
     - ``stop``
     - Terminate selected tracked processes or all tracked processes when the
       target is empty.
   * - 20
     - ``delete``
     - Remove one or more files managed by the RCLI actuator.
   * - 28
     - ``copy``
     - Transfer an artifact to the RCLI actuator's managed storage.

2.2 Targets
-----------

2.2.1 Common Targets
^^^^^^^^^^^^^^^^^^^^

.. rubric:: Type: Target (Choice)

.. list-table:: Table 2.2.1-1. Common Targets Applicable to RCLI
   :header-rows: 1
   :widths: 10 25 20 45

   * - ID
     - Name
     - Type
     - Description
   * - 1
     - ``artifact``
     - Artifact
     - A file-like payload or URL reference, used with ``copy`` to transfer an
       artifact to the RCLI actuator.
   * - 9
     - ``features``
     - :ref:`Features <rcli-type-features>`
     - Requested capability items, used with ``query`` to discover common
       OpenC2 capabilities and RCLI-specific functions.

2.2.2 Targets Unique to RCLI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following Targets are defined by the RCLI profile. The RCLI namespace is
used in serialized OpenC2 messages; within this profile, the target names are
shown without the ``x-rcli`` prefix.

.. rubric:: Type: Target (Choice)

.. list-table:: Table 2.2.2-1. Targets Unique to RCLI
   :header-rows: 1
   :widths: 10 25 20 45

   * - ID
     - Name
     - Type
     - Description
   * - 1024
     - ``processes``
     - :ref:`Processes <rcli-type-processes>`
     - Processes to start, stop, or query. The target can be empty when
       querying or stopping all processes tracked by the actuator.
   * - 1025
     - ``files``
     - :ref:`Files <rcli-type-files>`
     - Stored files to query or delete. An empty target queries all tracked
       files; a delete request identifies one or more files.

Each ``processes`` and ``files`` target contains at most ten entries. A
``start processes`` Command requires at least one process. The current Linux
implementation accepts only ``pid`` or ``name`` fields when querying or
stopping a specific process.

2.3 Command Arguments
---------------------

Arguments provide additional information about how or when a Command is to be
performed. Scheduling arguments retain the common OpenC2 semantics: at most two
of ``start_time``, ``stop_time``, and ``duration`` may be supplied in a Command.

2.3.1 Common Arguments
^^^^^^^^^^^^^^^^^^^^^^

.. rubric:: Type: Args (Map)

.. list-table:: Table 2.3.1-1. Common Command Arguments Applicable to RCLI
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

2.3.2 Arguments Unique to RCLI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The RCLI profile defines an argument that selects the location and file name
used when an artifact is copied. The current Linux implementation resolves that
location beneath its configured managed-storage directory.

.. rubric:: Type: :py:class:`~otupy.profiles.rcli.args.Args` (Map)

.. list-table:: Table 2.3.2-1. Command Arguments Unique to RCLI
   :header-rows: 1
   :widths: 8 25 22 10 35

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1024
     - ``storage``
     - File
     - 0..1
     - Optional path and name for an artifact copied to the managed storage
       area. If omitted, the actuator chooses a name and location.

2.4 Actuator Specifiers
-----------------------

RCLI uses the following optional Actuator Specifiers to let a Consumer route a
Command to the intended RCLI destination. These values are opaque routing
identifiers; they do not select a command-line backend or modify the
capabilities of the implementation. A Producer discovers the capabilities of
the addressed actuator through ``query features``.

.. rubric:: Type: :py:class:`~otupy.profiles.rcli.actuator.Specifiers` (Map)

.. list-table:: Table 2.4-1. RCLI Actuator Specifiers
   :header-rows: 1
   :widths: 8 25 20 10 37

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1
     - ``hostname``
     - String
     - 0..1
     - Host name used by the Consumer to route a Command to an RCLI
       destination.
   * - 2
     - ``named_group``
     - String
     - 0..1
     - Consumer-defined group label for a set of RCLI destinations.
   * - 3
     - ``asset_id``
     - String
     - 0..1
     - Opaque identifier of the intended RCLI Consumer destination.
   * - 4
     - ``asset_tuple``
     - ArrayOf(String)
     - 0..1
     - Ordered set of opaque identifiers used by Consumer-specific routing.

.. _rcli-command-matrix:

2.5 Command Matrix
------------------

An Action in the top row paired with a Target in the first column defines a
valid RCLI Command.

.. list-table:: Table 2.5-1. RCLI Command Matrix
   :header-rows: 1
   :widths: 30 14 14 14 14 14

   * - Target
     - ``query``
     - ``start``
     - ``stop``
     - ``copy``
     - ``delete``
   * - ``features``
     - valid
     -
     -
     -
     -
   * - ``artifact``
     -
     -
     -
     - valid
     -
   * - ``processes``
     - valid
     - valid
     - valid
     -
     -
   * - ``files``
     - valid
     -
     -
     -
     - valid

2.6 Command Arguments Matrix
----------------------------

An Argument in the first column is permitted for the Command shown in the
corresponding top-row column.

.. list-table:: Table 2.6-1. RCLI Command Arguments Matrix
   :header-rows: 1
   :widths: 18 12 12 12 12 12 12 12

   * - Argument
     - ``query features``
     - ``query processes``
     - ``query files``
     - ``copy artifact``
     - ``start processes``
     - ``stop processes``
     - ``delete files``
   * - ``response_requested``
     - valid
     - valid
     - valid
     - valid
     - valid
     - valid
     - valid
   * - ``start_time``
     -
     -
     -
     -
     - valid
     -
     -
   * - ``stop_time``
     -
     -
     -
     -
     - valid
     - valid
     -
   * - ``duration``
     -
     -
     -
     -
     - valid
     - valid
     -
   * - ``storage``
     -
     -
     -
     - valid
     -
     -
     -

For the current Linux implementation, a supplied ``response_requested`` value
must be ``complete``. The ``query features`` Command is also constrained by the
OpenC2 Language Specification to use no other argument.
