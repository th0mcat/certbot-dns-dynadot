certbot-dns-dynadot
=====================

dynadot_ DNS Authenticator plugin for Certbot

This plugin automates the process of completing a ``dns-01`` challenge by
creating, and subsequently removing, TXT records using the dynadot Remote API.

Configuration of dynadot
---------------------------

In the *Tools* -> *API* -> *Production* *and* *Sandbox* *key* you have to create a
new API key (or reuse existing one).
Use Sandbox key for integration testing of this plugin or Production key for
using it with real domans.
You will acquire an API key and a Secret key. Sandbox credentials begin with
``sandbox_`` prefix.

.. _dynadot: https://www.dynadot.com/
.. _certbot: https://certbot.eff.org/

Installation
------------

::

    pip install certbot-dns-dynadot


Named Arguments
---------------

To start using DNS authentication for dynadot, pass the following arguments on
certbot's command line:

============================================================= ==============================================
``--authenticator dns-dynadot``                               select the authenticator plugin (Required)

``--dns-dynadot-credentials``                                 dynadot Remote User credentials
                                                              INI file. (Required)

``--dns-dynadot-propagation-seconds``                         | waiting time for DNS to propagate before asking
                                                              | the ACME server to verify the DNS record.
                                                              | (Default: 300, Recommended: >= 600)
============================================================= ==============================================


Credentials
-----------

An example ``credentials.ini`` file:

.. code-block:: ini

   dns_dynadot_api_key = your-api-key
   dns_dynadot_secret = your-api-secret

The path to this file can be provided interactively or using the
``--dns-dynadot-credentials`` command-line argument. Certbot
records the path to this file for use during renewal, but does not store the
file's contents.

**CAUTION:** You should protect these API credentials as you would the
password to your dynadot account. Users who can read this file can use these
credentials to issue arbitrary API calls on your behalf. Users who can cause
Certbot to run using these credentials can complete a ``dns-01`` challenge to
acquire new certificates or revoke existing certificates for associated
domains, even if those domains aren't being managed by this server.

Certbot will emit a warning if it detects that the credentials file can be
accessed by other users on your system. The warning reads "Unsafe permissions
on credentials configuration file", followed by the path to the credentials
file. This warning will be emitted each time Certbot uses the credentials file,
including for renewal, and cannot be silenced except by addressing the issue
(e.g., by using a command like ``chmod 600`` to restrict access to the file).


Examples
--------

To acquire a single certificate for both ``example.com`` and
``*.example.com``, waiting 900 seconds for DNS propagation:

.. code-block:: bash

   certbot certonly \
     --authenticator dns-dynadot \
     --dns-dynadot-credentials /etc/letsencrypt/.secrets/domain.tld.ini \
     --dns-dynadot-propagation-seconds 900 \
     --server https://acme-v02.api.letsencrypt.org/directory \
     --agree-tos \
     --rsa-key-size 4096 \
     -d 'example.com' \
     -d '*.example.com'


Docker
------

In order to create a docker container with a certbot-dns-dynadot installation,
create an empty directory with the following ``Dockerfile``:

.. code-block:: docker

    FROM certbot/certbot
    RUN pip install certbot-dns-dynadot

Proceed to build the image::

    docker build -t certbot/dns-dynadot .

Once that's finished, the application can be run as follows::

    docker run --rm \
       -v /var/lib/letsencrypt:/var/lib/letsencrypt \
       -v /etc/letsencrypt:/etc/letsencrypt \
       --cap-drop=all \
       certbot/dns-dynadot certonly \
       --authenticator dns-dynadot \
       --dns-dynadot-propagation-seconds 900 \
       --dns-dynadot-credentials \
           /etc/letsencrypt/.secrets/domain.tld.ini \
       --no-self-upgrade \
       --keep-until-expiring --non-interactive --expand \
       --server https://acme-v02.api.letsencrypt.org/directory \
       -d example.com -d '*.example.com'

It is suggested to secure the folder as follows::

    chown root:root /etc/letsencrypt/.secrets
    chmod 600 /etc/letsencrypt/.secrets
