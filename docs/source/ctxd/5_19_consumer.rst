5.19 Consumer
=============

The Consumer provides all the networking parameters to connect to an
OpenC2 Consumer. Despite of the name, it indeed points to an actuator.

Type: :py:class:`~otupy.profiles.ctxd.data.consumer.Consumer` (:py:class:`~otupy.types.base.record.Record`)


.. list-table::
   :widths: 3 5 5 5 45
   :header-rows: 1

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1
     - host
     - ``str``
     - 1
     - Hostname or IP address of the server
   * - 2
     - port
     - ``int``
     - 1
     - Port used to connect to the actuator
   * - 3
     - protocol
     - :py:class:`~otupy.types.data.l4_protocol.L4Protocol`
     - 1
     - Protocol used to connect to the actuator (this will be probably removed)
   * - 4
     - endpoint
     - ``str``
     - 1
     - Path to the endpoint (e.g., /.wellknown/openc2)
   * - 5
     - transfer
     - ``str``
     - 1
     - Transfer protocol used to connect to the actuator
   * - 6
     - encoding
     - ``str``
     - 1
     - Encoding format used to connect to the actuator
   * - 7
     - profile
     - ``str``
     - 1
     - Profile name available for this actuator
   * - 8
     - actuator
     - ``dict``
     - 1
     - Actuator specifiers (depending on the specific profile served)

		
