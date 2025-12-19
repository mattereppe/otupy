5.10 Cloud
==========

It describes a generic Cloud service.

Type: :py:class:`~otupy.profiles.ctxd.data.cloud.Cloud` (:py:class:`~otupy.types.base.record.Record`)

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
     - Generic description of the cloud service.
   * - 2
     - id
     - ``str``
     - 1
     - Id of the cloud provider.
   * - 3
     - name
     - ``str``
     - 1
     - Name of the cloud provider.
   * - 4
     - type
     - ``str``
     - 1
     - Type of the cloud service.

Sample Cloud object represented in JSON Format:

.. code:: json

   {
     "description": "cloud",
     "cloud_id": "123456",
     "name": "aws",
     "type": "lambda"
   }

