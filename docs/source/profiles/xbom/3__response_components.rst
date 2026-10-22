3. Response Components
======================

An OpenC2 Response conveys the outcome of an XBOM Query through a status code,
an optional human-readable status text, and optional results. XBOM uses the
common OpenC2 Response structure and extends the Results object with the
serialized BOM material and its representation metadata.

3.1 Response Structure
----------------------

.. rubric:: Type: OpenC2-Response (Map)

.. list-table:: Table 3.1-1. Common OpenC2 Response Fields Applicable to XBOM
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
     - Additional data returned by the Consumer or actuator.

3.2 Response Status Codes
-------------------------

XBOM uses the following status codes defined by the OpenC2 Language
Specification. XBOM defines no additional status codes.

.. rubric:: Type: Status-Code (Enumerated.ID)

.. list-table:: Table 3.2-1. Response Status Codes Applicable to XBOM
   :header-rows: 1
   :widths: 12 25 63

   * - Code
     - Status
     - Description
   * - 102
     - Processing
     - The Consumer accepted the Query but has not finished collecting or
       constructing the requested BOMs.
   * - 200
     - OK
     - The Query completed successfully.
   * - 400
     - Bad Request
     - The Consumer cannot process the Command because the target or arguments
       are malformed or invalid.
   * - 401
     - Unauthorized
     - The Command lacks valid authentication credentials, or the supplied
       credentials were refused.
   * - 403
     - Forbidden
     - The Consumer understood the Command but refuses to authorize access to
       the requested BOM information.
   * - 404
     - Not Found
     - No component or XBOM resource matching the requested identifier was
       found.
   * - 500
     - Internal Error
     - An unexpected Consumer or XBOM-backend condition prevented the Query
       from being completed.
   * - 501
     - Not Implemented
     - The Consumer does not support the requested XBOM capability, format, or
       encoding.
   * - 503
     - Service Unavailable
     - The Consumer or a dependency used to obtain BOM information is
       temporarily unavailable.

3.3 Response Results
--------------------

3.3.1 Common Results
^^^^^^^^^^^^^^^^^^^^

The following results are defined by the OpenC2 Language Specification and may
be returned by an XBOM Consumer, particularly in response to ``query features``.

.. rubric:: Type: Results (Map)

.. list-table:: Table 3.3.1-1. Common Results Applicable to XBOM
   :header-rows: 1
   :widths: 15 25 23 10 27

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

3.3.2 Results Unique to XBOM
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

XBOM extends the Results object with the following fields. The format and
encoding fields identify how each string in ``boms`` must be interpreted.

.. rubric:: Type: :py:class:`Results <otupy.profiles.xbom.results.Results>` (Map)

.. list-table:: Table 3.3.2-1. Results Unique to XBOM
   :header-rows: 1
   :widths: 25 25 10 40

   * - Name
     - Type
     - #
     - Description
   * - ``boms``
     - ArrayOf(String)
     - 0..*
     - Serialized BOM documents returned for the requested components.
   * - ``format``
     - :ref:`XbomFormat <xbom-type-xbom-format>`
     - 0..1
     - Data model used to represent the returned BOMs.
   * - ``encoding``
     - :ref:`XbomEncoding <xbom-type-xbom-encoding>`
     - 0..1
     - Serialization encoding used for the returned BOM strings.

