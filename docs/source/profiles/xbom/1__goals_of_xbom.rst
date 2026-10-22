1. Goals of XBOM
================

The eXtended Bill of Materials (XBOM) profile exposes Bills of Materials
through OpenC2. A Producer may request all BOMs known to a Consumer or identify
specific components whose BOMs are of interest.

The profile namespace is ``x-xbom``. The current implementation supports BOM
representation choices through a ``format`` argument and serialization choices
through an ``encoding`` argument. The returned BOM payloads are serialized
strings accompanied by their format and encoding metadata.
