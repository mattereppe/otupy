4.3 CTXD Results
================

:py:class:`otupy.profiles.ctxd.results.Results` extends the common OpenC2
results with two fields:

.. list-table:: CTXD result fields
   :header-rows: 1

   * - Name
     - Type
     - Meaning
   * - ``services``
     - ``ArrayOf(Service)``
     - Services discovered by the Consumer.
   * - ``links``
     - ``ArrayOf(Link)``
     - Relationships associated with the discovered services.

The older ``services_names`` and ``link_names`` result fields are not present
in the current implementation.
