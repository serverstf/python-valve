Steam Web API
*************

The Steam Web API provides a mechanism to use Steam services over an HTTP.
The API is divided up into "interfaces" with each interface having a number of
methods that can be performed on it. Python-valve provides a thin wrapper on
top of these interfaces as well as a higher-level implementation.

Generally you'll want to use the higher-level interface to the API as it
provides greater abstraction and session management. However the higher-level
API only covers a few core interfaces of the Steam Web API, so it may be
necessary to use the wrapper layer in some circumstances.

Although an API key is not strictly necessary to use the Steam Web API, it is
advisable to `get an API key <http://steamcommunity.com/dev/apikey>`_. Using an
API key allows access to greater functionality. Also, before using the Steam
Web API it is good idea to read the
`Steam Web API Terms of Use <http://steamcommunity.com/dev/apiterms>`_ and
`Steam Web API Documentation <http://steamcommunity.com/dev/>`_.


.. module:: valve.steam.api.interface


Low-level Wrapper
=================

The Steam Web API is self-documenting via the
``/ISteamWebAPIUtil/GetSupportedAPIList/v1/`` endpoint. This enables
python-valve to build the wrapper entirely automatically, which includes
validating parameters and automatic generation of documentation.

The entry-point for using the API wrapper is by constructing a :class:`API`
instance. During initialisation a request is issued to the
``GetSupportedAPIList`` endpoint and the interfaces are constructed. If a Steam
Web API key is specified then a wider selection of interfaces will be available.
Note that this can be a relatively time consuming process as the response
returned by ``GetSupportedAPIList`` can be quite large. This is especially true
when an API key is given as there are more interfaces to generated.

An instance of each interface is created and bound to the :class:`API`
instance, as it is this :class:`API` instance that will be responsible for
dispatching the HTTP requests. The interfaces are made available via
:meth:`API.__getitem__`. The interface objects have methods which correspond
to those returned by ``GetSupportedAPIList``.

.. autoclass:: API
    :members:
    :undoc-members:
    :special-members: __init__, __getitem__


Interface Method Version Pinning
--------------------------------

It's important to be aware of the fact that API interface methods can have
multiple versions. For example, ``ISteamApps/GetAppList``. This means they may
take different arguments and returned different responses. The default
behaviour of the API wrapper is to always expose the method with the highest
version number.

This is fine in most cases, however it does pose a potential problem. New
versions of interface methods are likely to break backwards compatability.
Therefore :class:`API` provides a mechanism to manually specify the interface
method versions to use via the ``versions`` argument to :meth:`API.__init__`.

The if given at all, ``versions`` is expected to be a dictionary of dictionaries
keyed against interface names. The inner dictionaries map method names to
versions. For example:

.. code:: python

    {"ISteamApps": {"GetAppList": 1}}

Passsing this into :meth:`API.__init__` would mean version 1 of
``ISteamApps/GetAppList`` would be used in preference to the default behaviour
of using the highest version -- wich at the time of writing is version 2.

It is important to pin your interface method versions when your code enters
production or otherwise face the risk of it breaking in the future if and when
Valve updates the Steam Web API. The :meth:`API.pin_versions()` method is
provided to help in determining what versions to pin. How to integrate interface
method version pinning into existing code is an excerise for the reader however.


Response Formatters
-------------------

.. autofunction:: json_format

.. autofunction:: etree_format

.. autofunction:: vdf_format


Interfaces
==========

These interfaces are automatically wrapped and documented. The availability of
some interfaces is dependant on whether or not an API key is given. It should
also be noted that as the interfaces are generated automatically they do not
respect the naming conventions as detailed in PEP 8.

.. automodule:: interfaces
    :members:
    :undoc-members:
