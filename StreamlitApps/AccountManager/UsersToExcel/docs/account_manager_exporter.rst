.. module:: your_module.account_manager_exporter
   :synopsis: Module for exporting user details from Account Manager.

account_manager_exporter Module
===============================

This module provides a class for exporting user details from Account Manager to an Excel file.

Classes
-------

.. autoclass:: your_module.account_manager_exporter.AccountManagerUsersExporter
   :members:

.. _account-manager-users-exporter:

AccountManagerUsersExporter Class
----------------------------------

.. class:: AccountManagerUsersExporter

    Provides functionality to export user details from Account Manager to an Excel file.

    **Attributes:**

    - ``excel_file`` (str): The name of the Excel file where user data will be saved.
    - ``users_api_endpoint`` (str): The URL of the Account Manager users API.

    **Methods:**

    - :meth:`~your_module.account_manager_exporter.AccountManagerUsersExporter.__init__`
    - :meth:`~your_module.account_manager_exporter.AccountManagerUsersExporter.get_users`
    - :meth:`~your_module.account_manager_exporter.AccountManagerUsersExporter.export_users_to_excel`

    **Initialization:**

    You can initialize an instance of the `AccountManagerUsersExporter` class as follows:

    .. code-block:: python

        exporter = AccountManagerUsersExporter()

    **Get Users:**

    To fetch user details from the Account Manager, you can use the :meth:`~your_module.account_manager_exporter.AccountManagerUsersExporter.get_users` method. This method retrieves user data using an access token obtained through the client credentials grant type.

    .. code-block:: python

        users = exporter.get_users()

    **Export to Excel:**

    The :meth:`~your_module.account_manager_exporter.AccountManagerUsersExporter.export_users_to_excel` method allows you to export user details to an Excel file. Only users with the userState values Enabled, Deleted, and Initial will be exported.

    .. code-block:: python

        exporter.export_users_to_excel()

    .. important::

        Ensure that the necessary configurations, such as client credentials and API endpoints, are set in your environment using a configuration library like `python-decouple`.

