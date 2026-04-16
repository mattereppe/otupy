5.2 Service
============

Digital resources can implement one or more services, with each service
described by a Service type. This type is a key element of the data
model, as it provides the information the Producer is seeking about the
services.

Type: :py:class:`~otupy.profiles.ctxd.data.service.Service` (:py:class:`~otupy.types.base.record.Record`)

.. list-table::
   :widths: 3 4 4 3 40
   :header-rows: 1

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1
     - name
     - :py:class:`~otupy.profiles.ctxd.data.name.Name`
     - 1
     - Id of the service.
   * - 2
     - type
     - :py:class:`~otupy.profiles.ctxd.data.service_type.ServiceType`
     - 1
     - It identifies the type of the service.
   * - 3
     - subservices
     - :py:class:`~otupy.types.base.array_of.ArrayOf`\(:py:class:`~otupy.profiles.ctxd.data.name.Name`)
     - 0
     - Subservices of the main service.
   * - 4
     - owner
     - ``str``
     - 0
     - Owner of the service.
   * - 5
     - release
     - ``str``
     - 0
     - Release version of the service.

