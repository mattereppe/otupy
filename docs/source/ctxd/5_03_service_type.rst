5.3 Service-Type
================

It represents the type of service, where each service type is further
defined with additional information that provides a more detailed
description of the service’s characteristics.

Type: :py:class:`~otupy.profiles.ctxd.data.service_type.ServiceType` (:py:class:`~otupy.types.base.choice.Choice`)

.. list-table::
   :widths: 3 4 4 3 40
   :header-rows: 1

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1
     - application
     - :py:class:`~otupy.profiles.ctxd.data.application.Application`
     - 1
     - Software application.
   * - 2
     - computer
     - :py:class:`~otupy.profiles.ctxd.data.computer.Computer`
     - 1
     - Operating and application software.
   * - 3
     - vm
     - :py:class:`~otupy.profiles.ctxd.data.vm.VM`
     - 1
     - Virtual Machine.
   * - 4
     - pod
     - :py:class:`~otupy.profiles.ctxd.data.pod.Pod`
     - 1
     - Kubernetes pod.
   * - 5
     - container
     - :py:class:`~otupy.profiles.ctxd.data.container.Container`
     - 1
     - Container.
   * - 6
     - web_service
     - :py:class:`~otupy.profiles.ctxd.data.web_service.WebService`
     - 1
     - Web service.
   * - 7
     - cloud
     - :py:class:`~otupy.profiles.ctxd.data.cloud.Cloud`
     - 1
     - Cloud.
   * - 8
     - network
     - :py:class:`~otupy.profiles.ctxd.data.network.Network`
     - 1
     - Connectivity service.
   * - 9
     - iot
     - :py:class:`~otupy.profiles.ctxd.data.iot.IOT`
     - 1
     - IOT device.

