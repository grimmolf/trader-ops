#!/usr/bin/env python3
"""
TraderTerminal Credential Management CLI

Secure management of API keys and secrets across macOS and Linux platforms.

Usage:
    python manage_credentials.py store --key TASTYTRADE_CLIENT_SECRET --value abc123
    python manage_credentials.py get --key TASTYTRADE_CLIENT_SECRET
    python manage_credentials.py list
    python manage_credentials.py migrate --env-file .env
    python manage_credentials.py test
    python manage_credentials.py setup-broker --broker tastytrade
"""

import asyncio
import argparse
import sys
import getpass
from pathlib import Path
import json
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backend.security.credential_manager import (
    SecureCredentialManager, 
    get_credential_manager,
    CredentialManagerError
)


class CredentialCLI:
    """Command-line interface for credential management"""
    
    def __init__(self):
        self.manager = get_credential_manager()
    
    async def store_credential(self, key: str, value: str = None, account: str = "default") -> bool:
        """Store a credential with optional interactive input"""
        if value is None:
            # Securely prompt for value
            value = getpass.getpass(f"Enter value for {key}: ")
        
        if not value:
            print("Error: Empty value provided")
            return False
        
        try:
            success = await self.manager.store_credential(key, value, account)
            if success:
                print(f"✅ Stored credential: {key}")
                return True
            else:
                print(f"❌ Failed to store credential: {key}")
                return False
        except CredentialManagerError as e:
            print(f"❌ Error storing credential: {e}")
            return False
    
    async def get_credential(self, key: str, account: str = "default", show_value: bool = False) -> bool:
        """Retrieve a credential"""
        try:
            value = await self.manager.get_credential(key, account)
            if value is None:
                print(f"❌ Credential not found: {key}")
                return False
            
            if show_value:
                print(f"✅ {key}: {value}")
            else:
                print(f"✅ {key}: {'*' * min(len(value), 20)}")
            
            return True
        except Exception as e:
            print(f"❌ Error retrieving credential: {e}")
            return False
    
    async def list_credentials(self, account: str = "default") -> bool:
        """List all stored credentials"""
        try:
            keys = await self.manager.list_credentials(account)
            if not keys:
                print(f"No credentials found for account: {account}")
                return True
            
            print(f"Stored credentials for account '{account}':")
            for i, key in enumerate(sorted(keys), 1):
                print(f"  {i:2d}. {key}")
            
            return True
        except Exception as e:
            print(f"❌ Error listing credentials: {e}")
            return False
    
    async def delete_credential(self, key: str, account: str = "default") -> bool:
        """Delete a credential"""
        try:
            # Confirm deletion
            confirm = input(f"Delete credential '{key}' from account '{account}'? [y/N]: ")
            if confirm.lower() not in ['y', 'yes']:
                print("Deletion cancelled")
                return True
            
            success = await self.manager.delete_credential(key, account)
            if success:
                print(f"✅ Deleted credential: {key}")
                return True
            else:
                print(f"❌ Failed to delete credential: {key}")
                return False
        except Exception as e:
            print(f"❌ Error deleting credential: {e}")
            return False
    
    async def migrate_from_env(self, env_file: str, account: str = "default") -> bool:
        """Migrate credentials from .env file"""
        try:
            env_path = Path(env_file)
            if not env_path.exists():
                print(f"❌ Environment file not found: {env_file}")
                return False
            
            print(f"Migrating credentials from {env_file}...")
            results = await self.manager.migrate_from_env_file(str(env_path), account)
            
            successful = sum(results.values())
            total = len(results)
            
            print(f"\nMigration Results:")
            print(f"✅ Successful: {successful}/{total}")
            
            for key, success in results.items():
                status = "✅" if success else "❌"
                print(f"  {status} {key}")
            
            if successful > 0:
                print(f"\n⚠️  Consider deleting or securing the .env file:")
                print(f"     rm {env_file}")
                print(f"     # or move to secure backup location")
            
            return successful == total
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False
    
    async def test_storage(self) -> bool:
        """Test credential storage functionality"""
        try:
            print("Testing credential storage...")
            results = await self.manager.test_storage()
            
            print(f"\nSystem Information:")
            print(f"  Platform: {results['platform']}")
            print(f"  Backend: {results['backend']}")
            print(f"  Keyring Available: {results['keyring_available']}")
            
            print(f"\nStorage Tests:")
            print(f"  Store: {'✅' if results.get('store_test') else '❌'}")
            print(f"  Retrieve: {'✅' if results.get('retrieve_test') else '❌'}")
            print(f"  Delete: {'✅' if results.get('delete_test') else '❌'}")
            
            if 'error' in results:
                print(f"  Error: {results['error']}")
            
            all_passed = all(results.get(test, False) for test in ['store_test', 'retrieve_test', 'delete_test'])
            
            if all_passed:
                print(f"\n✅ All tests passed! Credential storage is working.")
            else:
                print(f"\n❌ Some tests failed. Check system configuration.")
            
            return all_passed
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False
    
    async def setup_broker(self, broker_name: str) -> bool:
        """Interactive setup for specific broker credentials"""
        broker_configs = {
            "tastytrade": {
                "name": "Tastytrade",
                "credentials": [
                    ("TASTYTRADE_CLIENT_SECRET", "Client Secret", True),
                    ("TASTYTRADE_REDIRECT_URI", "Redirect URI", False),
                    ("TASTYTRADE_SANDBOX", "Use Sandbox (true/false)", False)
                ]
            },
            "schwab": {
                "name": "Charles Schwab",
                "credentials": [
                    ("SCHWAB_CLIENT_ID", "Client ID", False),
                    ("SCHWAB_CLIENT_SECRET", "Client Secret", True),
                    ("SCHWAB_REDIRECT_URI", "Redirect URI", False)
                ]
            },
            "tradovate": {
                "name": "Tradovate",
                "credentials": [
                    ("TRADOVATE_USERNAME", "Username", False),
                    ("TRADOVATE_PASSWORD", "Password", True),
                    ("TRADOVATE_APP_ID", "App ID", False),
                    ("TRADOVATE_CID", "CID", False),
                    ("TRADOVATE_SEC", "SEC", True)
                ]
            },
            "topstepx": {
                "name": "TopstepX",
                "credentials": [
                    ("TOPSTEPX_USERNAME", "Username", False),
                    ("TOPSTEPX_PASSWORD", "Password", True),
                    ("TOPSTEPX_API_KEY", "API Key", True)
                ]
            },
            "data_services": {
                "name": "Data Services",
                "credentials": [
                    ("ALPHA_VANTAGE_API_KEY", "Alpha Vantage API Key", True),
                    ("FRED_API_KEY", "FRED API Key", True),
                    ("THENEWSAPI_KEY", "TheNewsAPI Key", True)
                ]
            }
        }
        
        if broker_name not in broker_configs:
            print(f"❌ Unknown broker: {broker_name}")
            print(f"Available brokers: {', '.join(broker_configs.keys())}")
            return False
        
        config = broker_configs[broker_name]
        print(f"\n🔧 Setting up {config['name']} credentials")
        print("=" * 50)
        
        for key, description, is_secret in config["credentials"]:
            print(f"\n{description}:")
            
            if is_secret:
                value = getpass.getpass(f"Enter {description}: ")
            else:
                value = input(f"Enter {description}: ")
            
            if value:
                success = await self.store_credential(key, value)
                if not success:
                    print(f"❌ Failed to store {key}")
                    return False
            else:
                print(f"⏭️  Skipped {key}")
        
        print(f"\n✅ {config['name']} setup complete!")
        return True
    
    async def export_credentials(self, account: str = "default", output_file: str = None, include_values: bool = False) -> bool:
        """Export credentials for backup"""
        try:
            export_data = await self.manager.export_credentials(account, include_values)
            
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(export_data, f, indent=2)
                print(f"✅ Exported credentials to: {output_file}")
            else:
                print(json.dumps(export_data, indent=2))
            
            return True
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            return False


async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="TraderTerminal Secure Credential Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Store a credential interactively
  python manage_credentials.py store --key TASTYTRADE_CLIENT_SECRET
  
  # Store with value (not recommended for secrets)
  python manage_credentials.py store --key ALPHA_VANTAGE_API_KEY --value abc123
  
  # Get a credential (value hidden by default)
  python manage_credentials.py get --key TASTYTRADE_CLIENT_SECRET
  
  # Get with value shown
  python manage_credentials.py get --key TASTYTRADE_CLIENT_SECRET --show-value
  
  # List all credentials
  python manage_credentials.py list
  
  # Migrate from .env file
  python manage_credentials.py migrate --env-file .env
  
  # Test storage system
  python manage_credentials.py test
  
  # Interactive broker setup
  python manage_credentials.py setup-broker --broker tastytrade
  python manage_credentials.py setup-broker --broker data_services
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Store command
    store_parser = subparsers.add_parser('store', help='Store a credential')
    store_parser.add_argument('--key', required=True, help='Credential key')
    store_parser.add_argument('--value', help='Credential value (will prompt if not provided)')
    store_parser.add_argument('--account', default='default', help='Account namespace')
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Retrieve a credential')
    get_parser.add_argument('--key', required=True, help='Credential key')
    get_parser.add_argument('--account', default='default', help='Account namespace')
    get_parser.add_argument('--show-value', action='store_true', help='Show credential value')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all credentials')
    list_parser.add_argument('--account', default='default', help='Account namespace')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a credential')
    delete_parser.add_argument('--key', required=True, help='Credential key')
    delete_parser.add_argument('--account', default='default', help='Account namespace')
    
    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Migrate from .env file')
    migrate_parser.add_argument('--env-file', required=True, help='Path to .env file')
    migrate_parser.add_argument('--account', default='default', help='Account namespace')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test credential storage')
    
    # Setup broker command
    setup_parser = subparsers.add_parser('setup-broker', help='Interactive broker setup')
    setup_parser.add_argument('--broker', required=True, 
                             choices=['tastytrade', 'schwab', 'tradovate', 'topstepx', 'data_services'],
                             help='Broker to set up')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export credentials')
    export_parser.add_argument('--account', default='default', help='Account namespace')
    export_parser.add_argument('--output', help='Output file (default: stdout)')
    export_parser.add_argument('--include-values', action='store_true', help='Include credential values')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    cli = CredentialCLI()
    
    try:
        if args.command == 'store':
            success = await cli.store_credential(args.key, args.value, args.account)
        elif args.command == 'get':
            success = await cli.get_credential(args.key, args.account, args.show_value)
        elif args.command == 'list':
            success = await cli.list_credentials(args.account)
        elif args.command == 'delete':
            success = await cli.delete_credential(args.key, args.account)
        elif args.command == 'migrate':
            success = await cli.migrate_from_env(args.env_file, args.account)
        elif args.command == 'test':
            success = await cli.test_storage()
        elif args.command == 'setup-broker':
            success = await cli.setup_broker(args.broker)
        elif args.command == 'export':
            success = await cli.export_credentials(args.account, args.output, args.include_values)
        else:
            print(f"Unknown command: {args.command}")
            return 1
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))