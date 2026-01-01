5.11 Network
=============

It describes a generic network service. The Network-Type is described in
the following sections.

Type: :py:class:`~otupy.profiles.ctxd.data.network.Network` (:py:class:`~otupy.types.base.record.Record`)

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
     - Generic description of the network.
   * - 2
     - name
     - ``str``
     - 1
     - Name of the network provider.
   * - 3
     - type
     - :py:class:`~otupy.profiles.ctxd.data.network_type.NetworkType`
     - 1
     - Type of the network service.

Sample Network object represented in JSON Format:

.. code:: json

   {
     "description": "network",
     "name": "The Things Network",
     "type": "LoRaWAN"
   }

