from typing import cast

from certbot import errors
from certbot.plugins.dns_common import CredentialsConfiguration, DNSAuthenticator

from .client import DynadotClient


class Authenticator(DNSAuthenticator):
    description = "Obtain certificates using Dynadot DNS"

    credentials: CredentialsConfiguration
    client: DynadotClient

    @classmethod
    def add_parser_arguments(cls, add, default_propagation_seconds=30):
        super().add_parser_arguments(
            add, default_propagation_seconds=default_propagation_seconds
        )
        add("credentials", help="Dynadot API credentials file")

    def more_info(self):
        return "This plugin configures DNS TXT records via Dynadot REST API."

    def _setup_credentials(self):
        self.credentials = self._configure_credentials(
            "credentials",
            "Dynadot credentials file",
            {"api_key": "Dynadot API key", "secret": "Dynadot API secret"},
            self._validate_credentials,
        )

        self.client = DynadotClient(
            api_key=cast(str, self.credentials.conf("api_key")),
            secret=cast(str, self.credentials.conf("secret")),
        )

    def _validate_credentials(self, credentials: CredentialsConfiguration) -> None:
        api_key = credentials.conf("api_key")
        secret = credentials.conf("secret")
        if not api_key:
            raise errors.PluginError(
                "{}: dns_dynadot_api_key is required.".format(
                    credentials.confobj.filename
                )
            )
        if not secret:
            raise errors.PluginError(
                "{}: dns_dynadot_secret is required".format(
                    credentials.confobj.filename
                )
            )

        if (api_key.startswith("sandbox_") and not secret.startswith("sandbox_")) or (
            not api_key.startswith("sandbox_") and secret.startswith("sandbox_")
        ):
            raise errors.PluginError(
                "{}: Either dns_dynadot_api_key, or dns_dynadot_secret is for sandbox and other one is for production.".format(
                    credentials.confobj.filename
                )
            )

    def _perform(self, domain: str, validation_name: str, validation: str):
        try:
            self.client.add_txt_record(validation_name, validation)
        except Exception as e:
            raise errors.PluginError(f"Failed to add TXT record: {e}") from e

    def _cleanup(self, domain: str, validation_name: str, validation: str):
        try:
            self.client.remove_txt_record(validation_name, validation)
        except Exception as e:
            raise errors.PluginError(f"Failed to cleanup TXT record: {e}") from e
