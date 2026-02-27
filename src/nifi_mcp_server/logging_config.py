"""Central logging setup for nifi_mcp_server. LOG_LEVEL and LOG_FORMAT from env."""
from __future__ import annotations

import logging
import os

LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
LOG_FORMATS = ("human", "json")

def get_log_level() -> str:
	raw = (os.getenv("LOG_LEVEL") or "INFO").strip().upper()
	return raw if raw in LOG_LEVELS else "INFO"

def get_log_format() -> str:
	raw = (os.getenv("LOG_FORMAT") or "human").strip().lower()
	return raw if raw in LOG_FORMATS else "human"

def configure_logging() -> None:
	level = get_log_level()
	logging.basicConfig(
		level=getattr(logging, level),
		format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
		datefmt="%Y-%m-%d %H:%M:%S",
	)
	logger = logging.getLogger("nifi_mcp_server")
	logger.setLevel(getattr(logging, level))

def get_logger(name: str) -> logging.Logger:
	return logging.getLogger(f"nifi_mcp_server.{name}" if not name.startswith("nifi_mcp_server") else name)
