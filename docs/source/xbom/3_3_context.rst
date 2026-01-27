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
     - boms
     - :py:class:`~otupy.types.base.array_of.ArrayOf`\(:py:class:`~otupy.profiles.xbom.data.name.Name`)
     - 0
     - List the bom names that the command refers to.

It describes the service environment, its connections and security capabilities.
Notice that, since the boms usually don't have names, the "boms" field is used to specify the
names of the components or services that the Producer wants to query.

Usage requirements
------------------

-  Producer may send a “query” Command with no fields to the Consumer,
   which could return a heartbeat to this command.
-  A Producer may send a “query” Command containing an empty list of
   boms. The Consumer should return all the boms.

