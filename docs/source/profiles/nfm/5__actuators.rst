5. Actuator Implementations
===========================

An NFM actuator is a Consumer-side implementation of the NFM profile for a
particular network-monitoring agent. It translates the common OpenC2 NFM
commands into that agent's configuration and process-control operations. A
Producer uses the same ``query``, ``start``, and ``stop`` commands regardless
of the implementation.

The implementation documented in this profile provides the following
monitoring-agent backends:

.. list-table:: Table 5.1-1. NFM Actuator Implementations
   :header-rows: 1
   :widths: 25 40 35

   * - Monitoring agent
     - NFM implementation
     - Documentation
   * - `nProbe <https://www.ntop.org/guides/nprobe/>`__
     - :py:class:`~otupy.actuators.nfm.nfm_actuator_nprobe.NFMActuatorNProbe`
     - `nProbe User's Guide <https://www.ntop.org/guides/nprobe/>`__
   * - `fprobe <https://github.com/sb98052/fprobe>`__
     - :py:class:`~otupy.actuators.nfm.nfm_actuator_fprobe.NFMActuatorFProbe`
     - `fprobe documentation <https://github.com/sb98052/fprobe>`__
   * - `Packetbeat <https://www.elastic.co/docs/reference/beats/packetbeat>`__
     - :py:class:`~otupy.actuators.nfm.nfm_actuator_packetbeat.NFMActuatorPacketbeat`
     - `Packetbeat documentation <https://www.elastic.co/docs/reference/beats/packetbeat>`__
