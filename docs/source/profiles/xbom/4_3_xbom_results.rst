4.3 XBOM Results
================

:py:class:`otupy.profiles.xbom.results.Results` defines three fields:

.. list-table:: XBOM result fields
   :header-rows: 1

   * - Name
     - Type
     - Meaning
   * - ``boms``
     - ``ArrayOf(str)``
     - Serialized BOM documents returned by the Consumer.
   * - ``format``
     - :py:class:`~otupy.profiles.xbom.data.xbom_format.XbomFormat`
     - Data model used by the returned BOM strings.
   * - ``encoding``
     - :py:class:`~otupy.profiles.xbom.data.xbom_encoding.XbomEncoding`
     - Serialization used by the returned BOM strings.

The current result field is plural ``boms``; the earlier singular ``bom``
object is no longer the implemented response schema.
