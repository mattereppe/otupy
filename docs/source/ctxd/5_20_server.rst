5.20 Server
===========

It specifies the hostname or the IPv4 address of a server.

Type: :py:class:`~otupy.profiles.ctxd.data.server.Server` (:py:class:`~otupy.types.base.choice.Choice`)

.. list-table::
   :widths: 3 5 5 5 45
   :header-rows: 1

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1
     - hostname
     - :py:class:`~otupy.types.data.hostname.Hostname`
     - 1
     - Hostname of the server
   * - 2
     - ipv4-addr
     - :py:class:`~otupy.types.data.ipv4_addr.IPv4Addr`
     - 1
     - 32-bit IPv4 address as defined in RFC0791
