#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Smart Hostel Management System
Tests all API endpoints with realistic data and workflows
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

print(f"Testing backend at: {API_BASE}")

class HostelAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.test_data = {}
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
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
        """Make HTTP request and return response"""
        url = f"{API_BASE}{endpoint}"
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url)
            
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

    def test_student_management_api(self):
        """Test Student Management API endpoints"""
        print("\n🧑‍🎓 Testing Student Management API...")
        
        # Test 1: Create Student
        student_data = {
            "name": "Rahul Sharma",
            "email": "rahul.sharma@college.edu",
            "phone": "+91-9876543210",
            "student_id": "CS2021001"
        }
        
        response = self.make_request('POST', '/students', student_data)
        if response['success']:
            self.test_data['student'] = response['data']
            self.log_result("Create Student", True, f"Created student with ID: {response['data']['id']}")
        else:
            self.log_result("Create Student", False, f"Status: {response['status_code']}, Error: {response.get('error', 'Unknown')}")
            return
        
        # Test 2: Get All Students
        response = self.make_request('GET', '/students')
        if response['success'] and isinstance(response['data'], list):
            self.log_result("Get All Students", True, f"Retrieved {len(response['data'])} students")
        else:
            self.log_result("Get All Students", False, f"Status: {response['status_code']}")
        
        # Test 3: Get Single Student
        student_id = self.test_data['student']['id']
        response = self.make_request('GET', f'/students/{student_id}')
        if response['success']:
            self.log_result("Get Single Student", True, f"Retrieved student: {response['data']['name']}")
        else:
            self.log_result("Get Single Student", False, f"Status: {response['status_code']}")
        
        # Test 4: Update Student
        update_data = {
            "phone": "+91-9876543211",
            "status": "out"
        }
        response = self.make_request('PUT', f'/students/{student_id}', update_data)
        if response['success']:
            self.log_result("Update Student", True, f"Updated student phone and status")
        else:
            self.log_result("Update Student", False, f"Status: {response['status_code']}")

    def test_room_management_api(self):
        """Test Room Management API endpoints"""
        print("\n🏠 Testing Room Management API...")
        
        # Test 1: Create Room
        room_data = {
            "room_number": "A101",
            "floor": 1,
            "capacity": 2
        }
        
        response = self.make_request('POST', '/rooms', room_data)
        if response['success']:
            self.test_data['room'] = response['data']
            self.log_result("Create Room", True, f"Created room: {response['data']['room_number']}")
        else:
            self.log_result("Create Room", False, f"Status: {response['status_code']}")
            return
        
        # Test 2: Get All Rooms
        response = self.make_request('GET', '/rooms')
        if response['success'] and isinstance(response['data'], list):
            self.log_result("Get All Rooms", True, f"Retrieved {len(response['data'])} rooms")
        else:
            self.log_result("Get All Rooms", False, f"Status: {response['status_code']}")
        
        # Test 3: Get Available Rooms
        response = self.make_request('GET', '/rooms/available')
        if response['success']:
            self.log_result("Get Available Rooms", True, f"Retrieved {len(response['data'])} available rooms")
        else:
            self.log_result("Get Available Rooms", False, f"Status: {response['status_code']}")
        
        # Test 4: Room Allocation
        if 'student' in self.test_data and 'room' in self.test_data:
            student_id = self.test_data['student']['id']
            room_id = self.test_data['room']['id']
            response = self.make_request('POST', f'/rooms/{room_id}/allocate/{student_id}')
            if response['success']:
                self.log_result("Room Allocation", True, "Successfully allocated room to student")
            else:
                self.log_result("Room Allocation", False, f"Status: {response['status_code']}")

    def test_visitor_management_api(self):
        """Test Visitor Management API endpoints"""
        print("\n👥 Testing Visitor Management API...")
        
        if 'student' not in self.test_data:
            self.log_result("Visitor Management Setup", False, "No student data available for visitor test")
            return
        
        # Test 1: Create Visitor
        visitor_data = {
            "name": "Priya Patel",
            "phone": "+91-9876543212",
            "visiting_student_id": self.test_data['student']['id'],
            "visiting_student_name": self.test_data['student']['name'],
            "purpose": "Family visit"
        }
        
        response = self.make_request('POST', '/visitors', visitor_data)
        if response['success']:
            self.test_data['visitor'] = response['data']
            self.log_result("Create Visitor", True, f"Registered visitor: {response['data']['name']}")
        else:
            self.log_result("Create Visitor", False, f"Status: {response['status_code']}")
            return
        
        # Test 2: Get All Visitors
        response = self.make_request('GET', '/visitors')
        if response['success'] and isinstance(response['data'], list):
            self.log_result("Get All Visitors", True, f"Retrieved {len(response['data'])} visitors")
        else:
            self.log_result("Get All Visitors", False, f"Status: {response['status_code']}")
        
        # Test 3: Get Active Visitors
        response = self.make_request('GET', '/visitors/active')
        if response['success']:
            self.log_result("Get Active Visitors", True, f"Retrieved {len(response['data'])} active visitors")
        else:
            self.log_result("Get Active Visitors", False, f"Status: {response['status_code']}")
        
        # Test 4: Checkout Visitor
        visitor_id = self.test_data['visitor']['id']
        response = self.make_request('POST', f'/visitors/{visitor_id}/checkout')
        if response['success']:
            self.log_result("Checkout Visitor", True, "Successfully checked out visitor")
        else:
            self.log_result("Checkout Visitor", False, f"Status: {response['status_code']}")

    def test_maintenance_request_api(self):
        """Test Maintenance Request API endpoints"""
        print("\n🔧 Testing Maintenance Request API...")
        
        if 'student' not in self.test_data:
            self.log_result("Maintenance Request Setup", False, "No student data available for maintenance test")
            return
        
        # Test 1: Create Maintenance Request
        maintenance_data = {
            "student_id": self.test_data['student']['id'],
            "student_name": self.test_data['student']['name'],
            "room_number": "A101",
            "issue_type": "Electrical",
            "description": "Light fixture not working in room"
        }
        
        response = self.make_request('POST', '/maintenance', maintenance_data)
        if response['success']:
            self.test_data['maintenance'] = response['data']
            self.log_result("Create Maintenance Request", True, f"Created request: {response['data']['issue_type']}")
        else:
            self.log_result("Create Maintenance Request", False, f"Status: {response['status_code']}")
            return
        
        # Test 2: Get All Maintenance Requests
        response = self.make_request('GET', '/maintenance')
        if response['success'] and isinstance(response['data'], list):
            self.log_result("Get All Maintenance Requests", True, f"Retrieved {len(response['data'])} requests")
        else:
            self.log_result("Get All Maintenance Requests", False, f"Status: {response['status_code']}")
        
        # Test 3: Update Maintenance Status
        request_id = self.test_data['maintenance']['id']
        response = self.make_request('PUT', f'/maintenance/{request_id}/status', {"status": "in_progress"})
        if response['success']:
            self.log_result("Update Maintenance Status", True, "Updated status to in_progress")
        else:
            self.log_result("Update Maintenance Status", False, f"Status: {response['status_code']}")

    def test_fee_management_api(self):
        """Test Fee Management API endpoints"""
        print("\n💰 Testing Fee Management API...")
        
        if 'student' not in self.test_data:
            self.log_result("Fee Management Setup", False, "No student data available for fee test")
            return
        
        # Test 1: Create Fee Record
        fee_data = {
            "student_id": self.test_data['student']['id'],
            "student_name": self.test_data['student']['name'],
            "fee_type": "Monthly Rent",
            "amount": 5000.0,
            "due_date": (datetime.utcnow() + timedelta(days=30)).isoformat()
        }
        
        response = self.make_request('POST', '/fees', fee_data)
        if response['success']:
            self.test_data['fee'] = response['data']
            self.log_result("Create Fee Record", True, f"Created fee: {response['data']['fee_type']} - ₹{response['data']['amount']}")
        else:
            self.log_result("Create Fee Record", False, f"Status: {response['status_code']}")
            return
        
        # Test 2: Get All Fee Records
        response = self.make_request('GET', '/fees')
        if response['success'] and isinstance(response['data'], list):
            self.log_result("Get All Fee Records", True, f"Retrieved {len(response['data'])} fee records")
        else:
            self.log_result("Get All Fee Records", False, f"Status: {response['status_code']}")
        
        # Test 3: Get Overdue Fees
        response = self.make_request('GET', '/fees/overdue')
        if response['success']:
            self.log_result("Get Overdue Fees", True, f"Retrieved {len(response['data'])} overdue fees")
        else:
            self.log_result("Get Overdue Fees", False, f"Status: {response['status_code']}")
        
        # Test 4: Pay Fee
        fee_id = self.test_data['fee']['id']
        response = self.make_request('POST', f'/fees/{fee_id}/pay')
        if response['success']:
            self.log_result("Pay Fee", True, "Successfully processed fee payment")
        else:
            self.log_result("Pay Fee", False, f"Status: {response['status_code']}")

    def test_movement_tracking_api(self):
        """Test Movement Tracking API endpoints"""
        print("\n🚶 Testing Movement Tracking API...")
        
        if 'student' not in self.test_data:
            self.log_result("Movement Tracking Setup", False, "No student data available for movement test")
            return
        
        # Test 1: Log Check-out Movement
        movement_data = {
            "student_id": self.test_data['student']['id'],
            "student_name": self.test_data['student']['name'],
            "action": "check_out",
            "note": "Going to library"
        }
        
        response = self.make_request('POST', '/movements', movement_data)
        if response['success']:
            self.test_data['movement'] = response['data']
            self.log_result("Log Movement (Check-out)", True, f"Logged {response['data']['action']} for {response['data']['student_name']}")
        else:
            self.log_result("Log Movement (Check-out)", False, f"Status: {response['status_code']}")
        
        # Test 2: Log Check-in Movement
        movement_data['action'] = "check_in"
        movement_data['note'] = "Returned from library"
        
        response = self.make_request('POST', '/movements', movement_data)
        if response['success']:
            self.log_result("Log Movement (Check-in)", True, f"Logged {response['data']['action']} for {response['data']['student_name']}")
        else:
            self.log_result("Log Movement (Check-in)", False, f"Status: {response['status_code']}")
        
        # Test 3: Get All Movements
        response = self.make_request('GET', '/movements')
        if response['success'] and isinstance(response['data'], list):
            self.log_result("Get All Movements", True, f"Retrieved {len(response['data'])} movement records")
        else:
            self.log_result("Get All Movements", False, f"Status: {response['status_code']}")
        
        # Test 4: Get Recent Movements
        response = self.make_request('GET', '/movements/recent')
        if response['success']:
            self.log_result("Get Recent Movements", True, f"Retrieved {len(response['data'])} recent movements")
        else:
            self.log_result("Get Recent Movements", False, f"Status: {response['status_code']}")

    def test_dashboard_stats_api(self):
        """Test Dashboard Stats API endpoint"""
        print("\n📊 Testing Dashboard Stats API...")
        
        response = self.make_request('GET', '/dashboard/stats')
        if response['success']:
            stats = response['data']
            expected_fields = [
                'total_students', 'students_in', 'students_out',
                'total_rooms', 'occupied_rooms', 'available_rooms', 'maintenance_rooms',
                'pending_maintenance', 'overdue_fees', 'active_visitors'
            ]
            
            missing_fields = [field for field in expected_fields if field not in stats]
            if not missing_fields:
                self.log_result("Dashboard Stats", True, f"All stats fields present: {len(expected_fields)} metrics")
                print(f"   📈 Students: {stats['total_students']} total, {stats['students_in']} in, {stats['students_out']} out")
                print(f"   🏠 Rooms: {stats['total_rooms']} total, {stats['occupied_rooms']} occupied, {stats['available_rooms']} available")
                print(f"   🔧 Maintenance: {stats['pending_maintenance']} pending requests")
                print(f"   💰 Overdue fees: {stats['overdue_fees']}")
                print(f"   👥 Active visitors: {stats['active_visitors']}")
            else:
                self.log_result("Dashboard Stats", False, f"Missing fields: {missing_fields}")
        else:
            self.log_result("Dashboard Stats", False, f"Status: {response['status_code']}")

    def test_data_consistency(self):
        """Test data consistency across related operations"""
        print("\n🔄 Testing Data Consistency...")
        
        # Verify student status was updated by movement tracking
        if 'student' in self.test_data:
            student_id = self.test_data['student']['id']
            response = self.make_request('GET', f'/students/{student_id}')
            if response['success']:
                student_status = response['data']['status']
                self.log_result("Student Status Consistency", True, f"Student status: {student_status}")
            else:
                self.log_result("Student Status Consistency", False, "Could not verify student status")
        
        # Verify room occupancy was updated by allocation
        if 'room' in self.test_data:
            response = self.make_request('GET', '/rooms')
            if response['success']:
                rooms = response['data']
                allocated_room = next((r for r in rooms if r['id'] == self.test_data['room']['id']), None)
                if allocated_room and allocated_room['occupied'] > 0:
                    self.log_result("Room Occupancy Consistency", True, f"Room occupancy: {allocated_room['occupied']}")
                else:
                    self.log_result("Room Occupancy Consistency", False, "Room occupancy not updated")

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete test student (this should cascade to related data)
        if 'student' in self.test_data:
            student_id = self.test_data['student']['id']
            response = self.make_request('DELETE', f'/students/{student_id}')
            if response['success']:
                self.log_result("Cleanup Student", True, "Test student deleted")
            else:
                self.log_result("Cleanup Student", False, f"Status: {response['status_code']}")

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Comprehensive Backend API Testing...")
        print(f"Backend URL: {API_BASE}")
        print("=" * 60)
        
        try:
            # Test all API endpoints
            self.test_student_management_api()
            self.test_room_management_api()
            self.test_visitor_management_api()
            self.test_maintenance_request_api()
            self.test_fee_management_api()
            self.test_movement_tracking_api()
            self.test_dashboard_stats_api()
            self.test_data_consistency()
            
            # Cleanup
            self.cleanup_test_data()
            
        except Exception as e:
            print(f"❌ Test execution error: {str(e)}")
            self.results['failed'] += 1
            self.results['errors'].append(f"Test execution error: {str(e)}")
        
        # Print final results
        print("\n" + "=" * 60)
        print("📋 FINAL TEST RESULTS")
        print("=" * 60)
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
    
    tester = HostelAPITester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if results['failed'] == 0 else 1)