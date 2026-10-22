3.2 Targets
===========

.. list-table:: Implemented XBOM command matrix
   :header-rows: 1

   * - Action
     - Target
     - Type
   * - ``query``
     - ``features``
     - Standard OpenC2 features target
   * - ``query``
     - ``x-xbom:boms``
     - :py:class:`~otupy.profiles.xbom.targets.xbom_ctx.XbomTarget`

The current target name is ``boms``. Documentation and examples that use the
older ``xbom`` target or ``XbomCtx`` class refer to an earlier schema.
