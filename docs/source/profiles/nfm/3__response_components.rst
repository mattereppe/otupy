3. Response Components
======================

An OpenC2 Response conveys the outcome of an NFM Command through a status code,
an optional human-readable status text, and optional results. NFM uses the
common OpenC2 Response structure and extends the Results object with
flow-monitoring information.

3.1 Response Structure
----------------------

.. rubric:: Type: OpenC2-Response (Map)

.. list-table:: Table 3.1-1. Common OpenC2 Response Fields Applicable to NFM
   :header-rows: 1
   :widths: 20 25 15 40

   * - Name
     - Type
     - #
     - Description
   * - ``status``
     - Status-Code
     - 1
     - Status code indicating the outcome of the Command.
   * - ``status_text``
     - String
     - 0..1
     - Optional human-readable description of the response status.
   * - ``results``
     - Results
     - 0..1
     - Additional data returned by the actuator in response to the Command.

3.2 Response Status Codes
-------------------------

NFM uses the following status codes defined by the OpenC2 Language
Specification. NFM defines no additional status codes.

.. rubric:: Type: Status-Code (Enumerated.ID)

.. list-table:: Table 3.2-1. Response Status Codes Applicable to NFM
   :header-rows: 1
   :widths: 12 25 63

   * - Code
     - Status
     - Description
   * - 102
     - Processing
     - The Consumer accepted the Command but has not completed it; for example,
       a monitoring session has been scheduled for a future time.
   * - 200
     - OK
     - The Command completed successfully.
   * - 400
     - Bad Request
     - The Consumer cannot process the Command because it is malformed or has
       invalid arguments.
   * - 401
     - Unauthorized
     - The Command lacks valid authentication credentials, or the supplied
       credentials were refused.
   * - 403
     - Forbidden
     - The Consumer understood the Command but refuses to authorize it.
   * - 404
     - Not Found
     - No resource matching the Command was found, for example the requested
       ``monitor_id`` does not identify an active or scheduled monitor.
   * - 500
     - Internal Error
     - An unexpected Consumer or monitoring-backend condition prevented the
       Command from being performed.
   * - 501
     - Not Implemented
     - The Consumer does not support the requested Command functionality.
   * - 503
     - Service Unavailable
     - The Consumer is temporarily unable to perform the Command, for example
       because its monitoring backend is unavailable or overloaded.

3.3 Response Results
--------------------

3.3.1 Common Results
^^^^^^^^^^^^^^^^^^^^

The following results are defined by the OpenC2 Language Specification and may
be returned by an NFM actuator, in particular in response to ``query features``.

.. rubric:: Type: Results (Map)

.. list-table:: Table 3.3.1-1. Common Results Applicable to NFM
   :header-rows: 1
   :widths: 8 25 23 10 34

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1
     - ``versions``
     - Version
     - 0..*
     - OpenC2 language versions supported by the actuator.
   * - 2
     - ``profiles``
     - ArrayOf(Nsid)
     - 0..1
     - OpenC2 actuator profiles supported by the actuator.
   * - 3
     - ``pairs``
     - Action-Targets
     - 0..1
     - Supported Actions and their applicable Targets.
   * - 4
     - ``rate_limit``
     - Number
     - 0..1
     - Maximum number of Commands per minute supported by design or policy.

3.3.2 Results Unique to NFM
^^^^^^^^^^^^^^^^^^^^^^^^^^^

NFM extends the Results object with the following fields. They may report
discovered NFM capabilities, the configuration of a monitor, or the identifier
of a newly created monitoring session.

.. rubric:: Type: Results (Map)

.. list-table:: Table 3.3.2-1. Results Unique to NFM
   :header-rows: 1
   :widths: 8 25 25 10 32

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 3051
     - ``interfaces``
     - ArrayOf(:ref:`Interface <nfm-type-interface>`)
     - 0..1
     - Network interfaces available for monitoring, or associated with a
       returned monitor configuration.
   * - 3052
     - ``information_elements``
     - ArrayOf(:ref:`IE <nfm-type-ie>`)
     - 0..1
     - Flow fields supported or selected for monitoring and export.
   * - 3053
     - ``exports``
     - ArrayOf(String)
     - 0..1
     - Exporter types supported by the actuator, such as file or collector.
   * - 3054
     - ``export_options``
     - ArrayOf(String)
     - 0..1
     - Exporter parameters supported by the actuator, such as sampling,
       aggregation, or output format.
   * - 3055
     - ``flow_format``
     - ArrayOf(String)
     - 0..1
     - Flow output formats supported by the actuator, such as JSON, NetFlow,
       IPFIX, or CSV.
   * - 3056
     - ``monitor_id``
     - :ref:`MonitorID <nfm-type-monitor-id>`
     - 0..1
     - Identifier assigned to a monitoring session and returned after a
       successful ``start monitor`` Command.
   * - 3057
     - ``filters``
     - ArrayOf(String)
     - 0..1
     - IPv4, IPv6, or protocol-level filters supported by the actuator or
       active for a returned monitor configuration.
