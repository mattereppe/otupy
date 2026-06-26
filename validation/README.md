# Otupy validation suite

There are multiple tests available to check the compliance of otupy with the Language Specification, concerning data types, serialization, and message exchange. The same tests are available for both ```otupy``` and ```lycan``` in the folders of the same name, with the necessary profiles definitions for each tool. Test concerning the exchange of messages over the network are not available for ```lycan```, since this library does not include a transfer protocol. See our paper [1] for a discussion of numerical results and motivations.

## Data types
A first set of tests concerns the correct instantiation of data, including both data, targets, args, artifacts, and commands.



To run these tests, enter the ```test_types``` folder and run:
```
% pytest
```

## Encoding/Deconding messages

This is a more complete set of tests concerning the correct serialization and deserialization of messages. JSON samples were taken from a third party site [2], but they were reclassified to be strictly compliant to what found in the Specification (see [1] for a detailed list of issues found in the original dataset). To run these tests, enter the ```test_json``` folder.

There are three types of tests available:
- Deserialization of good samples: this takes the good JSON sample and deserialize them, checking for success:
```
% pytest test_commands.py::test_decoding
% pytest test_response.py::test_decoding
```
- Deserialization of bad samples: this takes the bad JSON sample and deserialize them, checking for failure:
```
% pytest test_commands.py::test_decoding_invalid
% pytest test_response.py::test_decoding_invalid
```
- Serialialization: this takes good samples only, deserialize them to obtain the internal representation, serialize them and check the result is the same as the original. Some fixes are present to account for equivalent representations (e.g., lowercase/uppercase MAC addresses).
```
% pytest test_commands.py::test_encoding
% pytest test_response.py::test_encoding
```

The same tests are also available for other serialization format. Use the same commands as above in the ```test_cbor```, ```test_yaml```, and ```test_xml``` folders. Note that these additional folders mostly replicate the same code as for json; changes to the validation routines must be applied to all folders.

## Sending/Receiving messages

These tests validate the syntax of  of both Commands and Responses messages over HTTP and MQTT. For this purpose, we only took into consideration JSON serialization, which is the only officially supported method so far.  

### HTTP

To run the test, enter the ```test_json``` folder and run:
```
% pytest test_commands.py::test_sending
```
for testing good commands, and
```
% pytest test_commands.py::test_response_to_invalid_commands
```
for testing bad commands.


To perform these tests, a Consumer must run and answer to requests from the Producer, which is emulated in the tests. A dumb consumer is available that uses dumb actuators, because the sample commands usually does not make sense for a real function.
To run this OpenC2 server, run:
```
% python3 ../../../examples/server-testing.py 
```
(Any other OpenC2 server implementation would be fine for running these tests, but the expected answers will likely change and this might impact the correctness of the results).

### MQTT

For these tests, an MQTT server is required (e.g., mosquitto). An example of OpenC2 server is available in the examples folder (server-mqtt.py). Run it:
```
% python3 server-mqtt.py
```
And then the following tests are available:
- sending good json-encoded commands:
  ```
  % pytest test_commands.py::test_sending
  ```
- sending good cbor-encoded commands:
  ```
  % pytest test_commands.py::test_sending_cbor
  ```
- sending bad json-encoded commands:
  ```
  % pytest test_commands.py::test_response_to_invalid_commands
  ```
- sending bad cbor-encoded commands:
  ```
  % pytest test_commands.py::test_response_to_invalid_commands_cbor
  ```

## Performance analysis 
The following procedure describes how to collect performance measures when running both the Producer and the Consumer on localhost. This makes perfect sense for this kind of analysis, to avoid counting the random effects of network traversal.

First, remove existing log files, if any.
```
% rm -rf controller.log server.log
```
Run the server:
```
% ../../examples/server-testing.py
```

Then run the simulation (change the number of trials in the Producer according to your needs):
```
% ./controller.py
```

Collect log file from the server
```
% cp ../../examples/server.log .
```

Collect statistics:
```
% awk -f server.awk server.log  | gawk -f stat-server.awk > server.txt
% awk -f controller.awk controller.log  | gawk -f stat-controller.awk > controller.txt
```

For network traces:
- Use wireshark to capture, display filter "HTTP", View -> Time from previous displayed.
- Export packet dissection as txt.
- Run the following awk filter:
  ```
  % grep "HTTP/1.1"  nettrace.txt| grep -v "POST" | awk 'BEGIN{ tot=0; count=0; min=99999; max=0} { tot+=$2; count++; if( $2 < min ) min=$2; if (max < $2) max=$2;} END{printf("Tot\tAvg\tMin\tMax\n"); printf("%s\t%s\t%s\t%s\n",count, tot/count, min, max);}'
  ```

  For serialization and deserialization measures only (both for ```oc2lib``` and ```Lycan```), run the following executables:
  ```
  % ./controller-serialization-only.py > data.log        <-- otupy
  % ./controller.py > data.log                           <-- Lycan
  ```
  and then collect data with:
  ```
  % wk -F ":" -f encoding.awk data.log | awk -F ":" -f stat.awk > stat.txt
  ```

# Datasets

Validation samples were created by extending and revising the original work from [2]. They are classified as "good" and "bad" samples: the former are valid OpenC2 messages, the latter are invalid syntax expected to raise errors from the receiving party.



# References

  [1] M. Repetto. Otupy: A flexible, portable, and extensible framework for remote control of security functions, Computers & Security, no. 158, art. 104597, 2025. DOI: [10.1016/j.cose.2025.104597](https://doi.org/10.1016/j.cose.2025.104597).
  
  [2]	B. Berliner. OpenC2 JSON-schema command/response validator and test suite. GitHub repository, 2019. [accessed June 2026]. URL: [https://github.com/bberliner/openc2-json-schema](https://github.com/bberliner/openc2-json-schema). 
