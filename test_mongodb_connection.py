#!/usr/bin/env python3
"""
MongoDB Connection Diagnostic Tool
Tests connectivity and DNS resolution for MongoDB Atlas
"""

import os
import sys
import socket
from dotenv import load_dotenv

load_dotenv()

def test_dns_resolution(hostname):
    """Test DNS resolution for MongoDB Atlas"""
    print(f"\n🔍 Testing DNS resolution for: {hostname}")
    try:
        # Test using socket
        ip = socket.gethostbyname(hostname)
        print(f"   ✅ Socket resolution: {ip}")
        return True
    except socket.gaierror as e:
        print(f"   ❌ Socket resolution failed: {e}")
        return False

def test_mongodb_connection():
    """Test MongoDB connection"""
    print("\n🔌 Testing MongoDB Connection...")
    
    mongodb_uri = os.getenv('MONGODB_URI')
    if not mongodb_uri:
        print("   ⚠️  MONGODB_URI not set in .env file")
        print("   💡 MongoDB will run in demo mode")
        return False
    
    print(f"   📝 Connection string configured: {mongodb_uri[:20]}...")
    
    # Extract and test individual shard DNS
    print("\n   🔍 Testing MongoDB Atlas shard DNS resolution...")
    dns_ok = True
    for i in range(3):
        shard_host = f"cluster0-shard-00-0{i}.ka2dl.mongodb.net"
        if not test_dns_resolution(shard_host):
            dns_ok = False
    
    if not dns_ok:
        print("\n   ❌ DNS resolution failed - this is the root cause!")
        return False
    
    # Test actual MongoDB connection
    try:
        from pymongo import MongoClient
        import certifi
        
        print("\n⏳ Attempting MongoDB connection (30s timeout)...")
        client = MongoClient(
            mongodb_uri,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
            tls=True,
            tlsAllowInvalidCertificates=True,
            tlsCAFile=certifi.where()
        )
        
        # Test connection
        info = client.server_info()
        print(f"   ✅ Successfully connected to MongoDB!")
        print(f"   📊 MongoDB version: {info.get('version')}")
        
        # Test database access
        db = client['bloomwatch_kenya']
        collections = db.list_collection_names()
        print(f"   📚 Database: bloomwatch_kenya")
        print(f"   📁 Collections: {len(collections)}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"   ❌ MongoDB connection failed: {type(e).__name__}")
        print(f"   📝 Error: {str(e)[:200]}")
        return False

def check_network_config():
    """Check network configuration"""
    print("\n🌐 Network Configuration Check")
    
    # Check DNS servers
    print("   📋 Current DNS servers:")
    try:
        with open('/etc/resolv.conf', 'r') as f:
            for line in f:
                if line.strip().startswith('nameserver'):
                    print(f"      {line.strip()}")
    except Exception as e:
        print(f"   ❌ Could not read /etc/resolv.conf: {e}")
    
    # Check internet connectivity
    print("\n   🌍 Testing internet connectivity:")
    for host in ['8.8.8.8', 'google.com', 'mongodb.com']:
        try:
            if host == '8.8.8.8':
                socket.create_connection((host, 53), timeout=5)
            else:
                socket.gethostbyname(host)
            print(f"      ✅ {host}: Reachable")
        except Exception as e:
            print(f"      ❌ {host}: Unreachable - {e}")

def main():
    print("=" * 70)
    print("🌾 BloomWatch Kenya - MongoDB Connection Diagnostics")
    print("=" * 70)
    
    check_network_config()
    
    # Test specific MongoDB hostnames
    dns_ok = True
    print("\n🔍 Testing MongoDB Atlas DNS Resolution:")
    for i in range(3):
        shard = f"cluster0-shard-00-0{i}.ka2dl.mongodb.net"
        if not test_dns_resolution(shard):
            dns_ok = False
    
    mongo_ok = test_mongodb_connection()
    
    print("\n" + "=" * 70)
    print("📊 Summary")
    print("=" * 70)
    
    if dns_ok and mongo_ok:
        print("✅ All tests passed! MongoDB connection is working.")
        print("\n💡 Your signup should now be fast (<1 second)")
        print("💡 Login should work without errors")
    elif not dns_ok:
        print("❌ DNS resolution is FAILING - This is your problem!")
        print("\n🔧 FIX THIS NOW:")
        print("\n   Step 1: Run the DNS fix script")
        print("   -------")
        print("   ./fix_wsl_dns.sh")
        print("\n   Step 2: Restart WSL2")
        print("   -------")
        print("   1. Close ALL WSL terminal windows")
        print("   2. Open PowerShell or CMD")
        print("   3. Run: wsl --shutdown")
        print("   4. Wait 10 seconds")
        print("   5. Reopen WSL")
        print("\n   Step 3: Test again")
        print("   -------")
        print("   python test_mongodb_connection.py")
        print("\n📖 See WSL2_MONGODB_FIX.md for detailed troubleshooting")
    elif not mongo_ok:
        print("❌ MongoDB connection is failing (but DNS works)")
        print("\n💡 Solutions:")
        print("   1. Verify MONGODB_URI in .env file")
        print("   2. Check MongoDB Atlas IP whitelist:")
        print("      - Go to MongoDB Atlas → Network Access")
        print("      - Add IP: 0.0.0.0/0 (for testing)")
        print("   3. Verify MongoDB Atlas cluster is running")
        print("   4. Check MongoDB Atlas credentials")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
