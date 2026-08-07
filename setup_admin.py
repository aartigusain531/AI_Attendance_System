#!/usr/bin/env python3
"""
Setup script to create admin accounts for the AI Attendance System
Run this to register admin emails
"""

from app import app, db
from models.database import Admin

def create_admin():
    with app.app_context():
        print("=" * 50)
        print("AI Attendance System - Admin Registration")
        print("=" * 50)
        
        username = input("\nEnter admin username: ").strip()
        
        if not username:
            print("❌ Username cannot be empty")
            return

        password = input("Enter admin password: ").strip()
        if not password:
            print("❌ Password cannot be empty")
            return
        
        # Check if username already exists
        admin_exists = Admin.query.filter_by(username=username).first()
        
        if admin_exists:
            print(f"✅ Username '{username}' is already registered as admin!")
            return
        
        # Create admin account with username and password
        admin = Admin(username=username, password=password)
        db.session.add(admin)
        db.session.commit()
        
        print(f"\n✅ Admin account created successfully!")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print("\n🔐 Admin can now login using:")
        print("   1. Go to /login")
        print(f"   2. Enter username: {username}")
        print("   3. Enter the password you provided")

if __name__ == "__main__":
    create_admin()

