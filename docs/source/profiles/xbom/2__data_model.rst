2. Data model
=============

The current XBOM OpenC2 wire model is deliberately small:

* the profile-specific ``x-xbom:boms`` target is an array of component
  identifiers (strings); an empty target requests all available BOMs;
* command arguments select the requested BOM ``format`` and ``encoding`` and
  optionally allow cached information;
* the response contains ``boms`` as an array of serialized strings together
  with the ``format`` and ``encoding`` used for those strings.

The internal :mod:`otupy.profiles.xbom.data` package contains additional model
classes used while constructing BOM content. Those implementation types should
not be confused with the current OpenC2 result envelope, which transports
serialized BOM strings.
