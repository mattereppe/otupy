2. Data model
=============

The main purpose for the Context Discovery profile is to return a description
of the execution environment, including digital services and the relationships
between them. Hence, the data model of the returned data revolves around two
key concepts:

-  :py:class:`~otupy.profiles.ctxd.data.service.Service`: 
	A Service is any
	kind of digital resource which can be identified and linked to other
	resources. It can be a software, an application, a repository,
	an infrastructure, a network, a device, and anything else may be
	subject to cyber-attacks. Its description includes location, 
	subservices, owner, release version. Most of the relevant information
	concerning the description of the service are indeed embedded
	in the :py:class:`~otupy.profiles.ctxd.data.service_type.ServiceType`, since they
	are specific to the service type. The current assumption is that 
	there is only one CTXD actuator that provides the service description
	through the :py:class:`~otupy.profiles.ctxd.data.service.Service` object,
	to avoid the risk of having multiple versions to merge. 

-  :py:class:`~otupy.profiles.ctxd.data.link.Link`: 
	A link is a relationship
	between two or more services. The :py:class:`~otupy.profiles.ctxd.data.link.Link`
	object describes the relationship between one 
	:py:attr:`~otupy.profiles.ctxd.data.link.Link.name` which is always
	described by the current actuator and one or more
	:py:attr:`~otupy.profiles.ctxd.data.link.Link.peers` which might be described
	by the same actuator or another one. In the last case, the
	:py:class:`~otupy.profiles.ctxd.data.Peer` object might include
	a :py:class:`~otupy.profiles.ctxd.data.consumer.Consumer` object that describes
	the endpoint where the whole service description can be retrieved
	(this object will not be present if the consumer does not know where
	to find this description or no ctxd consumer is avaiable to describe
	such service, i.e., it is an hidden node in the chain).
	It is responsibility of the producer that performs the discovery to
	query another consumer to build the whole service chain (there is no
	caching). Similar to the :py:class:`~otupy.profiles.ctxd.data.service.Service`:
	object, also for the :py:class:`~otupy.profiles.ctxd.data.link.Link` most
	of the descriptive elements are indeed in the 
	:py:class:`~otupy.profiles.ctxd.data.link_type.LinkType`, since they are specific
	of differente link types. Finally, note that multiple peers can
	be provided (e.g., multiple VMs controlled by the same software, or
	hosted on the same hypervisor), but this does not preclude implementations
	to alternatively returns different :py:class:`~otupy.profiles.ctxd.data.link.Link`
	objects for each peer. As last remark, the concept of peer also
	includes security functions managed by other profiles (e.g., slpf).
	
Additionally, one more class is relevant to locate the actuator responsible 
for external services and security functions:

-  :py:class:`~otupy.profiles.ctxd.data.consumer.Consumer`: 	
	This object provides
	information about a consumer endpoint. Indeed, it includes both 
	communication parameters (IP address, endpoint, serialization, transfer)
	as well as the profile and specifiers of the actuator. In case some
	parameter is not provided, it could be assumed as the default values
	(JSON over HTTPS).

.. figure:: ctxd-datamodel.png
   :alt: Context Discovery data model

