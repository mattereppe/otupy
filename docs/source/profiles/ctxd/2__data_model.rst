2. Data model
=============

The CTXD wire result is built from two model types located in
:mod:`otupy.models.ctxd`:

``Service``
   A digital resource such as software, an application, a host, a network,
   infrastructure, or another identifiable component. Services can carry a
   structured service identifier (``SId``), type information, ownership and
   release metadata, and references to subservices.

``Link``
   A relationship owned by a service and connecting it to one or more peers.
   A link can carry a description, link type, role, and peer set.

The current profile result therefore returns arrays of
:py:class:`~otupy.models.ctxd.Service` and :py:class:`~otupy.models.ctxd.Link`.
The profile-specific ``Context`` target itself no longer contains selectors for
individual service or link names.
