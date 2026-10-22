3. Response Components
======================

An OpenC2 Response conveys the outcome of an RCLI Command through a status
code, an optional human-readable status text, and optional results. RCLI uses
the common OpenC2 Response structure and extends the Results object with
command, process, and file information.

3.1 Response Structure
----------------------

.. rubric:: Type: OpenC2-Response (Map)

.. list-table:: Table 3.1-1. Common OpenC2 Response Fields Applicable to RCLI
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

RCLI uses the following status codes defined by the OpenC2 Language
Specification. RCLI defines no additional status codes.

.. rubric:: Type: Status-Code (Enumerated.ID)

.. list-table:: Table 3.2-1. Response Status Codes Applicable to RCLI
   :header-rows: 1
   :widths: 12 25 63

   * - Code
     - Status
     - Description
   * - 102
     - Processing
     - The Consumer accepted the Command but has not completed it; for example,
       a process termination has been scheduled for a future time.
   * - 200
     - OK
     - The Command completed successfully.
   * - 400
     - Bad Request
     - The Consumer cannot process the Command because it is malformed or has
       invalid arguments, payload, or target fields.
   * - 401
     - Unauthorized
     - The Command lacks valid authentication credentials, or the supplied
       credentials were refused.
   * - 403
     - Forbidden
     - The Consumer understood the Command but refuses to authorize an
       operation on a tracked file or process.
   * - 404
     - Not Found
     - No resource matching the Command was found, for example a requested
       actuator destination, file, or tracked process.
   * - 500
     - Internal Error
     - An unexpected Consumer or host condition prevented the Command from
       being performed.
   * - 501
     - Not Implemented
     - The Consumer does not support the requested Action, Target, Argument,
       command-line program, or artifact MIME type.
   * - 503
     - Service Unavailable
     - The Consumer is temporarily unable to perform the Command because the
       RCLI service or its host environment is unavailable.

3.3 Response Results
--------------------

3.3.1 Common Results
^^^^^^^^^^^^^^^^^^^^

The following results are defined by the OpenC2 Language Specification and may
be returned by an RCLI actuator, in particular in response to ``query features``.

.. rubric:: Type: Results (Map)

.. list-table:: Table 3.3.1-1. Common Results Applicable to RCLI
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

3.3.2 Results Unique to RCLI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

RCLI extends the Results object with command allowlist, process-status, and
file-status fields.

.. rubric:: Type: :py:class:`~otupy.profiles.rcli.results.Results` (Map)

.. list-table:: Table 3.3.2-1. Results Unique to RCLI
   :header-rows: 1
   :widths: 8 25 25 10 32

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 2051
     - ``clicommands``
     - :ref:`Processes <rcli-type-processes>`
     - 0..1
     - Allowlisted command-line utilities and their permitted argument forms.
       Returned when ``clicommands`` is requested through ``query features``.
   * - 2052
     - ``process_status``
     - :ref:`Processes <rcli-type-processes>`
     - 0..1
     - Processes created or queried through RCLI, including their identifiers
       and current states when available.
   * - 2053
     - ``file_status``
     - :ref:`Files <rcli-type-files>`
     - 0..1
     - Files copied to or queried from the RCLI managed-storage area, including
       their paths, names, and available hashes.
