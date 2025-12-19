5.1 Name
========

The Name type is used to indicate the name of any object. When the
Command Argument is “name_only”, an array of Name is returned to the
Producer.

Type: :py:class:`~otupy.profiles.ctxd.data.name.Name` (:py:class:`~otupy.types.base.choice.Choice`)

.. list-table::
   :widths: 3 4 4 3 40
   :header-rows: 1

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1
     - uri
     - :py:class:`~otupy.types.data.uri.URI`
     - 1
     - Uniform Resource Identifier of the service.
   * - 2
     - reverse_dns
     - :py:class:`~otupy.types.data.hostname.Hostname`
     - 1
     - Reverse domain name notation.
   * - 3
     - uuid
     - ``UUID``
     - 1
     - Universally unique identifier of the service.
   * - 4
     - local
     - ``str``
     - 1
     - Name without guarantee of uniqueness.

