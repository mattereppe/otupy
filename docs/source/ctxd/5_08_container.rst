5.8 Container
=============

It describes a generic Container.

Type: :py:class:`~otupy.profiles.ctxd.data.container.Container` (:py:class:`~otupy.types.base.record.Record`)

.. list-table::
   :widths: 3 4 4 3 40
   :header-rows: 1

   * - ID
     - Name
     - Type
     - #
     - Description
   * - 1
     - description
     - ``str``
     - 1
     - Generic description of the container.
   * - 2
     - id
     - ``str``
     - 1
     - ID of the Container.
   * - 3
     - name
     - ``str``
     - 1
     - Hostname of the Container.
   * - 4
     - namespace
     - ``str``
     - 1
     - Namespace of the pod hosting the Container.
   * - 5
     - status
     - ``str``
     - 1
     - Current status of the contaienr.
   * - 6
     - image
     - ``str``
     - 1
     - Software image used to boot the container.

Sample Container object represented in JSON Format:

.. code:: json

   {
     "description": "container",
     "id": "123456",
     "hostname": "container_name",
     "namespace": "default",
     "image": "debian-stable.img"
   }

