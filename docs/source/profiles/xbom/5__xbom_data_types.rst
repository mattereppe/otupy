5. XBOM Data Types
==================

Two small enumerations are part of the current command/response contract:

``XbomFormat``
   ``ctxd`` (0) and ``cyclonedx`` (1).

``XbomEncoding``
   ``json`` (0), ``xml`` (1), and ``yaml`` (2).

The :mod:`otupy.profiles.xbom.data` package also contains classes used by XBOM
producers while constructing context and BOM information. Field-level
information for those classes is maintained in the generated API reference
rather than duplicated manually here.
