"""
Secure Credential Management for TraderTerminal

Provides cross-platform secure storage for API keys and secrets using:
- macOS: Keychain Services  
- Linux: libsecret/GNOME Keyring or encrypted file storage
- Windows: Windows Credential Store (future support)

Falls back to encrypted file storage when native keyring is unavailable.
"""

import os
import sys
import json
import platform
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import getpass

try:
    import keyring
    import keyring.backends.SecretService
    import keyring.backends.macOS
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

logger = logging.getLogger(__name__)


class CredentialManagerError(Exception):
    """Base exception for credential manager errors"""
    pass


class CredentialNotFoundError(CredentialManagerError):
    """Raised when a credential is not found"""
    pass


class SecureCredentialManager:
    """
    Cross-platform secure credential management system
    
    Uses native keyring services when available, falls back to encrypted file storage.
    """
    
    SERVICE_NAME = "TraderTerminal"
    ENCRYPTED_FILE_NAME = "trader_credentials.enc"
    
    def __init__(self, use_keyring: bool = True, encryption_key: Optional[str] = None):
        """
        Initialize credential manager
        
        Args:
            use_keyring: Whether to use native keyring (default: True)
            encryption_key: Custom encryption key for file storage (optional)
        """
        self.platform = platform.system()
        self.use_keyring = use_keyring and KEYRING_AVAILABLE
        self.encryption_key = encryption_key
        self._cipher = None
        
        # Determine storage backend
        self._setup_backend()
        
        logger.info(f"Credential manager initialized: platform={self.platform}, "
                   f"keyring={self.use_keyring}, backend={self.backend_type}")
    
    def _setup_backend(self):
        """Setup appropriate credential storage backend"""
        if self.use_keyring:
            try:
                # Test keyring availability
                keyring.get_keyring()
                self.backend_type = "keyring"
                logger.info(f"Using native keyring: {keyring.get_keyring().__class__.__name__}")
                return
            except Exception as e:
                logger.warning(f"Keyring unavailable: {e}")
        
        # Fallback to encrypted file storage
        self.backend_type = "encrypted_file"
        self._setup_file_encryption()
        logger.info("Using encrypted file storage")
    
    def _setup_file_encryption(self):
        """Setup encryption for file-based storage"""
        if self.encryption_key:
            # Use provided key
            key = self.encryption_key.encode()
        else:
            # Derive key from system information and user password
            key = self._derive_encryption_key()
        
        # Create Fernet cipher
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'traderterminal_salt',  # Static salt for consistency
            iterations=100000,
        )
        
        fernet_key = base64.urlsafe_b64encode(kdf.derive(key))
        self._cipher = Fernet(fernet_key)
    
    def _derive_encryption_key(self) -> bytes:
        """Derive encryption key from system and user information"""
        # Get system-specific identifier
        if self.platform == "Darwin":  # macOS
            import subprocess
            try:
                # Use hardware UUID
                result = subprocess.run(['system_profiler', 'SPHardwareDataType'], 
                                      capture_output=True, text=True)
                system_id = result.stdout
            except:
                system_id = platform.node()
        elif self.platform == "Linux":
            try:
                # Use machine ID
                with open('/etc/machine-id', 'r') as f:
                    system_id = f.read().strip()
            except:
                system_id = platform.node()
        else:
            system_id = platform.node()
        
        # Combine with username for uniqueness
        unique_string = f"{system_id}:{getpass.getuser()}:traderterminal"
        return unique_string.encode()
    
    def _get_credentials_file_path(self) -> Path:
        """Get path to encrypted credentials file"""
        if self.platform == "Darwin":
            # macOS: ~/Library/Application Support/TraderTerminal/
            base_dir = Path.home() / "Library" / "Application Support" / "TraderTerminal"
        elif self.platform == "Linux":
            # Linux: ~/.local/share/traderterminal/
            base_dir = Path.home() / ".local" / "share" / "traderterminal"
        else:
            # Fallback: ~/.traderterminal/
            base_dir = Path.home() / ".traderterminal"
        
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir / self.ENCRYPTED_FILE_NAME
    
    async def store_credential(self, key: str, value: str, account: str = "default") -> bool:
        """
        Store a credential securely
        
        Args:
            key: Credential identifier (e.g., 'tastytrade_client_secret')
            value: Credential value
            account: Account namespace (default: 'default')
            
        Returns:
            True if stored successfully
        """
        try:
            credential_id = f"{account}:{key}"
            
            if self.backend_type == "keyring":
                keyring.set_password(self.SERVICE_NAME, credential_id, value)
            else:
                await self._store_to_encrypted_file(credential_id, value)
            
            logger.debug(f"Stored credential: {credential_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store credential {key}: {e}")
            raise CredentialManagerError(f"Failed to store credential: {e}")
    
    async def get_credential(self, key: str, account: str = "default") -> Optional[str]:
        """
        Retrieve a credential
        
        Args:
            key: Credential identifier
            account: Account namespace (default: 'default')
            
        Returns:
            Credential value or None if not found
        """
        try:
            credential_id = f"{account}:{key}"
            
            if self.backend_type == "keyring":
                value = keyring.get_password(self.SERVICE_NAME, credential_id)
            else:
                value = await self._get_from_encrypted_file(credential_id)
            
            if value is None:
                logger.debug(f"Credential not found: {credential_id}")
                return None
            
            logger.debug(f"Retrieved credential: {credential_id}")
            return value
            
        except Exception as e:
            logger.error(f"Failed to retrieve credential {key}: {e}")
            return None
    
    async def delete_credential(self, key: str, account: str = "default") -> bool:
        """
        Delete a credential
        
        Args:
            key: Credential identifier
            account: Account namespace
            
        Returns:
            True if deleted successfully
        """
        try:
            credential_id = f"{account}:{key}"
            
            if self.backend_type == "keyring":
                keyring.delete_password(self.SERVICE_NAME, credential_id)
            else:
                await self._delete_from_encrypted_file(credential_id)
            
            logger.debug(f"Deleted credential: {credential_id}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to delete credential {key}: {e}")
            return False
    
    async def list_credentials(self, account: str = "default") -> List[str]:
        """
        List all stored credential keys for an account
        
        Args:
            account: Account namespace
            
        Returns:
            List of credential keys
        """
        try:
            if self.backend_type == "keyring":
                # Keyring doesn't support listing, return empty list
                return []
            else:
                return await self._list_from_encrypted_file(account)
                
        except Exception as e:
            logger.error(f"Failed to list credentials: {e}")
            return []
    
    async def _store_to_encrypted_file(self, credential_id: str, value: str):
        """Store credential in encrypted file"""
        file_path = self._get_credentials_file_path()
        
        # Load existing data
        data = {}
        if file_path.exists():
            try:
                with open(file_path, 'rb') as f:
                    encrypted_data = f.read()
                    decrypted_data = self._cipher.decrypt(encrypted_data)
                    data = json.loads(decrypted_data.decode())
            except Exception as e:
                logger.warning(f"Could not read existing credentials file: {e}")
        
        # Add new credential
        data[credential_id] = {
            "value": value,
            "created": datetime.utcnow().isoformat(),
            "accessed": datetime.utcnow().isoformat()
        }
        
        # Encrypt and save
        json_data = json.dumps(data).encode()
        encrypted_data = self._cipher.encrypt(json_data)
        
        with open(file_path, 'wb') as f:
            f.write(encrypted_data)
        
        # Set secure permissions (owner read/write only)
        os.chmod(file_path, 0o600)
    
    async def _get_from_encrypted_file(self, credential_id: str) -> Optional[str]:
        """Retrieve credential from encrypted file"""
        file_path = self._get_credentials_file_path()
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()
                decrypted_data = self._cipher.decrypt(encrypted_data)
                data = json.loads(decrypted_data.decode())
            
            if credential_id in data:
                # Update access time
                data[credential_id]["accessed"] = datetime.utcnow().isoformat()
                
                # Save updated data
                json_data = json.dumps(data).encode()
                encrypted_data = self._cipher.encrypt(json_data)
                with open(file_path, 'wb') as f:
                    f.write(encrypted_data)
                
                return data[credential_id]["value"]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to read encrypted credentials: {e}")
            return None
    
    async def _delete_from_encrypted_file(self, credential_id: str):
        """Delete credential from encrypted file"""
        file_path = self._get_credentials_file_path()
        
        if not file_path.exists():
            return
        
        try:
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()
                decrypted_data = self._cipher.decrypt(encrypted_data)
                data = json.loads(decrypted_data.decode())
            
            if credential_id in data:
                del data[credential_id]
                
                # Save updated data
                json_data = json.dumps(data).encode()
                encrypted_data = self._cipher.encrypt(json_data)
                with open(file_path, 'wb') as f:
                    f.write(encrypted_data)
            
        except Exception as e:
            logger.error(f"Failed to delete from encrypted credentials: {e}")
    
    async def _list_from_encrypted_file(self, account: str) -> List[str]:
        """List credentials from encrypted file"""
        file_path = self._get_credentials_file_path()
        
        if not file_path.exists():
            return []
        
        try:
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()
                decrypted_data = self._cipher.decrypt(encrypted_data)
                data = json.loads(decrypted_data.decode())
            
            # Filter by account and return keys
            account_prefix = f"{account}:"
            keys = []
            for credential_id in data.keys():
                if credential_id.startswith(account_prefix):
                    key = credential_id[len(account_prefix):]
                    keys.append(key)
            
            return keys
            
        except Exception as e:
            logger.error(f"Failed to list encrypted credentials: {e}")
            return []
    
    async def migrate_from_env_file(self, env_file_path: str, account: str = "default") -> Dict[str, bool]:
        """
        Migrate credentials from .env file to secure storage
        
        Args:
            env_file_path: Path to .env file
            account: Account namespace for storage
            
        Returns:
            Dictionary of migration results per key
        """
        results = {}
        
        try:
            if not os.path.exists(env_file_path):
                raise FileNotFoundError(f"Environment file not found: {env_file_path}")
            
            with open(env_file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse key=value
                    if '=' not in line:
                        logger.warning(f"Invalid line {line_num} in {env_file_path}: {line}")
                        continue
                    
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")  # Remove quotes
                    
                    # Only migrate sensitive keys (API keys, secrets, passwords)
                    if any(sensitive in key.lower() for sensitive in 
                          ['api_key', 'secret', 'password', 'token', 'credentials']):
                        
                        try:
                            success = await self.store_credential(key, value, account)
                            results[key] = success
                            if success:
                                logger.info(f"Migrated credential: {key}")
                        except Exception as e:
                            logger.error(f"Failed to migrate {key}: {e}")
                            results[key] = False
            
            logger.info(f"Migration complete: {sum(results.values())}/{len(results)} credentials migrated")
            return results
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise CredentialManagerError(f"Migration failed: {e}")
    
    async def export_credentials(self, account: str = "default", include_values: bool = False) -> Dict[str, Any]:
        """
        Export credentials for backup or debugging
        
        Args:
            account: Account namespace
            include_values: Whether to include credential values (default: False)
            
        Returns:
            Dictionary of credential information
        """
        try:
            keys = await self.list_credentials(account)
            export_data = {
                "account": account,
                "backend": self.backend_type,
                "platform": self.platform,
                "exported_at": datetime.utcnow().isoformat(),
                "credentials": {}
            }
            
            for key in keys:
                credential_info = {"key": key}
                
                if include_values:
                    value = await self.get_credential(key, account)
                    credential_info["value"] = value
                else:
                    credential_info["value"] = "***HIDDEN***"
                
                export_data["credentials"][key] = credential_info
            
            return export_data
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise CredentialManagerError(f"Export failed: {e}")
    
    async def test_storage(self) -> Dict[str, Any]:
        """
        Test credential storage functionality
        
        Returns:
            Test results
        """
        test_key = "test_credential"
        test_value = "test_value_123"
        test_account = "test_account"
        
        results = {
            "platform": self.platform,
            "backend": self.backend_type,
            "keyring_available": KEYRING_AVAILABLE,
            "store_test": False,
            "retrieve_test": False,
            "delete_test": False
        }
        
        try:
            # Test store
            store_success = await self.store_credential(test_key, test_value, test_account)
            results["store_test"] = store_success
            
            if store_success:
                # Test retrieve
                retrieved_value = await self.get_credential(test_key, test_account)
                results["retrieve_test"] = retrieved_value == test_value
                
                # Test delete
                delete_success = await self.delete_credential(test_key, test_account)
                results["delete_test"] = delete_success
                
                # Verify deletion
                deleted_value = await self.get_credential(test_key, test_account)
                results["delete_verification"] = deleted_value is None
        
        except Exception as e:
            results["error"] = str(e)
            logger.error(f"Storage test failed: {e}")
        
        return results


# Singleton instance for global use
_credential_manager: Optional[SecureCredentialManager] = None


def get_credential_manager() -> SecureCredentialManager:
    """Get the global credential manager instance"""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = SecureCredentialManager()
    return _credential_manager


async def get_api_credential(key: str, account: str = "default") -> Optional[str]:
    """
    Convenience function to get an API credential
    
    Args:
        key: Credential key (e.g., 'tastytrade_client_secret')
        account: Account namespace
        
    Returns:
        Credential value or None
    """
    manager = get_credential_manager()
    return await manager.get_credential(key, account)


async def store_api_credential(key: str, value: str, account: str = "default") -> bool:
    """
    Convenience function to store an API credential
    
    Args:
        key: Credential key
        value: Credential value
        account: Account namespace
        
    Returns:
        True if stored successfully
    """
    manager = get_credential_manager()
    return await manager.store_credential(key, value, account)