.. _authentication-module:

########################
Authentication
########################

This document describes the authentication layer of the OpenC2 framework, which is designed to verify the identity of the entities involved in the command and control process. The implementation is based on the **OAuth 2.0** authorization framework, a robust and widely adopted standard for delegated access.

.. contents::
   :local:

Architecture Components
=======================

The authentication architecture extends the standard OpenC2 Producer-Consumer model by introducing dedicated components to handle security flows. The primary functional blocks are :

* **Producer**: This is the entity that issues OpenC2 commands. In this security context, it acts as the **OAuth 2.0 Client**. Its main responsibilities include initiating the authentication flow when necessary, managing access tokens (and refresh tokens), and attaching the valid token to every outgoing command to prove its identity.
* **Consumer**: This entity receives and executes OpenC2 commands. It functions as the **OAuth 2.0 Resource Server**. Its security role is to intercept every incoming command, validate the attached access token, and reject any request that lacks proper authentication credentials .
* **Authorization Server (AS)**: This is a new, centralized component that acts as the core of the trust model. It is responsible for authenticating the human operator (the **Resource Owner**), obtaining their consent, and issuing access tokens to the Producer upon a successful authorization grant .
* **User Agent (UA)**: Since Producers are often command-line tools or backend services without a graphical interface, the User Agent acts as a web-based intermediary. It provides the necessary interface for the operator to interact with the Authorization Server (e.g., to enter credentials) and approve the Producer's access request.

.. figure:: docs/source/Pictures/general_arch.png
   :align: center
   :alt: System Architecture

   High-level architecture of the OAuth 2.0 integration in OpenC2.

End-to-End Authentication Flow
==============================

The authentication process is triggered when a Producer attempts to send a command without a valid access token. The flow follows the **Authorization Code Grant**, which is considered the most secure OAuth 2.0 flow for confidential clients because it prevents access tokens from being exposed to the user-agent.

The complete sequence is as follows:

1.  **Unauthorized Command**: The Producer sends a command to the Consumer. Since it doesn't have an access token, the Consumer rejects the request with a ``401 Unauthorized`` status. The response body contains the URL of the User Agent (UA), which is the entry point for the authentication process.
2.  **Authentication Trigger**: The Producer's ``OAuth2Authenticator`` module receives the 401 response and initiates the authentication flow. It first contacts the UA to discover the location of the Authorization Server (AS).
3.  **User Interaction via UA**: The Producer instructs the UA to start the process. The UA, acting as a headless browser, redirects the operator to the AS's login page.
4.  **Operator Authentication and Consent**: The human operator authenticates with the AS (e.g., with a username and password) and grants the Producer permission to perform OpenC2 operations on their behalf.
5.  **Authorization Code Reception**: After consent is given, the AS redirects the UA to the Producer's callback endpoint (e.g., ``/callback``), including a short-lived, single-use **authorization code** in the URL parameters .
6.  **Token Exchange**: The Producer receives the authorization code and immediately makes a secure, direct (back-channel) request to the AS's ``/token`` endpoint. This request includes the authorization code and the Producer's own credentials (client_id and client_secret) to authenticate itself.
7.  **Access Token Issuance**: The AS validates the code and the client's credentials. If everything is correct, it issues an **access token** and, optionally, a long-lived **refresh token**. The Producer securely stores these tokens for future use .
8.  **Authenticated Command**: The Producer can now resend the original OpenC2 command, this time including the access token in the ``Authorization: Bearer <token>`` header of the HTTP request.
9.  **Token Introspection**: The Consumer receives the authenticated command, extracts the token, and validates it by sending it to the AS's ``/introspect`` endpoint. If the AS confirms the token is active and valid, the command is passed to the next stage: authorization.

.. figure:: docs/source/Pictures/oauth2flow.png
   :align: center
   :alt: Sequence Diagram

   Sequence diagram of the complete authentication and command execution flow.

Usage Example: Configuring the Producer
---------------------------------------

To use the authentication module, the ``Producer`` must be instantiated with an ``OAuth2Authenticator`` object. This object requires the client's credentials and the callback configuration. The ``sendcmd()`` method will automatically handle the authentication flow if a valid token is not already available.

.. code-block:: python

   from otupy.core import Producer
   from otupy.encoders.json import JSONEncoder
   from otupy.transfers.http.http_transfer import HTTPTransfer
   from otupy.oauth2.OAuth2Authenticator import OAuth2Authenticator
   import openc2 as oc2

   def main():
       """Create an OAuth2-enabled Producer and send a command."""
       # Configuration for the OAuth2 client (Producer)
       oauth2_config = {
           'client_id': 'my-producer-client-id',
           'client_secret': 'my-super-secret-key',
           'redirect_uri': 'http://127.0.0.1:8000/callback',
           'callback_port': 8000
       }

       # Instantiate the authenticator
       oauth2_authenticator = OAuth2Authenticator(**oauth2_config)

       # Instantiate the Producer with the authenticator module
       producer = Producer(
           producer="producer.example.net",
           encoder=JSONEncoder(),
           transfer=HTTPTransfer("127.0.0.1", 9000),
           authenticator=oauth2_authenticator
       )

       # Create an example OpenC2 command to send
       command = oc2.Command(
           action=oc2.Actions.deny,
           target=oc2.IPv4Net('198.51.100.10/32')
       )

       # The first time sendcmd() is called, it will trigger the full
       # authentication flow if no token is stored. Subsequent calls
       # will reuse the stored token until it expires.
       print("Sending OpenC2 command...")
       response = producer.sendcmd(command)
       print(f"Received response: {response}")

   if __name__ == "__main__":
       main()