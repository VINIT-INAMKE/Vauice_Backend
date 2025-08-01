#!/usr/bin/env python
"""
Debug script to check environment variables on Render
"""
import os

print("=== Environment Variables Debug ===")
print(f"SECRET_KEY: {'SET' if os.getenv('SECRET_KEY') else 'NOT SET'}")
print(f"DEBUG: {os.getenv('DEBUG', 'NOT SET')}")
print(f"DB_CONN_URL: {'SET' if os.getenv('DB_CONN_URL') else 'NOT SET'}")
print(f"REDIS_URL: {'SET' if os.getenv('REDIS_URL') else 'NOT SET'}")
print(f"CLOUDINARY_CLOUD_NAME: {'SET' if os.getenv('CLOUDINARY_CLOUD_NAME') else 'NOT SET'}")

# Check if .env file exists
env_file_path = '.env'
if os.path.exists(env_file_path):
    print(f".env file found at: {os.path.abspath(env_file_path)}")
else:
    print(".env file not found (this is normal for production)")

print("=== Full Environment (first 50 vars) ===")
for i, (key, value) in enumerate(os.environ.items()):
    if i >= 50:  # Limit output
        break
    # Don't print sensitive values
    if any(sensitive in key.lower() for sensitive in ['secret', 'key', 'token', 'password']):
        print(f"{key}: [HIDDEN]")
    else:
        print(f"{key}: {value}")