6. Examples
===========

This section shows how an application uses the Python ``otupy`` API to create
NFM OpenC2 commands and send them to a Consumer. The examples use JSON over
HTTP, but the command objects are independent of the selected encoder and
transfer implementation.


6.1 Common Setup
----------------

Import the OpenC2 command classes, the NFM extension, and the HTTP/JSON stack.
The NFM import registers the profile data types and the extended ``Feature``
values used in the following examples.

.. code-block:: python

   from otupy import Actions, Args, Command, Feature, Features, Producer, ResponseType
   from otupy.encoders.json import JSONEncoder
   from otupy.transfers.http import HTTPTransfer
   import otupy.profiles.nfm as nfm

   # Identify this Producer and the Consumer HTTP endpoint.
   producer = Producer(
       "producer.example.net",
       JSONEncoder(),
       HTTPTransfer("consumer.example.net", 8080),
   )

   # Optional: use only if this Consumer needs an explicit routing identifier.
   destination = nfm.Specifiers({"asset_id": "sensor-a"})

   # Request the complete response body for common query and stop commands.
   complete_response = Args({"response_requested": ResponseType.complete})

Replace the endpoint, Producer identifier, and ``asset_id`` with values from
your deployment. If the Consumer uses its default NFM actuator, pass
``actuator=None`` when creating the command instead of ``destination``.

6.2 Query Capabilities
----------------------

Query the routed actuator before starting a monitor. The response describes
the capabilities of the actual implementation, so it determines which monitor
fields and export arguments can be used safely.

.. code-block:: python

   query = Command(
       Actions.query,
       Features([
           Feature.versions,
           Feature.profiles,
           Feature.pairs,
           Feature.interfaces,
           Feature.information_elements,
           Feature.exports,
           Feature.export_options,
           Feature.flow_format,
           Feature.filters,
       ]),
       complete_response,
       actuator=destination,
   )

   response = producer.sendcmd(query)
   capabilities = response.content["results"]

``capabilities`` contains the values returned by the Consumer, for example
available interfaces, Information Elements, output formats, and filters. An
application can inspect this mapping to select a compatible monitor
configuration.

6.3 Start a Monitor
-------------------

This example requests monitoring on ``eth0``, exports NetFlow v5 records to a
collector, and asks for source and destination IP addresses. It assumes that
those interfaces, Information Elements, exporter settings, and format were
advertised by the preceding query.

.. code-block:: python

   from otupy.profiles.nfm.data.collector import Host
   from otupy.types.base import ArrayOf
   from otupy.types.data import Port

   # Define the flow-record destination.
   collectors = ArrayOf(nfm.Collector)()
   collectors.append(nfm.Collector(host=Host("192.0.2.20"), port=Port(2055)))

   # Select the flow source and fields. These are NFM-specific Command Arguments.
   interfaces = ArrayOf(nfm.Interface)()
   interfaces.append(nfm.Interface(name="eth0"))
   information_elements = ArrayOf(nfm.IE)()
   information_elements.append(nfm.IE("source ip"))
   information_elements.append(nfm.IE("destination ip"))

   # Add the interface, fields, and export configuration to the start arguments.
   start_arguments = nfm.Args({
       "interfaces": interfaces,
       "information_elements": information_elements,
       "exporter": nfm.Exporter(collectors=collectors),
       "exporter_options": nfm.ExportOptions(
           format=nfm.FlowFormat.netflow5,
           timeout=60,
       ),
   })

   # The target carries optional IPv4 or IPv6 traffic filters.
   monitor = nfm.FlowMonitor()

   start = Command(Actions.start, monitor, start_arguments, actuator=destination)
   response = producer.sendcmd(start)
   monitor_id = nfm.MonitorID(response.content["results"]["monitor_id"])

The Consumer returns ``monitor_id`` when the monitor is created. Persist that
value in the application if it will later need to stop the monitoring session.
The selected implementation may reject unsupported options, which is why the
capability query is performed first.

6.4 Stop a Monitor
------------------

Use the identifier returned by the start response as the ``monitor_id`` target.
The stop command does not need to reproduce the monitor configuration.

.. code-block:: python

   stop = Command(
       Actions.stop,
       monitor_id,
       complete_response,
       actuator=destination,
   )

   response = producer.sendcmd(stop)

Check the response status and any returned status text before removing the
stored monitor identifier from the application state.
