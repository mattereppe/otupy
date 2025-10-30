.. _authorization-module:

#########################
Authorization
#########################

While authentication verifies the identity of a Producer, authorization determines whether that authenticated Producer has the permission to execute a specific command on a given target. This framework uses **Casbin**, a powerful and flexible open-source access control library, to manage and enforce authorization policies.

.. contents::
   :local:

Decoupled Authorization with Casbin
===================================

Casbin provides a policy-based access control mechanism that decouples the authorization logic from the application code. This is achieved by defining the access rules in external files, which can be updated without modifying the Consumer's source code.

The core of Casbin's integration is built around two main components:

* **Model File**: This configuration file (e.g., ``model.conf``) defines the access control model using the **PERM (Policy, Effect, Request, Matchers)** metamodel. For this framework, a standard **Role-Based Access Control (RBAC)** model is used, which allows for defining permissions based on roles assigned to users.
* **Policy File**: This file (e.g., ``policy.csv``) contains the actual authorization rules. It defines which **subjects** (``sub``, e.g., a user or a role) are allowed to perform an **action** (``act``) on an **object** (``obj``).

Authorization Workflow
======================

The authorization process takes place within the ``Consumer`` after a command has been successfully authenticated:

1.  **Token Validation**: After receiving an OpenC2 command, the ``OAuth2Authorizer`` module first introspects the access token with the Authorization Server to validate it .
2.  **Subject Identification**: If the token is valid, the introspected data typically contains the identity of the user (the subject) who authorized the Producer (e.g., a username or a unique ID).
3.  **Request Formulation**: The ``Authorizer`` constructs an authorization request tuple from the OpenC2 command, in the format ``(subject, object, action)``.
    * `subject`: The user identity from the token.
    * `object`: The target of the OpenC2 command (e.g., 'ipv4_net').
    * `action`: The action of the OpenC2 command (e.g., 'deny').
4.  **Policy Enforcement**: The ``Authorizer`` calls Casbin's ``enforce()`` method with the request tuple. Casbin evaluates the request against the loaded model and policy rules.
5.  **Decision**:
    * If the policy allows the request, the command is forwarded to the appropriate Actuator for execution.
    * If the policy denies the request, the Consumer rejects the command with a ``403 Forbidden`` status, indicating that the Producer is authenticated but not authorized to perform that specific operation.

Usage Example: Configuring the Consumer
---------------------------------------

To enable authorization, the ``Consumer`` must be instantiated with an ``OAuth2Authorizer``. This object is configured with the paths to the Casbin model and policy files.

**1. Define the Casbin Model (`model.conf`)**

This file defines an RBAC model where a request is allowed if the subject has a role that is granted permission for the requested action on the object.

.. code-block:: ini
   :caption: model.conf

   [request_definition]
   r = sub, obj, act

   [policy_definition]
   p = sub, obj, act

   [role_definition]
   g = _, _

   [policy_effect]
   e = some(where (p.eft == allow))

   [matchers]
   m = g(r.sub, p.sub) && r.obj == p.obj && r.act == p.act

**2. Define the Casbin Policy (`policy.csv`)**

This file assigns roles to users and defines permissions for those roles. In this example, the `security_analyst` can only `query` resources, while the `network_admin` can also `deny` traffic.

.. code-block:: csv
   :caption: policy.csv

   # Policies (permissions for roles)
   p, security_analyst, features, query
   p, network_admin, ipv4_net, deny
   p, network_admin, ipv6_net, deny

   # Role assignments (users assigned to roles)
   g, alice, network_admin
   g, bob, security_analyst
   g, alice, security_analyst

**3. Configure the Consumer**

The Consumer is configured to use the ``OAuth2Authorizer`` with the specified model and policy files.

.. code-block:: python

   from otupy.core import Consumer
   from otupy.transfers.http.http_transfer import HTTPTransfer
   from otupy.oauth2.OAuth2Authorizer import OAuth2Authorizer
   from otupy.actuators.slpf.dumb_actuator import MyFirewallActuator

   def main():
       """Create and run a secure OpenC2 Consumer with authorization."""
       # Configuration for the Authorizer, including Casbin files
       auth_config = {
           'as_url': 'http://127.0.0.1:5000',
           'ua_url': 'http://127.0.0.1:5001',
           'model': 'path/to/your/model.conf',
           'policy': 'path/to/your/policy.csv'
       }
       authorizer = OAuth2Authorizer(**auth_config)

       # Instantiate the Consumer with the authorizer
       consumer = Consumer(
           actuators={'slpf': MyFirewallActuator()},
           authorizer=authorizer
       )

       # The transfer layer will automatically use the authorizer
       # to check authentication and authorization for every request.
       http_server = HTTPTransfer("127.0.0.1", 9000)
       print("Starting secure consumer...")
       http_server.start(consumer)

   if __name__ == "__main__":
       main()