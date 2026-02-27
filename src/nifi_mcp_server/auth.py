from __future__ import annotations

import base64
from typing import Optional

import requests

try:
	from .logging_config import get_logger
except ImportError:
	def get_logger(name: str):
		import logging
		return logging.getLogger(f"nifi_mcp_server.{name}")

_log = get_logger("auth")


def _fetch_token_manual(base_url: str, user: str, password: str, verify: bool | str) -> str:
	"""
	Try both NiFi token endpoints:
	1) POST /access/token with form (username, password) – used by single-user auth.
	2) POST /access/token/login with Basic Auth – used by LDAP/other providers.
	"""
	base = base_url.rstrip("/")
	headers = {"X-Requested-By": "nifi-mcp-server"}

	# 1) Single-user auth: POST /access/token with form body (curl -d "username=...&password=...")
	_log.debug("trying POST %s/access/token (form)", base)
	r = requests.post(
		f"{base}/access/token",
		data={"username": user, "password": password},
		headers=headers,
		verify=verify,
		timeout=15,
	)
	if r.ok:
		token = (r.text or "").strip()
		if token:
			_log.info("token from /access/token (single-user)")
			return token
		raise ValueError("NiFi /access/token returned empty body")
	if r.status_code == 401:
		_log.warning("NiFi /access/token returned 401 (invalid credentials)")
		raise ValueError("NiFi rejected credentials (401). Check NIFI_USER and NIFI_PASSWORD.")
	if r.status_code not in (400, 404):
		r.raise_for_status()
	_log.debug("/access/token returned %s, trying /access/token/login", r.status_code)

	# 2) LDAP etc.: POST /access/token/login with Basic Auth
	credentials_b64 = base64.b64encode(f"{user}:{password}".encode()).decode("ascii")
	headers["Authorization"] = f"Basic {credentials_b64}"
	_log.debug("trying POST %s/access/token/login (Basic Auth)", base)
	r = requests.post(f"{base}/access/token/login", headers=headers, verify=verify, timeout=15)
	if r.ok:
		token = (r.text or "").strip()
		if token:
			_log.info("token from /access/token/login (LDAP/Basic)")
			return token
		raise ValueError("NiFi /access/token/login returned empty body")
	if r.status_code == 401:
		_log.warning("NiFi /access/token/login returned 401 (invalid credentials)")
		raise ValueError("NiFi rejected credentials (401). Check NIFI_USER and NIFI_PASSWORD.")
	r.raise_for_status()
	raise ValueError("NiFi token login failed (no token from /access/token or /access/token/login)")


class NiFiTokenSession:
	"""
	Session-like wrapper that refreshes the NiFi JWT on 401 and retries the request once.
	Exposes .get, .put, .post, .delete and .headers, .verify for use by NiFiClient.
	"""
	def __init__(self, base_url: str, user: str, password: str, verify: bool | str):
		self._base_url = base_url.rstrip("/")
		self._user = (user or "").strip()
		self._password = (password or "").strip()
		self._verify = verify
		self._session = requests.Session()
		self._session.verify = verify
		self._session.headers["X-Requested-By"] = "nifi-mcp-server"
		self._set_token(_fetch_token_manual(self._base_url, self._user, self._password, verify))

	def _set_token(self, token: str) -> None:
		self._session.headers["Authorization"] = f"Bearer {token}"

	def _refresh_and_retry(self, method: str, url: str, **kwargs):  # noqa: ANN001
		_log.info("Token refreshed after 401, retrying request")
		self._set_token(_fetch_token_manual(self._base_url, self._user, self._password, self._verify))
		return self._session.request(method, url, **kwargs)

	@property
	def headers(self):
		return self._session.headers

	@property
	def verify(self):
		return self._session.verify

	def get(self, url: str, **kwargs):  # noqa: ANN001
		r = self._session.get(url, **kwargs)
		if r.status_code == 401:
			r = self._refresh_and_retry("GET", url, **kwargs)
		return r

	def put(self, url: str, **kwargs):  # noqa: ANN001
		r = self._session.put(url, **kwargs)
		if r.status_code == 401:
			r = self._refresh_and_retry("PUT", url, **kwargs)
		return r

	def post(self, url: str, **kwargs):  # noqa: ANN001
		r = self._session.post(url, **kwargs)
		if r.status_code == 401:
			r = self._refresh_and_retry("POST", url, **kwargs)
		return r

	def delete(self, url: str, **kwargs):  # noqa: ANN001
		r = self._session.delete(url, **kwargs)
		if r.status_code == 401:
			r = self._refresh_and_retry("DELETE", url, **kwargs)
		return r


def build_nifi_token_session(
	base_url: str,
	user: str,
	password: str,
	verify: bool | str = True,
) -> NiFiTokenSession:
	"""
	Build a session for Open Source NiFi using token login. Returns a NiFiTokenSession
	that refreshes the JWT on 401 and retries once. Uses POST /access/token or
	/access/token/login.
	"""
	user = (user or "").strip()
	password = (password or "").strip()
	if not user or not password:
		raise ValueError("NIFI_USER and NIFI_PASSWORD must be non-empty (check env is passed to the process)")
	return NiFiTokenSession(base_url, user, password, verify)


def build_basic_auth_session(
	user: str,
	password: str,
	verify: bool | str = True,
) -> requests.Session:
	"""Build a requests Session with HTTP Basic auth for Open Source NiFi.
	Prefer build_nifi_token_session() when NiFi returns 401 – NiFi typically expects token login."""
	session = requests.Session()
	session.auth = (user, password)
	session.verify = verify
	session.headers["X-Requested-By"] = "nifi-mcp-server"
	credentials = base64.b64encode(f"{user}:{password}".encode()).decode("ascii")
	session.headers["Authorization"] = f"Basic {credentials}"
	return session


def build_no_auth_session(verify: bool | str = True) -> requests.Session:
	"""Build a requests Session with no auth (e.g. dev NiFi without login)."""
	session = requests.Session()
	session.verify = verify
	session.headers["X-Requested-By"] = "nifi-mcp-server"
	return session


class KnoxAuthFactory:
	def __init__(
		self,
		gateway_url: str,
		token: Optional[str],
		cookie: Optional[str],
		user: Optional[str],
		password: Optional[str],
		token_endpoint: Optional[str],
		passcode_token: Optional[str],
		verify: bool | str,
	):
		self.gateway_url = gateway_url.rstrip("/") if gateway_url else ""
		self.token = token
		self.cookie = cookie
		self.user = user
		self.password = password
		self.token_endpoint = token_endpoint or (
			f"{self.gateway_url}/knoxtoken/api/v1/token" if self.gateway_url else None
		)
		self.passcode_token = passcode_token
		self.verify = verify

	def build_session(self) -> requests.Session:
		session = requests.Session()
		session.verify = self.verify

		# Priority: Explicit Cookie -> Knox token (as cookie for CDP) -> Passcode token -> Basic creds token exchange
		if self.cookie:
			session.headers["Cookie"] = self.cookie
			return session
		
		if self.token:
			# For CDP NiFi, Knox JWT tokens must be sent as cookies, not Bearer headers
			session.headers["Cookie"] = f"hadoop-jwt={self.token}"
			return session


		if self.passcode_token:
			# Prefer exchanging passcode for JWT via knoxtoken endpoint when available
			if self.token_endpoint:
				jwt = self._exchange_passcode_for_jwt()
				session.headers["Authorization"] = f"Bearer {jwt}"
				return session
			# Fallback: send passcode as header (may not work on all deployments)
			session.headers["X-Knox-Passcode"] = self.passcode_token
			return session

		if self.user and self.password and self.token_endpoint:
			jwt = self._fetch_knox_token()
			session.headers["Authorization"] = f"Bearer {jwt}"
			return session

		return session

	def _fetch_knox_token(self) -> str:
		# Default Knox token endpoint returns raw JWT or JSON with token fields
		resp = requests.get(
			self.token_endpoint,
			auth=(self.user, self.password),
			verify=self.verify,
			timeout=15,
		)
		resp.raise_for_status()
		try:
			data = resp.json()
			return data.get("access_token") or data.get("token") or data.get("accessToken")
		except ValueError:
			text = resp.text.strip()
			# Some envs return Base64-encoded token; detect and decode if needed
			try:
				decoded = base64.b64decode(text).decode("utf-8")
				if decoded.count(".") == 2:
					return decoded
			except Exception:
				pass
			return text

	def _exchange_passcode_for_jwt(self) -> str:
		"""Exchange Knox passcode token for JWT using Basic auth pattern passcode:<token>."""
		if not (self.passcode_token and self.token_endpoint):
			raise RuntimeError("Passcode token exchange requires token_endpoint and passcode token")
		import base64
		header = {
			"Authorization": "Basic " + base64.b64encode(f"passcode:{self.passcode_token}".encode()).decode(),
			"X-Requested-By": "nifi-mcp-server",
		}
		resp = requests.get(self.token_endpoint, headers=header, verify=self.verify, timeout=15)
		resp.raise_for_status()
		try:
			data = resp.json()
			return data.get("access_token") or data.get("token") or data.get("accessToken")
		except ValueError:
			return resp.text.strip()


