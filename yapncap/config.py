import os
import json
from pathlib import Path
from dataclasses import dataclass, asdict

CONFIG_DIR = Path.home() / ".yapncap"
CONFIG_FILE = CONFIG_DIR / "config.json"

@dataclass
class YapnCapConfig:
    language: str = "en"
    provider: str = "gemini"
    api_key: str = ""
    intensity: str = "balanced"

def load_config() -> YapnCapConfig:
    """Loads configuration from ~/.yapncap/config.json and applies env var overrides."""
    config = YapnCapConfig()
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            try:
                data = json.load(f)
                config = YapnCapConfig(**data)
            except Exception:
                pass # Fallback to defaults if corrupt
    
    # Environment variable overrides
    if env_lang := os.getenv("YAPNCAP_LANGUAGE"):
        config.language = env_lang
    if env_prov := os.getenv("YAPNCAP_PROVIDER"):
        config.provider = env_prov
    if env_int := os.getenv("YAPNCAP_INTENSITY"):
        config.intensity = env_int
        
    # Provider-specific API key from env
    env_key_map = {
        "gemini": "GEMINI_API_KEY",
        "openai": "OPENAI_API_KEY",
        "groq": "GROQ_API_KEY"
    }
    if env_key := os.getenv(env_key_map.get(config.provider, "")):
        config.api_key = env_key

    return config

def save_config(config: YapnCapConfig) -> None:
    """Saves configuration to ~/.yapncap/config.json."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(asdict(config), f, indent=2)

def validate_config(config: YapnCapConfig) -> bool:
    """Returns True if the config has all required fields to run."""
    return bool(config.api_key)
