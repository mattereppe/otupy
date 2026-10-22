6. Examples
===========

This section shows how an application builds and sends RCLI OpenC2 Commands
with the Python ``otupy`` API. It deliberately focuses on the command objects:
the application-specific transport setup and user interface are outside the
scope of these examples.

6.1 Common Setup
----------------

Import the common OpenC2 classes and the RCLI profile types. The snippets
assume that ``producer`` is an already initialized ``oc2.Producer`` instance.

.. code-block:: python

   import hashlib
   import otupy as oc2
   from otupy.profiles.rcli.data.process import Process
   from otupy.profiles.rcli.targets.files import Files
   from otupy.profiles.rcli.targets.processes import Processes
   from otupy.types.targets.file import File
   import otupy.profiles.rcli as rcli

   # Route the Command to the intended Consumer destination.
   destination = rcli.Specifiers({"asset_id": "rcli-linux-01"})

   # The current RCLI actuator returns command results in a complete response.
   complete_response = rcli.Args(
       {"response_requested": oc2.ResponseType.complete}
   )

Replace the sample ``asset_id`` with the routing identifier used by the
Consumer deployment. It does not select the host implementation or alter its
capabilities.

6.2 Query Capabilities
----------------------

Before starting a process, query the destination for its OpenC2 features and
the commands that its RCLI actuator allows. The ``clicommands`` result lists
the command names and permitted flags or path arguments that can be used in a
``start processes`` Command.

.. code-block:: python

   capability_query = oc2.Command(
       oc2.Actions.query,
       oc2.Features(
           [
               oc2.Feature.versions,
               oc2.Feature.profiles,
               oc2.Feature.pairs,
               oc2.Feature.clicommands,
           ]
       ),
       complete_response,
       actuator=destination,
   )

   capability_response = producer.sendcmd(capability_query)
   capabilities = capability_response.content["results"]
   allowed_commands = capabilities["clicommands"]

Use ``allowed_commands`` to select the name and argument string in the next
example. A Command not listed by this response is rejected by the actuator.

6.3 Copy an Artifact
--------------------

The ``copy`` Action places an artifact in the actuator-managed storage area.
This example supplies a shell-script payload and requests the storage location
and file name. The application can instead construct the Artifact with a URI
payload when the Consumer is permitted to retrieve it.

.. code-block:: python

   script = b"#!/bin/sh\\necho 'RCLI artifact'\\n"
   artifact = oc2.Artifact(
       mime_type="application/x-sh",
       payload=oc2.Binary(script),
       hashes=oc2.Hashes(
           {"md5": oc2.Binaryx(hashlib.md5(script).digest())}
       ),
   )

   storage = File({"path": "tools", "name": "collector.sh"})
   copy_arguments = rcli.Args(
       {
           "response_requested": oc2.ResponseType.complete,
           "storage": storage,
       }
   )

   copy_command = oc2.Command(
       oc2.Actions.copy,
       artifact,
       copy_arguments,
       actuator=destination,
   )
   copy_response = producer.sendcmd(copy_command)
   copied_file = copy_response.content["results"]["file_status"][0]

The returned ``file_status`` entry records the file that the actuator manages.
The same path and name can be used to query or delete it later.

6.4 Start an Approved Command
-----------------------------

Build a ``Processes`` target containing an allowlisted command. The ``fprobe``
invocation below is illustrative and is valid only when the earlier capability
query advertises ``fprobe`` and the shown arguments. Substitute a command and
arguments returned by the addressed actuator.

.. code-block:: python

   process = Process(
       name="fprobe",
       command_line="-l 2 -i eth0 collector.example.net:2055",
   )
   processes = Processes()
   processes.append(process)

   start_command = oc2.Command(
       oc2.Actions.start,
       processes,
       complete_response,
       actuator=destination,
   )
   start_response = producer.sendcmd(start_command)
   process_id = start_response.content["results"]["process_status"][0]["pid"]

The ``process_status`` result identifies the process created by the actuator.
Save its ``pid`` when the application must query or stop that particular
process.

6.5 Query and Stop a Process
----------------------------

Use a ``Processes`` target with the returned process identifier to get its
current state, then issue a ``stop`` Command for that same process. Supplying a
specific identifier avoids the empty-target behavior, which applies to all
processes tracked by the actuator.

.. code-block:: python

   selected_process = Processes()
   selected_process.append(Process(pid=process_id))

   process_query = oc2.Command(
       oc2.Actions.query,
       selected_process,
       complete_response,
       actuator=destination,
   )
   process_response = producer.sendcmd(process_query)
   state = process_response.content["results"]["process_status"][0]["state"]

   stop_command = oc2.Command(
       oc2.Actions.stop,
       selected_process,
       complete_response,
       actuator=destination,
   )
   stop_response = producer.sendcmd(stop_command)

6.6 Query and Delete a Stored File
----------------------------------

Use the ``Files`` target to inspect a copied artifact and remove it when it is
no longer required. The target below matches the ``storage`` argument in the
copy example.

.. code-block:: python

   stored_files = Files()
   stored_files.append(File({"path": "tools", "name": "collector.sh"}))

   file_query = oc2.Command(
       oc2.Actions.query,
       stored_files,
       complete_response,
       actuator=destination,
   )
   file_response = producer.sendcmd(file_query)
   file_status = file_response.content["results"]["file_status"]

   delete_command = oc2.Command(
       oc2.Actions.delete,
       stored_files,
       complete_response,
       actuator=destination,
   )
   delete_response = producer.sendcmd(delete_command)
