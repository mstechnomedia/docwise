#!/usr/bin/env python3

import requests
import sys
import json
import os
from datetime import datetime
from io import BytesIO

class ManuscriptTMAPITester:
    def __init__(self, base_url="https://docai-answers.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

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

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.session_token:
            test_headers['Authorization'] = f'Bearer {self.session_token}'
        
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

    def test_register_user(self):
        """Test user registration"""
        test_user = {
            "email": f"test_{datetime.now().strftime('%H%M%S')}@example.com",
            "password": "TestPass123!",
            "name": "Test User"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=test_user
        )
        
        if success and 'session_token' in response:
            self.session_token = response['session_token']
            self.user_data = response['user']
            return True
        return False

    def test_login_admin(self):
        """Test admin user login"""
        admin_login = {
            "email": "mueen.ahmed@gmail.com",
            "password": "admin123456"
        }
        
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data=admin_login
        )
        
        if success and 'session_token' in response:
            self.session_token = response['session_token']
            self.user_data = response['user']
            return True
        return False

    def test_login_user(self):
        """Test user login with existing credentials"""
        if not self.user_data:
            return False
            
        login_data = {
            "email": self.user_data['email'],
            "password": "TestPass123!"
        }
        
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and 'session_token' in response:
            self.session_token = response['session_token']
            return True
        return False

    def test_get_current_user(self):
        """Test getting current user info"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_create_prompt(self):
        """Test creating analysis prompt"""
        prompt_data = {
            "title": "Extract Financial Metrics",
            "content": "Please extract all financial metrics, revenue figures, profit margins, and key performance indicators from this document. Provide a structured summary with specific numbers and percentages."
        }
        
        success, response = self.run_test(
            "Create Prompt",
            "POST",
            "prompts",
            200,
            data=prompt_data
        )
        
        if success and 'id' in response:
            self.test_prompt_id = response['id']
            return True
        return False

    def test_create_second_prompt(self):
        """Test creating second analysis prompt for multi-prompt testing"""
        prompt_data = {
            "title": "Extract Key Insights",
            "content": "Please identify and summarize the key insights, trends, and strategic recommendations from this document. Focus on actionable items and future outlook."
        }
        
        success, response = self.run_test(
            "Create Second Prompt",
            "POST",
            "prompts",
            200,
            data=prompt_data
        )
        
        if success and 'id' in response:
            self.test_prompt_id_2 = response['id']
            return True
        return False

    def test_get_prompts(self):
        """Test getting user prompts"""
        success, response = self.run_test(
            "Get Prompts",
            "GET",
            "prompts",
            200
        )
        return success

    def test_update_prompt(self):
        """Test updating a prompt"""
        if not hasattr(self, 'test_prompt_id'):
            return False
            
        update_data = {
            "title": "Updated Financial Metrics",
            "content": "Updated prompt content for extracting financial data with additional focus on quarterly trends."
        }
        
        success, response = self.run_test(
            "Update Prompt",
            "PUT",
            f"prompts/{self.test_prompt_id}",
            200,
            data=update_data
        )
        return success

    def test_document_analysis(self):
        """Test document analysis with PDF upload (single prompt - backwards compatibility)"""
        if not hasattr(self, 'test_prompt_id'):
            return False
        
        # Create a simple test PDF content (this is a minimal PDF structure)
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
(Test Financial Report) Tj
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
        
        # Test with single prompt (backwards compatibility)
        analysis_data = {
            "prompt_ids": [self.test_prompt_id],
            "ai_model": "gpt-5"
        }
        
        files = {
            'file': ('test_document.pdf', BytesIO(pdf_content), 'application/pdf')
        }
        
        data = {
            'analysis_data': json.dumps(analysis_data)
        }
        
        success, response = self.run_test(
            "Document Analysis (Single Prompt)",
            "POST",
            "documents/analyze",
            200,
            data=data,
            files=files
        )
        
        if success and 'id' in response:
            self.test_analysis_id = response['id']
            return True
        return False

    def test_multi_prompt_document_analysis(self):
        """Test document analysis with multiple prompts"""
        if not hasattr(self, 'test_prompt_id') or not hasattr(self, 'test_prompt_id_2'):
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
(Multi-Prompt Test Report) Tj
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
        
        # Test with multiple prompts
        analysis_data = {
            "prompt_ids": [self.test_prompt_id, self.test_prompt_id_2],
            "ai_model": "gpt-5"
        }
        
        files = {
            'file': ('multi_prompt_test.pdf', BytesIO(pdf_content), 'application/pdf')
        }
        
        data = {
            'analysis_data': json.dumps(analysis_data)
        }
        
        success, response = self.run_test(
            "Document Analysis (Multiple Prompts)",
            "POST",
            "documents/analyze",
            200,
            data=data,
            files=files
        )
        
        if success and 'id' in response:
            self.test_multi_analysis_id = response['id']
            return True
        return False

    def test_get_analyses(self):
        """Test getting analysis history"""
        success, response = self.run_test(
            "Get Analysis History",
            "GET",
            "documents/analyses",
            200
        )
        return success

    def test_download_analysis(self):
        """Test downloading analysis report"""
        if not hasattr(self, 'test_analysis_id'):
            return False
            
        success, response = self.run_test(
            "Download Analysis",
            "GET",
            f"documents/analyses/{self.test_analysis_id}/download",
            200
        )
        return success

    def test_text_analysis_gpt5(self):
        """Test text analysis with GPT-5 model (single prompt)"""
        if not hasattr(self, 'test_prompt_id'):
            return False
        
        text_analysis_data = {
            "prompt_ids": [self.test_prompt_id],
            "ai_model": "gpt-5",
            "text_content": "This is a sample financial report. Revenue for Q1 2024 was $1.2 million, representing a 15% increase from the previous quarter. Operating expenses were $800,000, resulting in a net profit margin of 33.3%. Key performance indicators show strong growth in customer acquisition with 500 new customers added this quarter.",
            "document_name": "Sample Financial Text"
        }
        
        success, response = self.run_test(
            "Text Analysis (GPT-5 Single Prompt)",
            "POST",
            "documents/analyze-text",
            200,
            data=text_analysis_data
        )
        
        if success and 'id' in response:
            self.test_text_analysis_id = response['id']
            return True
        return False

    def test_text_analysis_claude4(self):
        """Test text analysis with Claude-4 model (single prompt)"""
        if not hasattr(self, 'test_prompt_id'):
            return False
        
        text_analysis_data = {
            "prompt_ids": [self.test_prompt_id],
            "ai_model": "claude-4",
            "text_content": "Market analysis report: The technology sector showed robust performance in 2024. Software companies experienced an average revenue growth of 22%, while hardware manufacturers saw more modest gains of 8%. Cloud computing services dominated the market with a 45% market share increase. Investment in AI and machine learning technologies reached $50 billion globally.",
            "document_name": "Market Analysis Text"
        }
        
        success, response = self.run_test(
            "Text Analysis (Claude-4 Single Prompt)",
            "POST",
            "documents/analyze-text",
            200,
            data=text_analysis_data
        )
        
        if success and 'id' in response:
            self.test_text_analysis_claude_id = response['id']
            return True
        return False

    def test_multi_prompt_text_analysis(self):
        """Test text analysis with multiple prompts"""
        if not hasattr(self, 'test_prompt_id') or not hasattr(self, 'test_prompt_id_2'):
            return False
        
        text_analysis_data = {
            "prompt_ids": [self.test_prompt_id, self.test_prompt_id_2],
            "ai_model": "gpt-5",
            "text_content": "Comprehensive business report: Our company achieved record revenue of $5.2 million in 2024, marking a 28% year-over-year growth. The technology division contributed 60% of total revenue with innovative AI solutions. Customer satisfaction scores improved to 94%, and we expanded into three new markets. Strategic partnerships with major tech companies are expected to drive 40% growth in 2025. Key challenges include talent acquisition and supply chain optimization.",
            "document_name": "Multi-Prompt Business Report"
        }
        
        success, response = self.run_test(
            "Text Analysis (Multiple Prompts)",
            "POST",
            "documents/analyze-text",
            200,
            data=text_analysis_data
        )
        
        if success and 'id' in response:
            self.test_multi_text_analysis_id = response['id']
            return True
        return False

    def test_text_analysis_validation(self):
        """Test text analysis input validation"""
        # Test missing prompt_ids
        invalid_data = {
            "ai_model": "gpt-5",
            "text_content": "Some text content",
            "document_name": "Test Document"
        }
        
        success, response = self.run_test(
            "Text Analysis Validation (Missing Prompts)",
            "POST",
            "documents/analyze-text",
            422,  # Validation error
            data=invalid_data
        )
        
        # Test empty prompt_ids array
        invalid_data2 = {
            "prompt_ids": [],
            "ai_model": "gpt-5",
            "text_content": "Some text content",
            "document_name": "Test Document"
        }
        
        success2, response2 = self.run_test(
            "Text Analysis Validation (Empty Prompts)",
            "POST",
            "documents/analyze-text",
            400,  # Bad request - at least one prompt required
            data=invalid_data2
        )
        
        # Test missing text_content
        invalid_data3 = {
            "prompt_ids": ["fake-prompt-id"],
            "ai_model": "gpt-5",
            "document_name": "Test Document"
        }
        
        success3, response3 = self.run_test(
            "Text Analysis Validation (Missing Text)",
            "POST",
            "documents/analyze-text",
            422,  # Validation error
            data=invalid_data3
        )
        
        return success and success2 and success3

    def test_delete_prompt(self):
        """Test deleting first prompt"""
        if not hasattr(self, 'test_prompt_id'):
            return False
            
        success, response = self.run_test(
            "Delete First Prompt",
            "DELETE",
            f"prompts/{self.test_prompt_id}",
            200
        )
        return success

    def test_delete_second_prompt(self):
        """Test deleting second prompt"""
        if not hasattr(self, 'test_prompt_id_2'):
            return False
            
        success, response = self.run_test(
            "Delete Second Prompt",
            "DELETE",
            f"prompts/{self.test_prompt_id_2}",
            200
        )
        return success

    def test_logout(self):
        """Test user logout"""
        success, response = self.run_test(
            "User Logout",
            "POST",
            "auth/logout",
            200
        )
        return success

    def run_all_tests(self):
        """Run comprehensive API test suite"""
        print("🚀 Starting Manuscript-TM DocWise API Tests")
        print("=" * 50)
        
        # Health check
        self.test_health_check()
        
        # Authentication tests
        if self.test_register_user():
            self.test_get_current_user()
            
            # Switch to admin user for prompt management
            if self.test_login_admin():
                self.test_get_current_user()
                
                # Prompt management tests (admin only)
                if self.test_create_prompt():
                    self.test_create_second_prompt()  # Create second prompt for multi-prompt testing
                    self.test_get_prompts()
                    self.test_update_prompt()
                    
                    # Document analysis tests (single and multi-prompt)
                    if self.test_document_analysis():
                        self.test_multi_prompt_document_analysis()  # New multi-prompt test
                        self.test_get_analyses()
                        self.test_download_analysis()
                    
                    # Text analysis tests (single and multi-prompt)
                    self.test_text_analysis_gpt5()
                    self.test_text_analysis_claude4()
                    self.test_multi_prompt_text_analysis()  # New multi-prompt test
                    self.test_text_analysis_validation()
                    
                    # Cleanup
                    self.test_delete_prompt()
                    self.test_delete_second_prompt()
                
                # Logout
                self.test_logout()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("❌ Some tests failed!")
            return 1

def main():
    tester = ManuscriptTMAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())