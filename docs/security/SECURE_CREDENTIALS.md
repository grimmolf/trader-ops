# Secure Credential Management for TraderTerminal

TraderTerminal uses a cross-platform secure credential management system to protect your API keys and secrets. This system provides enterprise-grade security while maintaining ease of use across macOS and Linux platforms.

## 🔒 Security Features

### **Native Keyring Integration**
- **macOS**: Uses macOS Keychain Services 
- **Linux**: Uses libsecret/GNOME Keyring or KWallet
- **Encrypted Fallback**: AES-256 encrypted file storage when native keyring unavailable

### **Security Benefits**
- ✅ **No Plain Text Storage**: API keys never stored in plain text files
- ✅ **System Integration**: Uses OS-level security services
- ✅ **Encryption**: Military-grade AES-256 encryption for file storage
- ✅ **Access Control**: Protected by user authentication and system permissions
- ✅ **Audit Trail**: Tracks credential access for security monitoring

## 🚀 Quick Setup

### 1. Install Secure Credential System

```bash
# Run the setup script
chmod +x scripts/setup_secure_credentials.sh
./scripts/setup_secure_credentials.sh
```

The setup script will:
- Install required system dependencies
- Test native keyring support
- Setup encrypted fallback storage
- Migrate existing .env files (optional)

### 2. Set Up Your API Credentials

#### **Interactive Broker Setup**
```bash
# Set up Tastytrade (commission-free trading)
python scripts/manage_credentials.py setup-broker --broker tastytrade

# Set up data services (Alpha Vantage, FRED, TheNewsAPI)
python scripts/manage_credentials.py setup-broker --broker data_services

# Set up Charles Schwab (stocks/options)
python scripts/manage_credentials.py setup-broker --broker schwab

# Set up TopstepX (funded accounts)
python scripts/manage_credentials.py setup-broker --broker topstepx
```

#### **Manual Credential Storage**
```bash
# Store individual credentials securely
python scripts/manage_credentials.py store --key TASTYTRADE_CLIENT_SECRET
python scripts/manage_credentials.py store --key ALPHA_VANTAGE_API_KEY
python scripts/manage_credentials.py store --key THENEWSAPI_KEY
```

### 3. Verify Your Setup

```bash
# List all stored credentials
python scripts/manage_credentials.py list

# Test credential storage system
python scripts/manage_credentials.py test

# Verify a specific credential (value hidden by default)
python scripts/manage_credentials.py get --key TASTYTRADE_CLIENT_SECRET
```

## 📋 Credential Reference

### **Required API Keys by Service**

| Service | Credential Key | Purpose | Cost |
|---------|---------------|---------|------|
| **Tastytrade** | `TASTYTRADE_CLIENT_SECRET` | Multi-asset trading | Free |
| **Alpha Vantage** | `ALPHA_VANTAGE_API_KEY` | Historical stock data | Free |
| **FRED** | `FRED_API_KEY` | Economic indicators | Free |
| **TheNewsAPI** | `THENEWSAPI_KEY` | Real-time financial news | $19/month |
| **Charles Schwab** | `SCHWAB_CLIENT_ID`, `SCHWAB_CLIENT_SECRET` | Stocks/options | Free |
| **TopstepX** | `TOPSTEPX_API_KEY` | Funded account management | Free |

### **Optional Credentials**

| Service | Credential Key | Purpose |
|---------|---------------|---------|
| **Tradovate** | `TRADOVATE_USERNAME`, `TRADOVATE_PASSWORD` | Futures trading |
| **Binance** | `BINANCE_API_KEY`, `BINANCE_API_SECRET` | Crypto data |
| **Coinbase** | `COINBASE_API_KEY`, `COINBASE_API_SECRET` | Crypto data |

## 🛠️ Advanced Usage

### **CLI Commands**

```bash
# Store credential with value prompt (secure)
python scripts/manage_credentials.py store --key API_KEY_NAME

# Store credential with inline value (not recommended for secrets)
python scripts/manage_credentials.py store --key API_KEY_NAME --value "your_key_here"

# Retrieve credential (value hidden by default)
python scripts/manage_credentials.py get --key API_KEY_NAME

# Retrieve credential with value shown
python scripts/manage_credentials.py get --key API_KEY_NAME --show-value

# Delete credential
python scripts/manage_credentials.py delete --key API_KEY_NAME

# List all credentials
python scripts/manage_credentials.py list

# Export credentials for backup (values hidden)
python scripts/manage_credentials.py export

# Export with values (be careful with this!)
python scripts/manage_credentials.py export --include-values --output backup.json
```

### **Account Namespaces**

Organize credentials by trading account or environment:

```bash
# Store credentials for different accounts
python scripts/manage_credentials.py store --key TASTYTRADE_CLIENT_SECRET --account production
python scripts/manage_credentials.py store --key TASTYTRADE_CLIENT_SECRET --account sandbox

# List credentials for specific account
python scripts/manage_credentials.py list --account production
```

### **Migration from Environment Files**

```bash
# Migrate from existing .env file
python scripts/manage_credentials.py migrate --env-file .env

# Migrate to specific account
python scripts/manage_credentials.py migrate --env-file .env --account production
```

## 🏗️ Platform-Specific Configuration

### **macOS Configuration**

- **Storage Location**: macOS Keychain
- **Access**: Protected by macOS user authentication
- **Backup**: Included in iCloud Keychain (if enabled)

```bash
# View keyring status
security dump-keychain | grep TraderTerminal

# Manual keychain access (if needed)
security find-generic-password -s TraderTerminal -a TASTYTRADE_CLIENT_SECRET
```

### **Linux Configuration**

- **Primary**: libsecret/GNOME Keyring
- **Fallback**: Encrypted file storage
- **Storage Location**: `~/.local/share/traderterminal/trader_credentials.enc`

```bash
# Install Linux dependencies (Ubuntu/Debian)
sudo apt-get install python3-dev libdbus-1-dev pkg-config libsecret-1-dev

# Install Linux dependencies (Fedora/RHEL)
sudo dnf install python3-devel dbus-devel pkgconfig libsecret-devel

# Check keyring status
python3 -c "import keyring; print(keyring.get_keyring())"
```

### **Encrypted File Storage (Fallback)**

When native keyring is unavailable:

- **Encryption**: AES-256 with PBKDF2 key derivation
- **Key Source**: System hardware ID + username
- **File Permissions**: 600 (owner read/write only)
- **Storage Location**:
  - macOS: `~/Library/Application Support/TraderTerminal/trader_credentials.enc`
  - Linux: `~/.local/share/traderterminal/trader_credentials.enc`

## 🔧 Integration with TraderTerminal

### **Automatic Credential Loading**

TraderTerminal automatically loads credentials using this priority:

1. **Secure Storage** (keyring/encrypted file)
2. **Environment Variables** (with deprecation warning)
3. **Default Values** (where applicable)

### **Code Integration**

```python
from src.backend.security.credential_loader import load_tastytrade_credentials

# Load credentials securely
credentials = await load_tastytrade_credentials()
if credentials:
    # Use credentials for API calls
    manager = TastytradeManager(credentials)
```

### **Environment Variable Migration**

Existing `.env` files will continue to work but will show warnings:

```
⚠️  Using environment variable for TASTYTRADE_CLIENT_SECRET. 
   Consider migrating to secure storage: 
   python scripts/manage_credentials.py store --key TASTYTRADE_CLIENT_SECRET
```

## 🚨 Security Best Practices

### **DO**
- ✅ Use the secure credential system for all API keys
- ✅ Migrate from `.env` files as soon as possible
- ✅ Use different accounts for production vs. sandbox
- ✅ Regularly rotate API keys (every 90 days)
- ✅ Enable 2FA on all broker accounts
- ✅ Monitor credential access logs

### **DON'T**
- ❌ Store API keys in plain text files
- ❌ Commit credentials to version control
- ❌ Share credentials via email or chat
- ❌ Use production credentials for development
- ❌ Store credentials in screenshots or documentation

### **Credential Rotation**

```bash
# Rotate credentials safely
python scripts/manage_credentials.py store --key OLD_KEY_NAME
python scripts/manage_credentials.py delete --key OLD_KEY_NAME
```

## 🔍 Troubleshooting

### **Common Issues**

#### **"Keyring backend not found"**
```bash
# Install platform-specific keyring support
# macOS: Should work out of the box
# Linux: Install libsecret
sudo apt-get install libsecret-1-dev  # Ubuntu/Debian
sudo dnf install libsecret-devel      # Fedora/RHEL

# Reinstall Python keyring
pip install --upgrade keyring
```

#### **"Permission denied" on Linux**
```bash
# Ensure D-Bus is running
systemctl --user status dbus

# Check if GNOME Keyring is running
ps aux | grep gnome-keyring

# Start GNOME Keyring if needed
gnome-keyring-daemon --start
```

#### **"Credential not found"**
```bash
# Check if credential exists
python scripts/manage_credentials.py list

# Test storage system
python scripts/manage_credentials.py test

# Check account namespace
python scripts/manage_credentials.py list --account production
```

### **Debugging**

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python scripts/manage_credentials.py test

# Check credential storage backend
python3 -c "
from src.backend.security.credential_manager import get_credential_manager
manager = get_credential_manager()
print(f'Backend: {manager.backend_type}')
print(f'Platform: {manager.platform}')
"
```

## 🔄 Backup and Recovery

### **Backup Credentials**

```bash
# Export credentials (without values for security)
python scripts/manage_credentials.py export --output backup.json

# Export with values (store securely!)
python scripts/manage_credentials.py export --include-values --output secure_backup.json
```

### **Restore from Backup**

```bash
# Restore individual credentials
python scripts/manage_credentials.py store --key TASTYTRADE_CLIENT_SECRET

# Bulk restore (not implemented yet - use individual commands)
```

### **System Migration**

When moving to a new system:

1. **Export** credentials from old system (with values)
2. **Install** TraderTerminal on new system
3. **Setup** secure credential system
4. **Import** credentials manually using CLI
5. **Test** all connections
6. **Securely delete** backup files

## 📚 Additional Resources

- **[API Access Guide](../architecture/API_ACCESS_GUIDE.md)**: How to obtain API keys
- **[Security Architecture](../architecture/SECURITY_ARCHITECTURE.md)**: Technical security details
- **[Installation Guide](../user/INSTALLATION_GUIDE.md)**: Complete setup instructions
- **[Development Guide](../developer/DEVELOPMENT_WORKFLOW.md)**: Developer integration

## 🆘 Support

If you encounter issues with the secure credential system:

1. **Run diagnostic**: `python scripts/manage_credentials.py test`
2. **Check logs**: Look for credential-related errors in application logs
3. **Platform support**: Ensure your platform has keyring support
4. **File an issue**: [GitHub Issues](https://github.com/grimmolf/trader-ops/issues)

---

**Remember**: Your trading account security is paramount. Never store API keys in plain text or share them with anyone. The secure credential system is designed to protect your sensitive information while providing convenient access for the TraderTerminal application.