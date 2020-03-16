make-plone-qrcode
=================

Create a QR code and inject the Plone logo.

The whole heavy-lifting rocket science of creating a QR code and formatting it
as an SVG image is done by the pyqrcode_ package.
In this image the Plone logo is injected, covering the centre of the code.

Since QR codes can contain enough error correction data to be readable
even if up to 30% of the data is covered,
the resulting image should still be usable.
This little tool doesn't guarantee this; you'll need to test the resulting
image with a QR Code scanner, e.g. an app on your smartphone, and - if
necessary - reduce the size of the logo.

.. _pyqrcode: https://pypi.org/project/pyqrcode

.. vim: sw=2 sts=2 si et tw=79 cc=+1
