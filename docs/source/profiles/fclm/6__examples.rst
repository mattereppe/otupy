6. Examples
===========

This section shows how an application uses the Python ``otupy`` API to create
FCLM OpenC2 commands and send them to a Consumer. The examples use JSON over
HTTP, but the command objects are independent of the selected encoder and
transfer implementation.

6.1 Common Setup
----------------

Import the common OpenC2 classes, the FCLM extension, and the HTTP/JSON stack.
Importing FCLM registers the profile data types and the extended ``Feature``
values used in the following examples.

.. code-block:: python

   import otupy as oc2
   from otupy.encoders.json import JSONEncoder
   from otupy.profiles.fclm.data.collector import Host
   from otupy.transfers.http import HTTPTransfer
   import otupy.profiles.fclm as fclm

   # Identify this Producer and the Consumer HTTP endpoint.
   producer = oc2.Producer(
       "producer.example.net",
       JSONEncoder(),
       HTTPTransfer("consumer.example.net", 8080),
   )

   # Optional: use only if this Consumer needs an explicit routing identifier.
   destination = fclm.Specifiers({"asset_id": "fclm-filebeat"})

   # FCLM responses carrying results are requested in their complete form.
   complete_response = fclm.Args({"response_requested": oc2.ResponseType.complete})

Replace the endpoint, Producer identifier, and ``asset_id`` with values from
your deployment. If the Consumer uses its default FCLM actuator, pass
``actuator=None`` when creating a command instead of ``destination``.

6.2 Query Capabilities
----------------------

Query the routed actuator before starting a log collection session. The response
describes the capabilities of the actual implementation, so it determines which
source types, exporter settings, fields, and input controls can be used safely.

.. code-block:: python

   query = oc2.Command(
       oc2.Actions.query,
       oc2.Features(
           [
               oc2.Feature.versions,
               oc2.Feature.profiles,
               oc2.Feature.pairs,
               oc2.Feature.export_fields,
               oc2.Feature.exports_config,
               oc2.Feature.imports_config,
               oc2.Feature.import_controls,
           ]
       ),
       complete_response,
       actuator=destination,
   )

   response = producer.sendcmd(query)
   capabilities = response.content["results"]

``capabilities`` contains the values returned by the Consumer, such as export
field names and supported import/export configuration. An application can
inspect this mapping to select a compatible log-monitor configuration.

6.3 Start a Log Monitor
-----------------------

This example monitors a local web-server log, sends selected fields to a
collector using JSON, and applies input scan/backoff controls. It assumes that
the source, exporter settings, fields, and controls were advertised by the
preceding query.

.. code-block:: python

   # Select the fields carried in exported log records.
   export_fields = oc2.ArrayOf(fclm.EF)()
   for field in ("timestamp", "metadata", "message", "log.file.path", "input.type"):
       export_fields.append(fclm.EF(field))

   # Configure the receiving collector.
   collectors = oc2.ArrayOf(fclm.Collector)()
   collectors.append(
       fclm.Collector(
           host=Host("192.0.2.20"),
           port=oc2.Port(1234),
           format=fclm.FileFormat.json,
       )
   )

   start_arguments = fclm.Args(
       {
           "exporter": fclm.Exporter(collectors=collectors),
           "import_controls": fclm.ImportOptions(
               scan_frequency=oc2.Duration(10),
               max_backoff=oc2.Duration(10),
           ),
           "export_fields": export_fields,
       }
   )

   # Define the source to collect. A URI or Socket may be used instead.
   monitor = fclm.LogMonitor(oc2.File({"path": "/var/log/http_access.log"}))

   start = oc2.Command(
       oc2.Actions.start,
       monitor,
       start_arguments,
       actuator=destination,
   )
   response = producer.sendcmd(start)
   monitor_id = fclm.MonitorID(response.content["results"]["monitor_id"])

The Consumer returns ``monitor_id`` when the session is created. Persist that
value in the application if it will later need to stop the log collection
session. The selected implementation may reject unsupported options, which is
why the capability query is performed first.

6.4 Stop a Log Monitor
----------------------

Use the identifier returned by the start response as the ``monitor_id`` target.
The stop command does not need to reproduce the source or exporter
configuration.

.. code-block:: python

   stop = oc2.Command(
       oc2.Actions.stop,
       monitor_id,
       complete_response,
       actuator=destination,
   )

   response = producer.sendcmd(stop)

Check the response status and any returned status text before removing the
stored monitor identifier from the application state.
