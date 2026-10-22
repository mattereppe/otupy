5. Actuator Implementations
===========================

An RCLI actuator is a Consumer-side implementation of the RCLI profile for a
particular host. It translates RCLI Commands into controlled command-line and
file-management operations on that host. The optional ``asset_id`` Specifier is
only a routing identifier for the Consumer; it does not select a command-line
backend. A Producer uses ``query features`` to learn the capabilities and
allowlisted commands of the addressed destination.

The current implementation supports the following host platform:

.. list-table:: Table 5.1-1. RCLI Actuator Implementations
   :header-rows: 1
   :widths: 25 40 35

   * - Supported host
     - RCLI implementation
     - Documentation
   * - `Linux hosts <https://man7.org/linux/man-pages/>`__
     - :py:class:`~otupy.actuators.rcli.rcli_actuator.RCLIActuator`
     - `Linux manual pages <https://man7.org/linux/man-pages/>`__
