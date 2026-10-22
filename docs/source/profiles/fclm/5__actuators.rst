5. Actuator Implementations
===========================

An FCLM actuator is a Consumer-side implementation of the FCLM profile for a
particular log-collection agent. It translates the common OpenC2 FCLM commands
into that agent's configuration and process-control operations. A Producer uses
the same ``query``, ``start``, and ``stop`` commands regardless of the
implementation, but the available capabilities and accepted start options depend
on the selected backend.

The implementation documented in this profile provides the following
log-collection backend:

.. list-table:: Table 5.1-1. FCLM Actuator Implementations
   :header-rows: 1
   :widths: 25 40 35

   * - Monitoring agent
     - FCLM implementation
     - Documentation
   * - `Filebeat <https://www.elastic.co/docs/reference/beats/filebeat>`__
     - :py:class:`~otupy.actuators.fclm.fclm_actuator_filebeat.FCLMActuatorFilebeat`
     - `Filebeat reference <https://www.elastic.co/docs/reference/beats/filebeat>`__
