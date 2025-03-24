.. module:: your_module.app
   :synopsis: Streamlit application for retrieving and exporting user data from Account Manager.

app Module
==========

This module provides a Streamlit application for retrieving and exporting user data from Account Manager.

Classes
-------

.. autoclass:: your_module.app.StreamlitApp
   :members:

.. _streamlit-app:

StreamlitApp Class
-----------------

.. class:: StreamlitApp

    A Streamlit application that provides an interface for users to retrieve Account Manager users and offers a download button for an Excel file containing the user data.

    **Attributes:**

    - ``am_users_exporter`` (:class:`~your_module.account_manager_exporter.AccountManagerUsersExporter`): An instance responsible for exporting user data to an Excel file.

    **Methods:**

    - :meth:`~your_module.app.StreamlitApp.__init__`
    - :meth:`~your_module.app.StreamlitApp.run`
    - :meth:`~your_module.app.StreamlitApp.display_download_button`

    **Initialization:**

    You can initialize an instance of the `StreamlitApp` class by providing an instance of the :class:`~your_module.account_manager_exporter.AccountManagerUsersExporter` class.

    .. code-block:: python

        am_users_exporter = AccountManagerUsersExporter()
        app = StreamlitApp(am_users_exporter)

    **Running the Application:**

    The :meth:`~your_module.app.StreamlitApp.run` method executes the Streamlit app. It displays a button to fetch and download user data.

    .. code-block:: python

        app.run()

    **Displaying the Download Button:**

    The :meth:`~your_module.app.StreamlitApp.display_download_button` method displays a download button for the Excel file if it exists.

    .. code-block:: python

        app.display_download_button()

    .. important::

        Make sure to run the Streamlit application within the ``if __name__ == "__main__":`` block.

