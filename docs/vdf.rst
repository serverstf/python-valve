.. module:: valve.vdf

Valve Data Format
*****************

Decoding
========

The high-level API for decoding VDF files and strings.

.. autofunction:: load

.. autofunction:: loads


Encoding
========

The high-level API for encoding VDF documents.

.. autofunction:: dump

.. autofunction:: dumps


Document Transclusion
=====================

.. autoclass:: VDFDisabledTranscluder

.. autoclass:: VDFIgnoreTranscluder

.. autoclass:: VDFFileSystemTranscluder


Low-Level API
=============

.. autoclass:: VDFDecoder
