otupy: OpenC2 Utilities for Python
==================================

``otupy`` (/’əʊtu:paɪ/) is an open-source implementation of the OpenC2
language written in Python. 

Description
-----------

``otupy`` is explicitly designed with flexibility
and extensibility in mind, meaning that additional profiles and
actuators can be added without impacting the core library itself. For
this reason, it is particullary suited for: 

* developers that are looking for a common interface to control their remote cybersecurity functions; 
* researchers that design new profiles for cybersecurity functions; 
* system integrators that need a common language for their cybersecurity frameworks.

Usage and extension of ``otupy`` have a shallow learning curve because data
structures are explicitly designed to follow the language specification.
Differently from many other implementations publicly available,
introducing new transfer protocols, new message encoding formats, new
profiles, and new implementations of actuators does not require
modification to the core package; these extensions are easily to
introduce because they largely reflect the language specification, hence
minimal comprehension of the ``otupy`` is required to getting started.

The ``otupy`` currently provides:

* the implementation of the core functions that implement the OpenC2 Architecture and Language Specification; 
* an implementation of the json encoder; 
* an implementation of the HTTP transfer protocol; 
* the definition of the SLPF profile; 
* a dumb implementation of an actuator for the SLPF profile.

Compatibility
-------------

Python 3.9+ is required to run ``otupy`` (Python 3.11 was used for development).

Getting started
---------------

.. toctree::
   :maxdepth: 1

   background
   architecture
   download
   usage

Advanced usage
--------------

Advanced usage of ``otupy`` requires knowledge of its data
structures and functions. Data structures are very straightforward to
learn, because they strictly follow the definition and requirements in
the common Language Specification and Profile extensions. 

.. toctree::
   :maxdepth: 1

   API reference <_autosummary/otupy>
   developerguide
   developingextensions
   logging
	documentation





Extensions
----------

``otupy`` comes with several extensions and use cases: 

.. toctree::
   :maxdepth: 1

   ctxd/ctxd   

Additional notes
----------------

.. toctree::
   :maxdepth: 1

   authors
   contributing
   changelog
   license

