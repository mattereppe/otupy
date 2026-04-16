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
     - bom
     - :py:class:`~otupy.profiles.xbom.data.abstract_xbom.Xbom`
     - 0
     - The generated Bill of Materials.

Usage requirements:
~~~~~~~~~~~~~~~~~~~

-  The response "bom" can only be used when the target is "xbom".
-  The "bom" field contains a single :py:class:`~otupy.profiles.xbom.data.abstract_xbom.Xbom`
   object, whose concrete type depends on the format requested (defaults
   to :py:class:`~otupy.profiles.xbom.data.xbom.CyclonedxXbom`).

