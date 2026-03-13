3.3 Context
===========

Type: Context (Record)

.. list-table::
   :widths: 3 4 4 3 40
   :header-rows: 1

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1
     - services
     - :py:class:`~otupy.types.base.array_of.ArrayOf`\(:py:class:`~otupy.profiles.ctxd.data.name.Name`)
     - 0
     - List the service names that the command refers to. This will be likely removed with SId in the future.
   * - 2
     - links
     - :py:class:`~otupy.types.base.array_of.ArrayOf`\(:py:class:`~otupy.profiles.ctxd.data.name.Name`)
     - 0
     - List the link names that the command refers to. This does not work, since Links do not have a name.
		 In future releases, this will be likely removed.

The Target Context is used when the Producer wants to know the
information of all active services and links of the Consumer. The
Producer can specify the names of the services and links it is
interested in.

TODO: :py:class:`~otupy.profiles.ctxd.data.name.Name`s will be replaced with 
						:py:class:`~otupy.profiles.ctxd.data.service.SId`

Usage requirements
------------------

-  Producer may send a “query” Command with no fields to the Consumer,
   which could return a heartbeat to this command.
-  A Producer may send a “query” Command containing an empty list of
   services. The Consumer should return all the services.
-  A Producer may send a “query” Command containing an empty list of
   links. The Consumer should return all the links.
-  A Producer may send a “query” Command containing an empty list of
   services and links. The Consumer should return all the services and
   links.

