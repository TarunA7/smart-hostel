#!/usr/bin/env python3
"""
Debug script to investigate student dashboard stats issue
"""

import requests
import json

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

def make_request(method: str, endpoint: str, data=None, token=None):
    url = f"{API_BASE}{endpoint}"
    headers = {}
    if token:
        headers['Authorization'] = f"Bearer {token}"
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers)
        
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

# Register and login a student
print("Registering student...")
student_data = {
    "username": "debug_student",
    "email": "debug@college.edu",
    "password": "password123",
    "role": "student",
    "full_name": "Debug Student",
    "phone": "+91-9876543299",
    "student_id": "DEBUG001"
}

response = make_request('POST', '/auth/register', student_data)
if response['success']:
    student_token = response['data']['access_token']
    student_user = response['data']['user']
    print(f"Student registered: {student_user}")
    
    # Check if there's a corresponding student record
    print("\nChecking student records...")
    warden_data = {
        "username": "debug_warden",
        "email": "debug_warden@hostel.edu",
        "password": "password123",
        "role": "warden",
        "full_name": "Debug Warden",
        "phone": "+91-9876543298"
    }
    
    warden_response = make_request('POST', '/auth/register', warden_data)
    if warden_response['success']:
        warden_token = warden_response['data']['access_token']
        
        # Create a student record for the user
        student_record_data = {
            "name": student_user['full_name'],
            "email": student_user['email'],
            "phone": student_user['phone'],
            "student_id": student_user['student_id']
        }
        
        print("Creating student record...")
        create_response = make_request('POST', '/students', student_record_data, warden_token)
        if create_response['success']:
            print(f"Student record created: {create_response['data']}")
            
            # Now try dashboard stats
            print("\nTrying dashboard stats...")
            stats_response = make_request('GET', '/dashboard/stats', token=student_token)
            print(f"Dashboard stats response: {stats_response}")
        else:
            print(f"Failed to create student record: {create_response}")
    else:
        print(f"Failed to register warden: {warden_response}")
else:
    print(f"Failed to register student: {response}")