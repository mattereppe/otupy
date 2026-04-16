3.1 Actions
===========

Action is a mandatory field in Command message and no Actuator Profile
can add a new Action that is not present in the specifications.

Type: :py:class:`~otupy.core.actions.Actions` (:py:class:`~otupy.types.base.enumerated.Enumerated`)

.. list-table::
   :widths: 3 10 30
   :header-rows: 1

   * - ID
     - Name
     - Description
   * - 3
     - query
     - Initiate a request for information.

