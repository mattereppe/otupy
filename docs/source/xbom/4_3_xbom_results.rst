4.3 XBOM Results
================

These results are not included in the Language Specification and are
introduced specifically for the XBOM Actuator Profile.

Type: :py:class:`~otupy.core.results.Results` (:py:class:`~otupy.types.base.map.Map`)

.. list-table::
   :widths: 3 4 4 3 40
   :header-rows: 1

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1024
     - boms
     - :py:class:`~otupy.types.base.array_of.ArrayOf`\(:py:class:`~otupy.profiles.xbom.data.xbom.Xbom`)
     - 0
     - List all the boms.
   * - 1025
     - bom_names
     - :py:class:`~otupy.types.base.array_of.ArrayOf`\(:py:class:`~otupy.profiles.xbom.data.name.Name`)
     - 0
     - List the names of all boms.

Usage requirements:
~~~~~~~~~~~~~~~~~~~

-  The response "boms" can only be used when the target is "context".
-  The response "bom_names" can only be used when the target is "context".
-  bom_names and boms are mutually exclusive. The choice is based on the value of the "name_only"
   argument in the query.
