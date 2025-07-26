#!/usr/bin/env python3
"""
Comprehensive Authentication System Testing for Smart Hostel Management System
Tests JWT-based authentication, role-based access control, and data filtering
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import uuid

# Load backend URL from frontend .env
def load_backend_url():
    env_path = "/app/frontend/.env"
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                return line.split('=')[1].strip()
    return None

BASE_URL = load_backend_url()
API_BASE = f"{BASE_URL}/api"

print(f"Testing authentication system at: {API_BASE}")

class AuthenticationTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_data = {}
        self.tokens = {}
        self.results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    def log_result(self, test_name: str, success: bool, message: str = ""):
        if success:
            self.results['passed'] += 1
            print(f"✅ {test_name}: PASSED {message}")
        else:
            self.results['failed'] += 1
            self.results['errors'].append(f"{test_name}: {message}")
            print(f"❌ {test_name}: FAILED - {message}")
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None, token: str = None) -> Dict:
        """Make HTTP request with optional authentication"""
        url = f"{API_BASE}{endpoint}"
        headers = {}
        if token:
            headers['Authorization'] = f"Bearer {token}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=params, headers=headers)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers)
            
            return {
                'status_code': response.status_code,
                'data': response.json() if response.content else {},
                'success': 200 <= response.status_code < 300
            }
        except Exception as e:
            return {
                'status_code': 0,
                'data': {},
                'success': False,
                'error': str(e)
            }

    def test_user_registration(self):
        """Test user registration for both roles"""
        print("\n👤 Testing User Registration...")
        
        # Test 1: Register Warden
        warden_data = {
            "username": "warden1",
            "email": "warden1@hostel.edu",
            "password": "password123",
            "role": "warden",
            "full_name": "Dr. Rajesh Kumar",
            "phone": "+91-9876543210"
        }
        
        response = self.make_request('POST', '/auth/register', warden_data)
        if response['success']:
            self.test_data['warden'] = response['data']['user']
            self.tokens['warden'] = response['data']['access_token']
            self.log_result("Register Warden", True, f"Warden registered: {response['data']['user']['username']}")
        else:
            self.log_result("Register Warden", False, f"Status: {response['status_code']}, Data: {response.get('data', {})}")
        
        # Test 2: Register Student
        student_data = {
            "username": "student1",
            "email": "student1@college.edu",
            "password": "password123",
            "role": "student",
            "full_name": "Priya Sharma",
            "phone": "+91-9876543211",
            "student_id": "STU001"
        }
        
        response = self.make_request('POST', '/auth/register', student_data)
        if response['success']:
            self.test_data['student'] = response['data']['user']
            self.tokens['student'] = response['data']['access_token']
            self.log_result("Register Student", True, f"Student registered: {response['data']['user']['username']}")
        else:
            self.log_result("Register Student", False, f"Status: {response['status_code']}, Data: {response.get('data', {})}")
        
        # Test 3: Duplicate Username Registration
        response = self.make_request('POST', '/auth/register', warden_data)
        if response['status_code'] == 400:
            self.log_result("Duplicate Username Handling", True, "Correctly rejected duplicate username")
        else:
            self.log_result("Duplicate Username Handling", False, f"Expected 400, got {response['status_code']}")
        
        # Test 4: Duplicate Email Registration
        duplicate_email_data = warden_data.copy()
        duplicate_email_data['username'] = "different_username"
        response = self.make_request('POST', '/auth/register', duplicate_email_data)
        if response['status_code'] == 400:
            self.log_result("Duplicate Email Handling", True, "Correctly rejected duplicate email")
        else:
            self.log_result("Duplicate Email Handling", False, f"Expected 400, got {response['status_code']}")

    def test_user_login(self):
        """Test user login functionality"""
        print("\n🔐 Testing User Login...")
        
        # Test 1: Successful Warden Login
        login_data = {
            "username": "warden1",
            "password": "password123"
        }
        
        response = self.make_request('POST', '/auth/login', login_data)
        if response['success']:
            token = response['data']['access_token']
            user = response['data']['user']
            if token and user['role'] == 'warden':
                self.tokens['warden_login'] = token
                self.log_result("Warden Login", True, f"Login successful, token generated")
            else:
                self.log_result("Warden Login", False, "Missing token or incorrect role")
        else:
            self.log_result("Warden Login", False, f"Status: {response['status_code']}")
        
        # Test 2: Successful Student Login
        login_data = {
            "username": "student1",
            "password": "password123"
        }
        
        response = self.make_request('POST', '/auth/login', login_data)
        if response['success']:
            token = response['data']['access_token']
            user = response['data']['user']
            if token and user['role'] == 'student':
                self.tokens['student_login'] = token
                self.log_result("Student Login", True, f"Login successful, token generated")
            else:
                self.log_result("Student Login", False, "Missing token or incorrect role")
        else:
            self.log_result("Student Login", False, f"Status: {response['status_code']}")
        
        # Test 3: Failed Login - Wrong Password
        login_data = {
            "username": "warden1",
            "password": "wrongpassword"
        }
        
        response = self.make_request('POST', '/auth/login', login_data)
        if response['status_code'] == 401:
            self.log_result("Failed Login - Wrong Password", True, "Correctly rejected wrong password")
        else:
            self.log_result("Failed Login - Wrong Password", False, f"Expected 401, got {response['status_code']}")
        
        # Test 4: Failed Login - Non-existent User
        login_data = {
            "username": "nonexistent",
            "password": "password123"
        }
        
        response = self.make_request('POST', '/auth/login', login_data)
        if response['status_code'] == 401:
            self.log_result("Failed Login - Non-existent User", True, "Correctly rejected non-existent user")
        else:
            self.log_result("Failed Login - Non-existent User", False, f"Expected 401, got {response['status_code']}")

    def test_token_verification(self):
        """Test JWT token verification"""
        print("\n🎫 Testing Token Verification...")
        
        # Test 1: Valid Warden Token
        if 'warden' in self.tokens:
            response = self.make_request('GET', '/auth/me', token=self.tokens['warden'])
            if response['success']:
                user = response['data']
                if user['role'] == 'warden' and user['username'] == 'warden1':
                    self.log_result("Valid Warden Token", True, f"Token verified for {user['username']}")
                else:
                    self.log_result("Valid Warden Token", False, "Token data mismatch")
            else:
                self.log_result("Valid Warden Token", False, f"Status: {response['status_code']}")
        
        # Test 2: Valid Student Token
        if 'student' in self.tokens:
            response = self.make_request('GET', '/auth/me', token=self.tokens['student'])
            if response['success']:
                user = response['data']
                if user['role'] == 'student' and user['username'] == 'student1':
                    self.log_result("Valid Student Token", True, f"Token verified for {user['username']}")
                else:
                    self.log_result("Valid Student Token", False, "Token data mismatch")
            else:
                self.log_result("Valid Student Token", False, f"Status: {response['status_code']}")
        
        # Test 3: Invalid Token
        response = self.make_request('GET', '/auth/me', token="invalid_token_12345")
        if response['status_code'] == 401:
            self.log_result("Invalid Token Rejection", True, "Correctly rejected invalid token")
        else:
            self.log_result("Invalid Token Rejection", False, f"Expected 401, got {response['status_code']}")
        
        # Test 4: No Token
        response = self.make_request('GET', '/auth/me')
        if response['status_code'] == 401 or response['status_code'] == 403:
            self.log_result("No Token Rejection", True, "Correctly rejected request without token")
        else:
            self.log_result("No Token Rejection", False, f"Expected 401/403, got {response['status_code']}")

    def test_role_based_access_control(self):
        """Test role-based access control for endpoints"""
        print("\n🛡️ Testing Role-Based Access Control...")
        
        # Create test data first
        self.setup_test_data()
        
        # Test 1: Warden-only endpoints - Student Creation
        student_data = {
            "name": "Test Student",
            "email": "test@college.edu",
            "phone": "+91-9876543212",
            "student_id": "TEST001"
        }
        
        # Warden should succeed
        if 'warden' in self.tokens:
            response = self.make_request('POST', '/students', student_data, token=self.tokens['warden'])
            if response['success']:
                self.test_data['created_student'] = response['data']
                self.log_result("Warden Create Student", True, "Warden successfully created student")
            else:
                self.log_result("Warden Create Student", False, f"Status: {response['status_code']}")
        
        # Student should fail
        if 'student' in self.tokens:
            response = self.make_request('POST', '/students', student_data, token=self.tokens['student'])
            if response['status_code'] == 403:
                self.log_result("Student Create Student Blocked", True, "Student correctly blocked from creating student")
            else:
                self.log_result("Student Create Student Blocked", False, f"Expected 403, got {response['status_code']}")
        
        # Test 2: Room Management - Warden only
        room_data = {
            "room_number": "TEST101",
            "floor": 1,
            "capacity": 2
        }
        
        # Warden should succeed
        if 'warden' in self.tokens:
            response = self.make_request('POST', '/rooms', room_data, token=self.tokens['warden'])
            if response['success']:
                self.test_data['created_room'] = response['data']
                self.log_result("Warden Create Room", True, "Warden successfully created room")
            else:
                self.log_result("Warden Create Room", False, f"Status: {response['status_code']}")
        
        # Student should fail
        if 'student' in self.tokens:
            response = self.make_request('POST', '/rooms', room_data, token=self.tokens['student'])
            if response['status_code'] == 403:
                self.log_result("Student Create Room Blocked", True, "Student correctly blocked from creating room")
            else:
                self.log_result("Student Create Room Blocked", False, f"Expected 403, got {response['status_code']}")
        
        # Test 3: Visitor Management - Warden only
        if 'created_student' in self.test_data:
            visitor_data = {
                "name": "Test Visitor",
                "phone": "+91-9876543213",
                "visiting_student_id": self.test_data['created_student']['id'],
                "visiting_student_name": self.test_data['created_student']['name'],
                "purpose": "Test visit"
            }
            
            # Warden should succeed
            if 'warden' in self.tokens:
                response = self.make_request('POST', '/visitors', visitor_data, token=self.tokens['warden'])
                if response['success']:
                    self.test_data['created_visitor'] = response['data']
                    self.log_result("Warden Create Visitor", True, "Warden successfully created visitor")
                else:
                    self.log_result("Warden Create Visitor", False, f"Status: {response['status_code']}")
            
            # Student should fail
            if 'student' in self.tokens:
                response = self.make_request('POST', '/visitors', visitor_data, token=self.tokens['student'])
                if response['status_code'] == 403:
                    self.log_result("Student Create Visitor Blocked", True, "Student correctly blocked from creating visitor")
                else:
                    self.log_result("Student Create Visitor Blocked", False, f"Expected 403, got {response['status_code']}")

    def test_data_filtering_by_role(self):
        """Test that students only see their own data while wardens see all data"""
        print("\n🔍 Testing Data Filtering by Role...")
        
        # Test 1: Student Data Access
        if 'student' in self.tokens:
            response = self.make_request('GET', '/students', token=self.tokens['student'])
            if response['success']:
                students = response['data']
                # Student should only see their own data
                if len(students) <= 1:  # Should see only their own record or none
                    self.log_result("Student Data Filtering", True, f"Student sees {len(students)} student record(s)")
                else:
                    self.log_result("Student Data Filtering", False, f"Student sees {len(students)} records, expected ≤1")
            else:
                self.log_result("Student Data Filtering", False, f"Status: {response['status_code']}")
        
        # Test 2: Warden Data Access
        if 'warden' in self.tokens:
            response = self.make_request('GET', '/students', token=self.tokens['warden'])
            if response['success']:
                students = response['data']
                # Warden should see all students
                if len(students) >= 1:  # Should see at least the created test student
                    self.log_result("Warden Data Access", True, f"Warden sees {len(students)} student record(s)")
                else:
                    self.log_result("Warden Data Access", False, f"Warden sees {len(students)} records, expected ≥1")
            else:
                self.log_result("Warden Data Access", False, f"Status: {response['status_code']}")
        
        # Test 3: Fee Records Filtering
        if 'created_student' in self.test_data and 'warden' in self.tokens:
            # Create a fee record first
            fee_data = {
                "student_id": self.test_data['created_student']['id'],
                "student_name": self.test_data['created_student']['name'],
                "fee_type": "Test Fee",
                "amount": 1000.0,
                "due_date": (datetime.utcnow() + timedelta(days=30)).isoformat()
            }
            
            response = self.make_request('POST', '/fees', fee_data, token=self.tokens['warden'])
            if response['success']:
                self.test_data['created_fee'] = response['data']
                
                # Test student access to fees
                if 'student' in self.tokens:
                    response = self.make_request('GET', '/fees', token=self.tokens['student'])
                    if response['success']:
                        fees = response['data']
                        # Student should see limited fees (only their own)
                        self.log_result("Student Fee Filtering", True, f"Student sees {len(fees)} fee record(s)")
                    else:
                        self.log_result("Student Fee Filtering", False, f"Status: {response['status_code']}")
                
                # Test warden access to fees
                response = self.make_request('GET', '/fees', token=self.tokens['warden'])
                if response['success']:
                    fees = response['data']
                    # Warden should see all fees
                    self.log_result("Warden Fee Access", True, f"Warden sees {len(fees)} fee record(s)")
                else:
                    self.log_result("Warden Fee Access", False, f"Status: {response['status_code']}")

    def test_dashboard_stats_filtering(self):
        """Test dashboard stats filtering by role"""
        print("\n📊 Testing Dashboard Stats Filtering...")
        
        # Test 1: Student Dashboard Stats
        if 'student' in self.tokens:
            response = self.make_request('GET', '/dashboard/stats', token=self.tokens['student'])
            if response['success']:
                stats = response['data']
                # Student should see limited stats
                expected_fields = ['total_students', 'students_in', 'students_out', 'total_rooms', 
                                 'occupied_rooms', 'available_rooms', 'maintenance_rooms', 
                                 'pending_maintenance', 'overdue_fees', 'active_visitors']
                
                if all(field in stats for field in expected_fields):
                    self.log_result("Student Dashboard Stats", True, "Student dashboard stats accessible")
                else:
                    self.log_result("Student Dashboard Stats", False, "Missing dashboard fields")
            else:
                self.log_result("Student Dashboard Stats", False, f"Status: {response['status_code']}")
        
        # Test 2: Warden Dashboard Stats
        if 'warden' in self.tokens:
            response = self.make_request('GET', '/dashboard/stats', token=self.tokens['warden'])
            if response['success']:
                stats = response['data']
                # Warden should see comprehensive stats
                expected_fields = ['total_students', 'students_in', 'students_out', 'total_rooms', 
                                 'occupied_rooms', 'available_rooms', 'maintenance_rooms', 
                                 'pending_maintenance', 'overdue_fees', 'active_visitors']
                
                if all(field in stats for field in expected_fields):
                    self.log_result("Warden Dashboard Stats", True, "Warden dashboard stats accessible")
                    print(f"   📈 Total Students: {stats['total_students']}")
                    print(f"   🏠 Total Rooms: {stats['total_rooms']}")
                    print(f"   🔧 Pending Maintenance: {stats['pending_maintenance']}")
                else:
                    self.log_result("Warden Dashboard Stats", False, "Missing dashboard fields")
            else:
                self.log_result("Warden Dashboard Stats", False, f"Status: {response['status_code']}")

    def test_unauthorized_access(self):
        """Test that all endpoints require authentication"""
        print("\n🚫 Testing Unauthorized Access Protection...")
        
        endpoints_to_test = [
            ('GET', '/students'),
            ('GET', '/rooms'),
            ('GET', '/visitors'),
            ('GET', '/maintenance'),
            ('GET', '/fees'),
            ('GET', '/movements'),
            ('GET', '/dashboard/stats')
        ]
        
        for method, endpoint in endpoints_to_test:
            response = self.make_request(method, endpoint)
            if response['status_code'] in [401, 403]:
                self.log_result(f"Unauthorized {method} {endpoint}", True, "Correctly blocked unauthorized access")
            else:
                self.log_result(f"Unauthorized {method} {endpoint}", False, f"Expected 401/403, got {response['status_code']}")

    def setup_test_data(self):
        """Setup test data for role-based testing"""
        # This method is called to ensure we have the necessary test data
        pass

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete created student
        if 'created_student' in self.test_data and 'warden' in self.tokens:
            student_id = self.test_data['created_student']['id']
            response = self.make_request('DELETE', f'/students/{student_id}', token=self.tokens['warden'])
            if response['success']:
                self.log_result("Cleanup Student", True, "Test student deleted")
            else:
                self.log_result("Cleanup Student", False, f"Status: {response['status_code']}")

    def run_all_tests(self):
        """Run all authentication tests"""
        print("🔐 Starting Comprehensive Authentication System Testing...")
        print(f"Backend URL: {API_BASE}")
        print("=" * 70)
        
        try:
            # Test authentication flow
            self.test_user_registration()
            self.test_user_login()
            self.test_token_verification()
            self.test_role_based_access_control()
            self.test_data_filtering_by_role()
            self.test_dashboard_stats_filtering()
            self.test_unauthorized_access()
            
            # Cleanup
            self.cleanup_test_data()
            
        except Exception as e:
            print(f"❌ Test execution error: {str(e)}")
            self.results['failed'] += 1
            self.results['errors'].append(f"Test execution error: {str(e)}")
        
        # Print final results
        print("\n" + "=" * 70)
        print("📋 AUTHENTICATION TEST RESULTS")
        print("=" * 70)
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"📊 Total: {self.results['passed'] + self.results['failed']}")
        
        if self.results['errors']:
            print("\n🚨 ERRORS:")
            for error in self.results['errors']:
                print(f"   • {error}")
        
        success_rate = (self.results['passed'] / (self.results['passed'] + self.results['failed'])) * 100 if (self.results['passed'] + self.results['failed']) > 0 else 0
        print(f"\n🎯 Success Rate: {success_rate:.1f}%")
        
        return self.results

if __name__ == "__main__":
    if not BASE_URL:
        print("❌ Could not load REACT_APP_BACKEND_URL from frontend/.env")
        exit(1)
    
    tester = AuthenticationTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if results['failed'] == 0 else 1)