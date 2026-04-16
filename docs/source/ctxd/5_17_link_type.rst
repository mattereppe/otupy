5.17 Link-Type
==============

This data type describes the type of the link between the peer and the
service under analysis.

Type: :py:class:`~otupy.profiles.ctxd.data.link_type.LinkType` (:py:class:`~otupy.types.base.enumerated.Enumerated`)

.. list-table::
   :widths: 3 4 40
   :header-rows: 1

   * - ID
     - Name
     - Description
   * - 1
     - api
     - The connection is an API.
   * - 2
     - hosting
     - The service is hosted in an infrastructure.
   * - 3
     - packet_flow
     - Network flow.
   * - 4
     - control
     - The service controls another resource.
   * - 5
     - protect
     - The service protects another resource.

The types of API, Hosting, Packet-Flow, Control, and Protect are not
defined in this document.

