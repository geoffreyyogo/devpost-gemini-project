# WSL2 MongoDB Atlas Connection Fix

## Problem
MongoDB Atlas connections fail in WSL2 with DNS resolution errors:
```
pymongo.errors.ServerSelectionTimeoutError: [Errno -3] Temporary failure in name resolution
```

## Root Cause
WSL2's default DNS configuration uses the Windows host as the DNS server, which can fail to resolve external hostnames like MongoDB Atlas cluster addresses.

## Solutions (Try in Order)

### Solution 1: Fix WSL2 DNS Configuration (Recommended)

1. **Run the automated fix script:**
   ```bash
   chmod +x fix_wsl_dns.sh
   ./fix_wsl_dns.sh
   ```

2. **Restart WSL2:**
   - Close ALL WSL terminal windows
   - Open PowerShell or CMD as Administrator
   - Run: `wsl --shutdown`
   - Wait 10 seconds
   - Reopen WSL

3. **Test the fix:**
   ```bash
   # Test DNS resolution
   nslookup cluster0-shard-00-00.ka2dl.mongodb.net
   
   # Should see successful resolution with IP addresses
   ```

4. **Run diagnostics:**
   ```bash
   python test_mongodb_connection.py
   ```

### Solution 2: Manual DNS Fix

If the script doesn't work, fix it manually:

1. **Create/edit WSL configuration:**
   ```bash
   sudo nano /etc/wsl.conf
   ```
   Add:
   ```ini
   [network]
   generateResolvConf = false
   ```

2. **Update DNS servers:**
   ```bash
   sudo nano /etc/resolv.conf
   ```
   Replace content with:
   ```
   nameserver 8.8.8.8
   nameserver 8.8.4.4
   nameserver 1.1.1.1
   ```

3. **Make it persistent:**
   ```bash
   sudo chattr +i /etc/resolv.conf
   ```

4. **Restart WSL2** (as above)

### Solution 3: Use IPv4 Address Directly (Temporary Workaround)

⚠️ **Not recommended for production** but useful for testing:

1. Get MongoDB Atlas IP addresses:
   ```bash
   nslookup cluster0-shard-00-00.ka2dl.mongodb.net 8.8.8.8
   ```

2. Add to `/etc/hosts`:
   ```bash
   sudo nano /etc/hosts
   ```
   Add lines like:
   ```
   18.144.32.12    cluster0-shard-00-00.ka2dl.mongodb.net
   18.144.32.13    cluster0-shard-00-01.ka2dl.mongodb.net
   18.144.32.14    cluster0-shard-00-02.ka2dl.mongodb.net
   ```

### Solution 4: Windows Host DNS Fix

If WSL2 DNS fix doesn't work, the Windows host might have DNS issues:

1. **Flush Windows DNS cache** (in PowerShell as Admin):
   ```powershell
   ipconfig /flushdns
   Clear-DnsClientCache
   ```

2. **Change Windows DNS servers:**
   - Open Network Settings
   - Change adapter options
   - Right-click active network → Properties
   - Select IPv4 → Properties
   - Use these DNS servers:
     - Preferred: 8.8.8.8
     - Alternate: 8.8.4.4

3. **Restart WSL2**

### Solution 5: Check MongoDB Atlas Settings

1. **Verify IP Whitelist:**
   - Go to MongoDB Atlas Dashboard
   - Network Access → IP Access List
   - Temporarily add `0.0.0.0/0` (allow all) for testing
   - ⚠️ Remove this in production!

2. **Check Connection String:**
   - Verify `MONGODB_URI` in `.env` file
   - Should look like: `mongodb+srv://username:password@cluster0.ka2dl.mongodb.net/dbname?retryWrites=true&w=majority`

3. **Verify Credentials:**
   - Database Access → Database Users
   - Ensure user exists and has correct permissions

### Solution 6: Firewall/Antivirus

1. **Temporarily disable Windows Firewall** (for testing only)
2. **Disable antivirus** temporarily
3. **Check VPN/Proxy settings**

## Verification Steps

1. **Test DNS resolution:**
   ```bash
   # Should succeed
   nslookup cluster0-shard-00-00.ka2dl.mongodb.net
   ping mongodb.com
   ```

2. **Test MongoDB connection:**
   ```bash
   python test_mongodb_connection.py
   ```

3. **Test application:**
   ```bash
   cd app
   streamlit run streamlit_app_enhanced.py
   ```
   - Try signing up a new user
   - Should be fast (not slow)
   - Try logging in
   - Should succeed without errors

## Why Signup Was Slow

The slow signup was caused by:
1. MongoDB connection timing out multiple times
2. Retry logic attempting to connect 3 times with 2s delays
3. Eventually succeeding after 30+ seconds
4. Total time: ~30-40 seconds instead of <1 second

After fixing DNS, signup should be instant!

## Code Changes Made

We've updated `/backend/mongodb_service.py` with:
- ✅ Increased timeouts (5s → 30s)
- ✅ Added retry logic (3 attempts)
- ✅ Enabled retry reads/writes
- ✅ Better connection pooling

These changes help, but **fixing the DNS is the real solution!**

## Still Having Issues?

1. **Check your .env file exists:**
   ```bash
   ls -la .env
   cat .env | grep MONGODB_URI
   ```

2. **Test without .env (demo mode):**
   - Temporarily rename `.env` to `.env.backup`
   - App should run in demo mode without MongoDB

3. **Use MongoDB Compass to test:**
   - Install MongoDB Compass
   - Try connecting with your connection string
   - If Compass fails too, it's definitely a network/DNS issue

4. **Check WSL2 version:**
   ```bash
   wsl --version
   ```
   Update to latest if needed.

## Prevention

To prevent this issue from recurring:
1. Keep `/etc/wsl.conf` with `generateResolvConf = false`
2. Keep `/etc/resolv.conf` with Google/Cloudflare DNS
3. Don't run `wsl --update` without backing up configs

## Contact Support

If none of these work:
1. Provide output of: `python test_mongodb_connection.py`
2. Provide output of: `cat /etc/resolv.conf`
3. Provide output of: `nslookup mongodb.com`
4. Your MongoDB Atlas cluster region
5. Your internet connection type (home/office/VPN)

