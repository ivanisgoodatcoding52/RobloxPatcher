"""
Configuration module for the Roblox Revival Creator.
"""
import json
import os
from dataclasses import asdict, dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Set


class ClientType(Enum):
    """Represents the different types of Roblox clients."""
    PLAYER = auto()
    STUDIO = auto()
    RCC_SERVICE = auto()
    
    def __str__(self) -> str:
        return self.name.replace('_', ' ').title()


class PatchType(Enum):
    """Represents the different types of patches available."""
    WEBSITE = auto()
    PUBLIC_KEY = auto()
    BLOCKING = auto()
    INVALID_REQUEST = auto()
    TRUST_CHECK = auto()
    RATNET_KEY = auto()
    HTML_SERVICE = auto()
    
    def __str__(self) -> str:
        return self.name.replace('_', ' ').title()


@dataclass
class PatchConfig:
    """Configuration for a patch operation."""
    client_path: str = ""
    website_domain: str = ""
    version_year: int = 2010
    client_type: ClientType = ClientType.PLAYER
    patches: Set[PatchType] = field(default_factory=set)
    rbxsigtools_path: str = ""
    x64dbg_path: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to a dictionary for serialization."""
        result = asdict(self)
        result['client_type'] = self.client_type.name
        result['patches'] = [p.name for p in self.patches]
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PatchConfig':
        """Create a PatchConfig from a dictionary."""
        config = cls()
        config.client_path = data.get('client_path', "")
        config.website_domain = data.get('website_domain', "")
        config.version_year = data.get('version_year', 2010)
        
        # Convert client_type string to enum
        client_type_str = data.get('client_type', ClientType.PLAYER.name)
        config.client_type = ClientType[client_type_str]
        
        # Convert patches list to set of enums
        patches_list = data.get('patches', [])
        config.patches = {PatchType[name] for name in patches_list}
        
        config.rbxsigtools_path = data.get('rbxsigtools_path', "")
        config.x64dbg_path = data.get('x64dbg_path', "")
        
        return config


@dataclass
class AppConfig:
    """Application configuration."""
    recent_configs: List[str] = field(default_factory=list)
    default_save_dir: str = ""
    dark_mode: bool = False
    config_file_path: str = field(default="config.json", init=False)
    
    def __post_init__(self):
        """Initialize after construction."""
        self.config_file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "config.json"
        )
        self.load()
    
    def load(self) -> None:
        """Load configuration from file."""
        if os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, 'r') as f:
                    data = json.load(f)
                    self.recent_configs = data.get('recent_configs', [])
                    self.default_save_dir = data.get('default_save_dir', "")
                    self.dark_mode = data.get('dark_mode', False)
            except Exception:
                # If loading fails, use defaults
                pass
    
    def save(self) -> None:
        """Save configuration to file."""
        data = {
            'recent_configs': self.recent_configs,
            'default_save_dir': self.default_save_dir,
            'dark_mode': self.dark_mode
        }
        
        with open(self.config_file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_recent_config(self, config_path: str) -> None:
        """Add a config file to recent configs list."""
        if config_path in self.recent_configs:
            self.recent_configs.remove(config_path)
        
        self.recent_configs.insert(0, config_path)
        
        # Keep only the 5 most recent
        self.recent_configs = self.recent_configs[:5]
        self.save()