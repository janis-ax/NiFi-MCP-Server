from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ServerConfig:
	# Transport: stdio (default), http, sse – read at instance creation
	transport: str = field(default_factory=lambda: os.getenv("MCP_TRANSPORT", "stdio"))
	host: str = field(default_factory=lambda: os.getenv("MCP_HOST", "127.0.0.1"))
	port: int = field(default_factory=lambda: int(os.getenv("MCP_PORT", "3030")))

	# Knox + NiFi
	knox_gateway_url: str = field(default_factory=lambda: os.getenv("KNOX_GATEWAY_URL", "") or "")
	nifi_api_base: Optional[str] = field(default_factory=lambda: os.getenv("NIFI_API_BASE"))

	# Auth options
	knox_token: Optional[str] = field(default_factory=lambda: os.getenv("KNOX_TOKEN"))
	knox_cookie: Optional[str] = field(default_factory=lambda: os.getenv("KNOX_COOKIE"))
	knox_user: Optional[str] = field(default_factory=lambda: os.getenv("KNOX_USER"))
	knox_password: Optional[str] = field(default_factory=lambda: os.getenv("KNOX_PASSWORD"))
	knox_token_endpoint: Optional[str] = field(default_factory=lambda: os.getenv("KNOX_TOKEN_ENDPOINT"))
	knox_passcode_token: Optional[str] = field(default_factory=lambda: os.getenv("KNOX_PASSCODE_TOKEN"))

	# Open Source NiFi: HTTP Basic auth (no Knox)
	nifi_user: Optional[str] = field(default_factory=lambda: os.getenv("NIFI_USER"))
	nifi_password: Optional[str] = field(default_factory=lambda: os.getenv("NIFI_PASSWORD"))

	# TLS/HTTP
	verify_ssl_env: str = field(default_factory=lambda: os.getenv("KNOX_VERIFY_SSL", "true").lower())
	ca_bundle: Optional[str] = field(default_factory=lambda: os.getenv("KNOX_CA_BUNDLE"))
	timeout_seconds: int = field(default_factory=lambda: int(os.getenv("HTTP_TIMEOUT_SECONDS", "30")))
	max_retries: int = field(default_factory=lambda: int(os.getenv("HTTP_MAX_RETRIES", "3")))
	rate_limit_rps: float = field(default_factory=lambda: float(os.getenv("HTTP_RATE_LIMIT_RPS", "5")))

	# Behavior
	readonly: bool = field(default_factory=lambda: os.getenv("NIFI_READONLY", "true").lower() == "true")
	allowed_actions_csv: str = field(default_factory=lambda: os.getenv("NIFI_ALLOWED_ACTIONS", ""))

	# CDP-specific proxy headers
	proxy_context_path: Optional[str] = field(default_factory=lambda: os.getenv("NIFI_PROXY_CONTEXT_PATH"))

	def build_verify(self) -> bool | str:
		if self.ca_bundle:
			return self.ca_bundle
		return self.verify_ssl_env not in {"0", "false", "no"}

	def build_nifi_base(self) -> str:
		if self.nifi_api_base:
			return self.nifi_api_base.rstrip("/")
		if not self.knox_gateway_url:
			raise ValueError("KNOX_GATEWAY_URL or NIFI_API_BASE must be set")
		return f"{self.knox_gateway_url.rstrip('/')}/nifi-api"


