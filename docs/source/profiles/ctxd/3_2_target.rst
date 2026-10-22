3.2 Targets
===========

.. list-table:: Implemented CTXD command matrix
   :header-rows: 1

   * - Action
     - Target
     - Type
   * - ``query``
     - ``features``
     - Standard OpenC2 features target
   * - ``query``
     - ``x-ctxd:context``
     - :py:class:`~otupy.profiles.ctxd.targets.context.Context`

The profile-specific ``context`` target requests the context currently visible
to the selected CTXD actuator.
