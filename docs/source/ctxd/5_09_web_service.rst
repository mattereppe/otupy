5.9 Web Service
================

It describes a generic web service.

Type: :py:class:`~otupy.profiles.ctxd.data.web_service.WebService` (:py:class:`~otupy.types.base.record.Record`)

.. list-table::
   :widths: 3 4 4 3 40
   :header-rows: 1

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1
     - description
     - ``str``
     - 1
     - Generic description of the web service.
   * - 2
     - server
     - :py:class:`~otupy.profiles.ctxd.data.server.Server`
     - 1
     - Hostname or IP address of the server.
   * - 3
     - port
     - ``int``
     - 1
     - The port used to connect to the web service.
   * - 4
     - endpoint
     - ``str``
     - 1
     - The endpoint used to connect to the web service.
   * - 5
     - owner
     - ``str``
     - 1
     - Owner of the web service.

Sample Web Service object represented in JSON Format:

.. code:: json

   {
     "description": "web_service",
     "server": "192.168.0.1",
     "port": 443,
     "endpoint": "maps/api/geocode/json",
     "owner": "Google"
   }

