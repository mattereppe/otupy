1. Goals of XBOM
================

To fill the gap left by the OpenC2 specifications, a new Actuator
Profile has been introduced with the goal to abstract the services that
are running into the network, the interactions between them and the security
features that they implement. Identifying a service involves determining its
type and the specific characteristics of that type, and generating an Extended
Bill of Materials (XBOM) compliant with the state of the art bill of materials
specifications, such as the CycloneDX. This profile was defined to replace the 
previous approach of defining the context as a list of services and links, as 
defined by the CTXD Actuator Profile.

This new Actuator Profile has been named "eXtended Bill of Materials", herein referred as XBOM, with the nsid "x-xbom".

The XBOM profile employs a standard method to generate BOMs,
recursevily querying each digital resource to determine its composition. Thus, the
Producer can obtain from the Consumer the information on how to connect to the
digital resources linked to the Consumer, and then query them to
produce a complete BOM of the entire system.

The XBOM profile is implemented on the Consumer side and is
one of the possible Actuator Profiles that the Consumer can support.
Communication follows the OpenC2 standard, where a Producer sends a
Command specifying that the Actuator to execute it is XBOM. If the
Consumer implements XBOM, it will return a Response containing the generated BOM.


