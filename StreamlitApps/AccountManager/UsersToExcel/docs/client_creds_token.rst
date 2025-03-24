.. module:: your_module.client_creds_token
   :synopsis: Module for client credentials token retrieval.

client_creds_token Module
=========================

This module provides functions for retrieving an access token using the client credentials grant type.

Functions
---------

.. autofunction:: your_module.client_creds_token.get_access_token

.. _get-access-token:

get_access_token()
------------------

.. function:: get_access_token() -> str

    Retrieve an access token using the client credentials grant type.

    This function sends a POST request to an OAuth2 authorization server to obtain
    an access token using the client credentials grant type.

    Returns:
        str: The access token obtained from the authorization server.

    Raises:
        requests.exceptions.RequestException: An error occurred during the HTTP request.
        ValueError: The response from the authorization server does not contain an access token.

    .. code-block:: python

        try:
            access_token = get_access_token()
        except Exception as e:
            print(f'Error extracting access token: {e}')

