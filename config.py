"""Configuration management for queuectl."""

import json
from pathlib import Path
from typing import Any, Optional


class ConfigManager:
    """Manage configuration in JSON file."""
    
    def __init__(self, config_file: str = "queuectl_config.json"):
        """Initialize config manager."""
        self.config_file = Path(config_file)
        self.default_config = {
            "max_retries": 3,
            "backoff_base": 2,
        }
        self._ensure_config_file()
    
    def _ensure_config_file(self) -> None:
        """Ensure config file exists with default values."""
        if not self.config_file.exists():
            self._write_config(self.default_config)
        else:
            # Merge with defaults to ensure all keys exist
            current = self._read_config()
            merged = {**self.default_config, **current}
            self._write_config(merged)
    
    def _read_config(self) -> dict:
        """Read configuration from file."""
        try:
            with open(self.config_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return self.default_config.copy()
    
    def _write_config(self, config: dict) -> None:
        """Write configuration to file."""
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        config = self._read_config()
        return config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        config = self._read_config()
        config[key] = value
        self._write_config(config)
    
    def get_all(self) -> dict:
        """Get all configuration values."""
        return self._read_config()

