import base64
import hmac
import json
from functools import cache
from itertools import chain
from typing import Any, Literal
from uuid import uuid4

import requests
from certbot import errors
from certbot.errors import PluginError
from certbot.plugins.dns_common import base_domain_name_guesses


class DynadotClient:
    api_key: str
    secret: str
    base_url: str
    base_path: str = "/restful/v2"

    def __init__(self, api_key: str, secret: str):
        self.api_key = api_key
        self.secret = secret
        self.base_url = (
            "https://api-sandbox.dynadot.com"
            if api_key.startswith("sandbox_")
            else "https://api.dynadot.com"
        )

    def _api_request(
        self,
        method: Literal["get", "post", "put", "delete"],
        resource: str,
        res_id: str | None = None,
        action: str | None = None,
        data: dict[str, Any] | None = None,
    ):
        path: str = "/".join(filter(None, (self.base_path, resource, res_id, action)))

        headers = {
            "Accept": "application/json",
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json",
            "X-Request-ID": str(uuid4()),
        }
        body = "" if method in ("get", "delete") else json.dumps(data)

        headers["X-Signature"] = base64.standard_b64encode(
            hmac.new(
                self.secret.encode(),
                "\n".join([self.api_key, path, headers["X-Request-ID"], body]).encode(),
                "sha256",
            ).digest()
        ).decode()

        response: requests.Response = requests.request(
            method, self.base_url + path, headers=headers, data=body.encode()
        )
        data = response.json()

        if data.get("code") >= 400:
            raise errors.PluginError(f"Dynadot API error: {data}")

        return data

    @cache
    def get_domains_list(self) -> set[str]:
        domains: list[dict[str, Any]] = self._api_request("get", "domains")["data"][
            "domain_info"
        ]
        return {d["domain_name"] for d in domains}

    @cache
    def get_dns(self, domain):
        return self._api_request("get", "domains", domain, "records")["data"][
            "name_server_settings"
        ]

    def set_dns(self, domain, records, sub_records):
        params = {"dns_main_list": records, "sub_list": sub_records}
        return self._api_request("post", "domains", domain, "records", params)

    def add_txt_record(self, fqdn: str, value: str):
        subdomain, domain = self._extract_domain(fqdn)

        ns_settings = self.get_dns(domain)

        if domain == fqdn:
            records = ns_settings.get("main_domains", [])
            match = ("txt", value, None)
        else:
            records = ns_settings.get("sub_domains", [])
            match = ("txt", value, subdomain)

        # verify we don't have record with value already added
        for item in records:
            if (item["record_type"], item["value"], item.get("sub_host")) == match:
                return

        self._rename_value_fields(ns_settings)

        new_record = {
            "record_type": "txt",
            "record_value1": value,
        }

        if domain == fqdn:
            ns_settings.setdefault("main_domains", []).append(new_record)
        else:
            ns_settings.setdefault("sub_domains", []).append(
                new_record | {"sub_host": subdomain}
            )

        self.set_dns(
            domain,
            ns_settings.get("main_domains", []),
            ns_settings.get("sub_domains", []),
        )
        self.get_dns.cache_clear()

    def remove_txt_record(self, fqdn, value):
        subdomain, domain = self._extract_domain(fqdn)

        ns_settings = self.get_dns(domain)

        if domain == fqdn:
            match = {"record_type": "txt", "value": value}
            ns_settings["main_domains"] = [
                item for item in ns_settings.get("main_domains", []) if item != match
            ]
        else:
            match = {"record_type": "txt", "value": value, "sub_host": subdomain}
            ns_settings["sub_domains"] = [
                item for item in ns_settings.get("sub_domains", []) if item != match
            ]

        self._rename_value_fields(ns_settings)

        self.set_dns(
            domain,
            ns_settings.get("main_domains", []),
            ns_settings.get("sub_domains", []),
        )
        self.get_dns.cache_clear()

    def _extract_domain(self, fqdn) -> tuple[str, str]:
        guesses = base_domain_name_guesses(fqdn)
        domain = next(iter(d for d in guesses if d in self.get_domains_list()), None)
        if not domain:
            raise PluginError(f"Failed to extract base domain from {fqdn}")
        return fqdn[: -len(domain) - 1], domain

    def _rename_value_fields(self, dns_response):
        # Dynadot returns values as 'value' and expects them as 'record_value1'

        for item in chain(
            dns_response.get("main_domains", []), dns_response.get("sub_domains", [])
        ):
            value = item.pop("value", None)
            if value is not None:
                item["record_value1"] = value
