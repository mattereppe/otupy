3.3 Xbom Target
===============

Type: :py:class:`~otupy.profiles.xbom.targets.xbom_ctx.XbomCtx` (:py:class:`~otupy.types.base.map.Map`)

.. list-table::
   :widths: 3 4 4 3 40
   :header-rows: 1

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1
     - format
     - :py:class:`~otupy.profiles.xbom.data.xbom_format.XbomFormat`
     - 0
     - Specifies the format of the XBOM (e.g., CycloneDX). Defaults to CycloneDX if not specified.

The ``XbomCtx`` target defines the arguments used to identify or format
a Software Bill of Materials. It allows the Producer to specify the
desired BOM format when querying the Consumer.

Usage requirements
------------------

-  A Producer may send a "query xbom" Command with no fields to the
   Consumer, which will return a BOM in the default format (CycloneDX).
-  A Producer may send a "query xbom" Command specifying a ``format``
   to request a specific BOM format.

