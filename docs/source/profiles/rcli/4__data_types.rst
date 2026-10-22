4. RCLI Data Types
==================

This section defines the RCLI profile data types and the RCLI extension to the
common OpenC2 ``Feature`` enumeration. References to these types elsewhere in
this profile point to the definitions in this section.

.. _rcli-type-features:

4.1 Features
------------

``Features`` is the common OpenC2 target data type used with the ``query``
Action. It is an array of requested :ref:`Feature <rcli-type-feature>` values.
RCLI retains the common container semantics and extends the permitted feature
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

.. _rcli-type-feature:

4.2 Feature
-----------

RCLI extends the common ``Feature`` enumeration so a Producer can discover the
allowlisted command-line utilities exposed by the addressed actuator.

.. rubric:: Type: :py:class:`~otupy.profiles.rcli.targets.features.Feature` (Enumerated)

.. list-table:: Table 4.2-1. Feature Values Unique to RCLI
   :header-rows: 1
   :widths: 10 25 65

   * - ID
     - Name
     - Description
   * - 15
     - ``clicommands``
     - Allowlisted command-line utilities and their permitted flags or path
       arguments. The actuator returns the values as ``clicommands`` results.

.. _rcli-type-process:

4.3 Process
-----------

``Process`` extends the common OpenC2 Process type with a ``state`` field.
It represents an RCLI process to be started, stopped, or queried, and it also
represents an entry returned in ``process_status`` or ``clicommands`` results.

.. rubric:: Type: :py:class:`~otupy.profiles.rcli.data.process.Process` (Map{1..*})

.. list-table:: Table 4.3-1. Process Data Type
   :header-rows: 1
   :widths: 8 22 25 10 35

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1
     - ``pid``
     - Integer{0..*}
     - 0..1
     - Operating-system process identifier.
   * - 2
     - ``name``
     - String
     - 0..1
     - Process name. For an RCLI start request, it identifies an allowlisted
       command-line utility.
   * - 3
     - ``cwd``
     - String
     - 0..1
     - Current working directory of the process.
   * - 4
     - ``executable``
     - File
     - 0..1
     - File object describing an executable to be run.
   * - 5
     - ``parent``
     - Process
     - 0..1
     - Process that spawned this process.
   * - 6
     - ``command_line``
     - String
     - 0..1
     - Full command-line invocation, including arguments. For an allowlisted
       named command, the arguments must comply with the advertised allowlist.
   * - 7
     - ``state``
     - :ref:`State <rcli-type-state>`
     - 0..1
     - Current runtime state reported by the RCLI actuator.

At least one field MUST be present. For a current-process query or stop request,
the Linux actuator accepts ``pid`` or ``name`` as the selector fields.

.. _rcli-type-processes:

4.4 Processes
-------------

``Processes`` is the RCLI target and result container for process entries. It
is used with the ``processes`` target.

.. rubric:: Type: :py:class:`~otupy.profiles.rcli.targets.processes.Processes` (ArrayOf(Process){0..10})

.. list-table:: Table 4.4-1. Processes Data Type
   :header-rows: 1
   :widths: 25 30 45

   * - Type Name
     - Type Definition
     - Description
   * - ``Processes``
     - ArrayOf(:ref:`Process <rcli-type-process>`){0..10}
     - Zero to ten process entries to manage or report.

.. _rcli-type-files:

4.5 Files
---------

``Files`` is the RCLI target and result container for files in the actuator's
managed-storage area. It is used with the ``files`` target.

.. rubric:: Type: :py:class:`~otupy.profiles.rcli.targets.files.Files` (ArrayOf(File){0..10})

.. list-table:: Table 4.5-1. Files Data Type
   :header-rows: 1
   :widths: 25 30 45

   * - Type Name
     - Type Definition
     - Description
   * - ``Files``
     - ArrayOf(File){0..10}
     - Zero to ten file entries to query, delete, or report. Each File uses the
       common OpenC2 ``name``, ``path``, and optional ``hashes`` fields.

.. _rcli-type-state:

4.6 State
---------

``State`` identifies the runtime state of a process. The Linux implementation
derives these values from the host process state reported by ``psutil``.

.. rubric:: Type: :py:class:`~otupy.profiles.rcli.data.state.State` (Enumerated)

.. list-table:: Table 4.6-1. State Data Type
   :header-rows: 1
   :widths: 10 25 65

   * - ID
     - Name
     - Description
   * - 1
     - ``running``
     - The process is actively executing instructions.
   * - 2
     - ``sleeping``
     - The process is waiting for an event to complete.
   * - 3
     - ``disk_sleep``
     - The process is blocked in uninterruptible disk I/O.
   * - 4
     - ``stopped``
     - The process has been stopped by a signal or user.
   * - 5
     - ``tracing_stop``
     - The process is being traced or debugged.
   * - 6
     - ``zombie``
     - The process has terminated but remains in the process table.
   * - 7
     - ``dead``
     - The process has terminated and is no longer active.
   * - 8
     - ``wake_kill``
     - The process is being awakened so that it can be killed.
   * - 9
     - ``waking``
     - The process is in the process of waking up.
   * - 10
     - ``parked``
     - The process is parked, for example an idle kernel thread.
   * - 11
     - ``idle``
     - The process is idle and waiting for work.
   * - 12
     - ``locked``
     - The process is blocked while waiting for a resource lock.
   * - 13
     - ``waiting``
     - The process is waiting for another event or resource.
   * - 14
     - ``suspended``
     - The process is suspended by the system or a user.
   * - 15
     - ``not_found``
     - The process does not exist or has already terminated.

.. _rcli-type-transfer:

4.7 Transfer
------------

``Transfer`` is an RCLI enumeration for identifying transport protocols. It is
defined by the RCLI Python profile for use by future extensions; no current RCLI
Command field uses this type.

.. rubric:: Type: :py:class:`~otupy.profiles.rcli.data.transfer.Transfer` (Enumerated)

.. list-table:: Table 4.7-1. Transfer Data Type
   :header-rows: 1
   :widths: 10 25 65

   * - ID
     - Name
     - Description
   * - 1
     - ``http``
     - Hypertext Transfer Protocol.
   * - 2
     - ``https``
     - Hypertext Transfer Protocol Secure.
   * - 3
     - ``mqtt``
     - Message Queuing Telemetry Transport.
