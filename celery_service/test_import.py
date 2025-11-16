#!/usr/bin/env python
"""
Test script to verify celery_service imports correctly
Run this inside the Docker container to test
"""

import sys
print("Python path:", sys.path)

try:
    from celery_service import celery_app
    print("✅ Successfully imported celery_app")
    print(f"   App name: {celery_app.main}")
    print(f"   Broker: {celery_app.conf.broker_url}")
    print(f"   Backend: {celery_app.conf.result_backend}")
    print(f"   Beat schedule: {list(celery_app.conf.beat_schedule.keys())}")
    print("\n✅ All imports successful!")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
