"""
Website patcher implementation.
"""
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from config import PatchConfig
from patchers.base_patcher import BasePatcher


class WebsitePatcher(BasePatcher):
    """Patcher for changing website domains in the client."""
    
    def validate(self) -> bool:
        """
        Validate that the configuration has all required elements for this patch.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if not self.client_path.exists():
            self.logger.error(f"Client file not found: {self.client_path}")
            return False
        
        if len(self.config.website_domain) != 10:
            self.logger.error(f"Website domain must be exactly 10 characters: '{self.config.website_domain}'")
            return False
        
        return True
    
    def apply(self) -> bool:
        """
        Apply the website patch to the client.
        
        Returns:
            True if patching was successful, False otherwise
        """
        if not self.validate():
            return False
        
        try:
            # Create backup first
            if not self.backup_client():
                return False
            
            # Replace 'roblox.com' with the new domain in the binary
            with open(self.client_path, 'rb') as file:
                content = file.read()
            
            modified_content = content.replace(b'roblox.com', self.config.website_domain.encode())
            
            with open(self.client_path, 'wb') as file:
                file.write(modified_content)
            
            # Check if we need to create/update AppSettings.xml
            self._update_app_settings()
            
            self.logger.info("Website patch applied successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error applying website patch: {e}")
            return False
    
    def _update_app_settings(self) -> None:
        """Update or create the AppSettings.xml file."""
        app_settings_path = self.client_path.parent / "AppSettings.xml"
        
        if not app_settings_path.exists():
            # Create a new AppSettings.xml file
            xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Settings>
<ContentFolder>content</ContentFolder>
<BaseUrl>http://www.{self.config.website_domain}</BaseUrl>
</Settings>
"""
            with open(app_settings_path, 'w') as file:
                file.write(xml_content)
            
            self.logger.info(f"Created new AppSettings.xml at: {app_settings_path}")
        else:
            # Update existing AppSettings.xml
            try:
                tree = ET.parse(app_settings_path)
                root = tree.getroot()
                base_url_elem = root.find('BaseUrl')
                
                if base_url_elem is not None:
                    base_url_elem.text = f"http://www.{self.config.website_domain}"
                else:
                    base_url_elem = ET.SubElement(root, 'BaseUrl')
                    base_url_elem.text = f"http://www.{self.config.website_domain}"
                
                tree.write(app_settings_path)
                self.logger.info(f"Updated BaseUrl in AppSettings.xml to: http://www.{self.config.website_domain}")
            except Exception as e:
                self.logger.error(f"Error updating AppSettings.xml: {e}")