3.4 Command Arguments
=====================

Type: Args (Map)

.. list-table::
   :widths: 3 4 4 3 40
   :header-rows: 1

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 4
     - response_requested
     - :py:class:`~otupy.types.data.response_type.ResponseType`
     - 0
     - The type of Response required for the Command: none, ack, status, complete.
   * - 1025
     - cached
     - ``bool``
     - 0
     - If TRUE, the Consumer may return cached data in the Response.

Command Arguments are optional. A new argument called "cached" has been
defined, which is not present in the Language Specification.

Usage requirements:
-------------------

-  The "response_requested": "complete" argument can be present in the
   "query features" Command. (Language specification 4.1)
-  The "query xbom" Command may include the "response_requested":
   "complete" Argument.
-  The "query xbom" Command may include the "cached" argument:

   -  If TRUE, the Consumer may return previously cached results to speed
      up the response.
   -  If FALSE (default), the Consumer updates its service information
      before returning the response.

