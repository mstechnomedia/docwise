#!/usr/bin/env python3

import requests
import sys
import json
import os
from datetime import datetime
from io import BytesIO

class AdminPromptManagementTester:
    def __init__(self, base_url="https://docai-answers.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_session_token = None
        self.regular_session_token = None
        self.admin_user_data = None
        self.regular_user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.admin_prompt_id = None

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = {
            "test": name,
            "status": "PASS" if success else "FAIL",
            "details": details
        }
        self.test_results.append(result)
        print(f"{status} - {name}: {details}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, headers=None, session_token=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if session_token:
            test_headers['Authorization'] = f'Bearer {session_token}'
        
        if headers:
            test_headers.update(headers)
        
        if files:
            # Remove Content-Type for multipart/form-data
            test_headers.pop('Content-Type', None)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, headers=test_headers)
                else:
                    response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f" (Expected: {expected_status})"
                try:
                    error_data = response.json()
                    details += f" - {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f" - {response.text[:100]}"

            self.log_test(name, success, details)
            
            if success:
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                return False, {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test API health check"""
        return self.run_test("Health Check", "GET", "", 200)

    def test_register_admin_user(self):
        """Test admin user registration"""
        admin_user = {
            "email": "mueen.ahmed@gmail.com",
            "password": "admin123456",
            "name": "Admin User"
        }
        
        success, response = self.run_test(
            "Admin User Registration",
            "POST",
            "auth/register",
            200,
            data=admin_user
        )
        
        if success and 'session_token' in response:
            self.admin_session_token = response['session_token']
            self.admin_user_data = response['user']
            return True
        return False

    def test_register_regular_user(self):
        """Test regular user registration"""
        regular_user = {
            "email": "test@example.com",
            "password": "password123",
            "name": "Regular User"
        }
        
        success, response = self.run_test(
            "Regular User Registration",
            "POST",
            "auth/register",
            200,
            data=regular_user
        )
        
        if success and 'session_token' in response:
            self.regular_session_token = response['session_token']
            self.regular_user_data = response['user']
            return True
        return False

    def test_admin_login(self):
        """Test admin user login"""
        login_data = {
            "email": "mueen.ahmed@gmail.com",
            "password": "admin123456"
        }
        
        success, response = self.run_test(
            "Admin User Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and 'session_token' in response:
            self.admin_session_token = response['session_token']
            self.admin_user_data = response['user']
            return True
        return False

    def test_regular_login(self):
        """Test regular user login"""
        login_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        
        success, response = self.run_test(
            "Regular User Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and 'session_token' in response:
            self.regular_session_token = response['session_token']
            self.regular_user_data = response['user']
            return True
        return False

    def test_admin_user_info(self):
        """Test admin user info includes is_admin flag"""
        success, response = self.run_test(
            "Admin User Info",
            "GET",
            "auth/me",
            200,
            session_token=self.admin_session_token
        )
        
        if success and response.get('is_admin') == True:
            self.log_test("Admin Flag Check", True, "Admin user correctly identified")
            return True
        else:
            self.log_test("Admin Flag Check", False, f"Admin flag: {response.get('is_admin')}")
            return False

    def test_regular_user_info(self):
        """Test regular user info does not have admin flag"""
        success, response = self.run_test(
            "Regular User Info",
            "GET",
            "auth/me",
            200,
            session_token=self.regular_session_token
        )
        
        if success and response.get('is_admin') == False:
            self.log_test("Regular User Flag Check", True, "Regular user correctly identified")
            return True
        else:
            self.log_test("Regular User Flag Check", False, f"Admin flag: {response.get('is_admin')}")
            return False

    def test_admin_create_prompt(self):
        """Test admin can create prompts"""
        prompt_data = {
            "title": "Admin Test Prompt",
            "content": "This is a test prompt created by admin for document analysis."
        }
        
        success, response = self.run_test(
            "Admin Create Prompt",
            "POST",
            "prompts",
            200,
            data=prompt_data,
            session_token=self.admin_session_token
        )
        
        if success and 'id' in response:
            self.admin_prompt_id = response['id']
            return True
        return False

    def test_regular_user_create_prompt_denied(self):
        """Test regular user cannot create prompts"""
        prompt_data = {
            "title": "Regular User Prompt",
            "content": "This should fail - regular users cannot create prompts."
        }
        
        success, response = self.run_test(
            "Regular User Create Prompt (Should Fail)",
            "POST",
            "prompts",
            403,  # Forbidden
            data=prompt_data,
            session_token=self.regular_session_token
        )
        return success

    def test_admin_update_prompt(self):
        """Test admin can update prompts"""
        if not self.admin_prompt_id:
            return False
            
        update_data = {
            "title": "Updated Admin Prompt",
            "content": "Updated content by admin user."
        }
        
        success, response = self.run_test(
            "Admin Update Prompt",
            "PUT",
            f"prompts/{self.admin_prompt_id}",
            200,
            data=update_data,
            session_token=self.admin_session_token
        )
        return success

    def test_regular_user_update_prompt_denied(self):
        """Test regular user cannot update prompts"""
        if not self.admin_prompt_id:
            return False
            
        update_data = {
            "title": "Hacked Prompt",
            "content": "This should fail - regular users cannot update prompts."
        }
        
        success, response = self.run_test(
            "Regular User Update Prompt (Should Fail)",
            "PUT",
            f"prompts/{self.admin_prompt_id}",
            403,  # Forbidden
            data=update_data,
            session_token=self.regular_session_token
        )
        return success

    def test_admin_get_prompts(self):
        """Test admin can see their own prompts"""
        success, response = self.run_test(
            "Admin Get Prompts",
            "GET",
            "prompts",
            200,
            session_token=self.admin_session_token
        )
        
        if success and isinstance(response, list) and len(response) > 0:
            self.log_test("Admin Prompts Count", True, f"Found {len(response)} prompts")
            return True
        return success

    def test_regular_user_get_admin_prompts(self):
        """Test regular user can see admin's prompts"""
        success, response = self.run_test(
            "Regular User Get Admin Prompts",
            "GET",
            "prompts",
            200,
            session_token=self.regular_session_token
        )
        
        if success and isinstance(response, list):
            # Regular users should see admin's prompts
            self.log_test("Regular User Sees Admin Prompts", True, f"Found {len(response)} admin prompts")
            return True
        return success

    def test_regular_user_delete_prompt_denied(self):
        """Test regular user cannot delete prompts"""
        if not self.admin_prompt_id:
            return False
            
        success, response = self.run_test(
            "Regular User Delete Prompt (Should Fail)",
            "DELETE",
            f"prompts/{self.admin_prompt_id}",
            403,  # Forbidden
            session_token=self.regular_session_token
        )
        return success

    def test_regular_user_document_analysis_with_admin_prompt(self):
        """Test regular user can analyze documents using admin prompts"""
        if not self.admin_prompt_id:
            return False
        
        # Create a simple test PDF content
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test Document for Regular User) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF"""
        
        analysis_data = {
            "prompt_id": self.admin_prompt_id,
            "ai_model": "gpt-5"
        }
        
        files = {
            'file': ('regular_user_test.pdf', BytesIO(pdf_content), 'application/pdf')
        }
        
        data = {
            'analysis_data': json.dumps(analysis_data)
        }
        
        success, response = self.run_test(
            "Regular User Document Analysis with Admin Prompt",
            "POST",
            "documents/analyze",
            200,
            data=data,
            files=files,
            session_token=self.regular_session_token
        )
        
        if success and 'id' in response:
            self.regular_analysis_id = response['id']
            return True
        return False

    def test_regular_user_text_analysis_with_admin_prompt(self):
        """Test regular user can analyze text using admin prompts"""
        if not self.admin_prompt_id:
            return False
        
        text_analysis_data = {
            "prompt_id": self.admin_prompt_id,
            "ai_model": "gpt-5",
            "text_content": "This is a test document for regular user analysis. It contains sample financial data: Revenue $100K, Expenses $60K, Profit $40K.",
            "document_name": "Regular User Text Analysis"
        }
        
        success, response = self.run_test(
            "Regular User Text Analysis with Admin Prompt",
            "POST",
            "documents/analyze-text",
            200,
            data=text_analysis_data,
            session_token=self.regular_session_token
        )
        
        if success and 'id' in response:
            return True
        return False

    def test_admin_delete_prompt(self):
        """Test admin can delete prompts"""
        if not self.admin_prompt_id:
            return False
            
        success, response = self.run_test(
            "Admin Delete Prompt",
            "DELETE",
            f"prompts/{self.admin_prompt_id}",
            200,
            session_token=self.admin_session_token
        )
        return success

    def run_all_tests(self):
        """Run comprehensive admin-only prompt management test suite"""
        print("🚀 Starting Admin-Only Prompt Management Tests")
        print("=" * 60)
        
        # Health check
        self.test_health_check()
        
        # Try to login with existing credentials first
        admin_login_success = self.test_admin_login()
        regular_login_success = self.test_regular_login()
        
        # If login fails, try registration
        if not admin_login_success:
            admin_login_success = self.test_register_admin_user()
        
        if not regular_login_success:
            regular_login_success = self.test_register_regular_user()
        
        if admin_login_success and regular_login_success:
            # Test user info and admin flags
            self.test_admin_user_info()
            self.test_regular_user_info()
            
            # Test admin prompt creation
            if self.test_admin_create_prompt():
                # Test regular user cannot create prompts
                self.test_regular_user_create_prompt_denied()
                
                # Test admin can update prompts
                self.test_admin_update_prompt()
                
                # Test regular user cannot update prompts
                self.test_regular_user_update_prompt_denied()
                
                # Test prompt visibility
                self.test_admin_get_prompts()
                self.test_regular_user_get_admin_prompts()
                
                # Test regular user cannot delete prompts
                self.test_regular_user_delete_prompt_denied()
                
                # Test regular user can use admin prompts for analysis
                self.test_regular_user_document_analysis_with_admin_prompt()
                self.test_regular_user_text_analysis_with_admin_prompt()
                
                # Cleanup - admin deletes prompt
                self.test_admin_delete_prompt()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All admin-only prompt management tests passed!")
            return 0
        else:
            print("❌ Some tests failed!")
            return 1

def main():
    tester = AdminPromptManagementTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())