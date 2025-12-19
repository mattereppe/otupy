5.15 Link
=========

A Service can be connected to one or more Services, the module Link
describes the type of the connection, and the security features applied
on the link.

Type: :py:class:`~otupy.profiles.ctxd.data.link.Link` (:py:class:`~otupy.types.base.record.Record`)

.. list-table::
   :widths: 3 4 4 3 40
   :header-rows: 1

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1
     - name
     - :py:class:`~otupy.profiles.ctxd.data.name.Name`
     - 1
     - Id of the link.
   * - 2
     - desc
     - ``str``
     - 0
     - Generic description of the relationship.
   * - 3
     - versions
     - :py:class:`~otupy.types.base.array_of.ArrayOf`\(:py:class:`~otupy.types.data.version.Version`)
     - 0
     - Subset of service features used in this relationship (e.g., version of an API or network protocol).
   * - 4
     - link_type
     - :py:class:`~otupy.profiles.ctxd.data.link_type.LinkType`
     - 1
     - Type of the link.
   * - 5
     - peers
     - :py:class:`~otupy.types.base.array_of.ArrayOf`\(:py:class:`~otupy.profiles.ctxd.data.peer.Peer`)
     - 1
     - Services connected on the link.

