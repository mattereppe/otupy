5.5 Computer
============

It describes an Operating and Application software installed on a machine.

Type: :py:class:`~otupy.profiles.ctxd.data.computer.Computer` (:py:class:`~otupy.types.base.record.Record`)

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
     - Description of the installation.
   * - 2
     - id
     - ``str``
     - 1
     - Identifier of the computer
   * - 3
     - hostname
     - :py:class:`~otupy.types.data.hostname.Hostname`
     - 1
     - Local or DNS name of the computer.
   * - 4
     - os
     - :py:class:`~otupy.profiles.ctxd.data.os.OS`
     - 1
     - Operating systems installed on the computer.
   * - 5
     - apps
     - :py:class:`~otupye.types.base.array_of.ArrayOf`\(:py:class:`~otupy.profiles.ctxd.data.application.Application`
     - 1
     - Daemons and other application software installed on the computer.

