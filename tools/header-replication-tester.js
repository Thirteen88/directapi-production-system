const axios = require('axios');
const fs = require('fs');
const path = require('path');

class HeaderReplicationTester {
  constructor(captureFile) {
    this.captureData = this.loadCaptureData(captureFile);
    this.testResults = {
      originalFailed: [],
      replicationTests: [],
      successfulAuth: [],
      summary: {}
    };
  }

  loadCaptureData(filePath) {
    try {
      const data = fs.readFileSync(filePath, 'utf8');
      return JSON.parse(data);
    } catch (error) {
      console.error('❌ Failed to load capture data:', error.message);
      process.exit(1);
    }
  }

  async testHeaderReplication() {
    console.log(`🧪 Testing Header Replication for ${this.captureData.siteName}`);
    console.log('=' .repeat(60));

    // Test 1: Replicate failed requests with captured auth data
    await this.testFailedRequestsWithAuth();

    // Test 2: Test chat completion with various auth combinations
    await this.testChatCompletionAuth();

    // Test 3: Test cookies separately
    await this.testCookieAuth();

    // Generate summary
    this.generateTestSummary();
  }

  async testFailedRequestsWithAuth() {
    console.log('\n🔍 Testing Failed Requests with Auth Headers');
    console.log('-'.repeat(50));

    const failedRequests = this.captureData.failedRequests.filter(req => 
      req.url.includes('/chat/completions') || req.url.includes('/models')
    );

    if (failedRequests.length === 0) {
      console.log('⚠️ No failed chat/completion requests found in capture');
      return;
    }

    for (const failedReq of failedRequests.slice(0, 3)) { // Test first 3
      console.log(`\n📡 Testing: ${failedReq.method} ${failedReq.url}`);
      
      // Test with different auth header combinations
      const authCombinations = this.generateAuthCombinations();
      
      for (let i = 0; i < authCombinations.length; i++) {
        const authHeaders = authCombinations[i];
        const testName = `Auth Combo ${i + 1} (${Object.keys(authHeaders).length} headers)`;
        
        try {
          const result = await this.makeRequest(failedReq, authHeaders);
          this.testResults.replicationTests.push({
            testName,
            originalStatus: failedReq.response?.status || 'unknown',
            newStatus: result.status,
            success: result.status < 400,
            responseSize: JSON.stringify(result.data).length,
            headersUsed: Object.keys(authHeaders)
          });

          if (result.status < 400) {
            console.log(`   ✅ ${testName}: ${result.status} SUCCESS!`);
            this.testResults.successfulAuth.push({
              url: failedReq.url,
              headers: authHeaders,
              response: result
            });
          } else {
            console.log(`   ❌ ${testName}: ${result.status}`);
          }
        } catch (error) {
          console.log(`   💥 ${testName}: Error - ${error.message}`);
        }
      }
    }
  }

  async testChatCompletionAuth() {
    console.log('\n💬 Testing Chat Completion with Auth');
    console.log('-'.repeat(50));

    // Find the main chat endpoint
    const chatEndpoint = 'https://chat3.eqing.tech/v1/chat/completions';
    
    // Test message
    const testPayload = {
      model: "gpt-4o-mini",
      messages: [
        { role: "user", content: "Hello! Please say 'Authentication test successful'" }
      ],
      max_tokens: 50,
      temperature: 0.7
    };

    const authCombinations = this.generateAuthCombinations();
    
    for (let i = 0; i < authCombinations.length; i++) {
      const authHeaders = authCombinations[i];
      const testName = `Chat Test ${i + 1}`;
      
      try {
        console.log(`\n🔍 ${testName}: Testing with ${Object.keys(authHeaders).length} auth headers`);
        
        const response = await axios.post(chatEndpoint, testPayload, {
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ...authHeaders
          },
          timeout: 30000
        });

        console.log(`   ✅ SUCCESS: ${response.status}`);
        console.log(`   📄 Response: ${JSON.stringify(response.data).substring(0, 200)}...`);
        
        this.testResults.successfulAuth.push({
          testName,
          url: chatEndpoint,
          headers: authHeaders,
          response: response.data,
          status: response.status
        });

        // If we found a working combination, we can stop
        break;

      } catch (error) {
        if (error.response) {
          console.log(`   ❌ Failed: ${error.response.status} - ${error.response.statusText}`);
          
          // Check if we got a response despite the error
          if (error.response.data && error.response.data.choices) {
            console.log(`   🎯 Got response despite ${error.response.status}:`);
            console.log(`   📄 ${JSON.stringify(error.response.data).substring(0, 150)}...`);
            
            this.testResults.successfulAuth.push({
              testName,
              url: chatEndpoint,
              headers: authHeaders,
              response: error.response.data,
              status: error.response.status,
              note: 'Response extracted from error'
            });
          }
        } else {
          console.log(`   💥 Error: ${error.message}`);
        }
      }
    }
  }

  async testCookieAuth() {
    console.log('\n🍪 Testing Cookie Authentication');
    console.log('-'.repeat(50));

    if (this.captureData.cookies.length === 0) {
      console.log('⚠️ No cookies captured');
      return;
    }

    const chatEndpoint = 'https://chat3.eqing.tech/v1/chat/completions';
    const testPayload = {
      model: "gpt-4o-mini",
      messages: [
        { role: "user", content: "Cookie test: say hello" }
      ],
      max_tokens: 20
    };

    // Create cookie header
    const cookieString = this.captureData.cookies
      .map(cookie => `${cookie.name}=${cookie.value}`)
      .join('; ');

    const cookieHeaders = {
      'Cookie': cookieString
    };

    try {
      console.log(`🔍 Testing with ${this.captureData.cookies.length} cookies`);
      
      const response = await axios.post(chatEndpoint, testPayload, {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
          ...cookieHeaders
        },
        timeout: 30000
      });

      console.log(`   ✅ Cookie auth SUCCESS: ${response.status}`);
      console.log(`   📄 Response: ${JSON.stringify(response.data).substring(0, 200)}...`);
      
      this.testResults.successfulAuth.push({
        testName: 'Cookie Auth',
        url: chatEndpoint,
        headers: cookieHeaders,
        response: response.data,
        status: response.status
      });

    } catch (error) {
      if (error.response) {
        console.log(`   ❌ Cookie auth failed: ${error.response.status}`);
        
        if (error.response.data && error.response.data.choices) {
          console.log(`   🎯 Got response despite error:`);
          console.log(`   📄 ${JSON.stringify(error.response.data).substring(0, 150)}...`);
          
          this.testResults.successfulAuth.push({
            testName: 'Cookie Auth (from error)',
            url: chatEndpoint,
            headers: cookieHeaders,
            response: error.response.data,
            status: error.response.status,
            note: 'Response extracted from error'
          });
        }
      } else {
        console.log(`   💥 Cookie auth error: ${error.message}`);
      }
    }
  }

  generateAuthCombinations() {
    const authHeaders = this.captureData.authHeaders;
    const combinations = [];

    // Combination 1: All auth headers
    if (Object.keys(authHeaders).length > 0) {
      combinations.push({...authHeaders});
    }

    // Combination 2: Only authorization header
    if (authHeaders.authorization) {
      combinations.push({ authorization: authHeaders.authorization });
    }

    // Combination 3: Cookie header (if available)
    const cookieString = this.captureData.cookies
      .map(cookie => `${cookie.name}=${cookie.value}`)
      .join('; ');
    if (cookieString) {
      combinations.push({ Cookie: cookieString });
    }

    // Combination 4: Important looking headers only
    const importantHeaders = {};
    Object.keys(authHeaders).forEach(key => {
      const lowerKey = key.toLowerCase();
      if (lowerKey.includes('auth') || lowerKey.includes('token') || lowerKey.includes('session')) {
        importantHeaders[key] = authHeaders[key];
      }
    });
    if (Object.keys(importantHeaders).length > 0) {
      combinations.push(importantHeaders);
    }

    // Combination 5: Most common headers
    const commonHeaders = {};
    ['authorization', 'x-api-key', 'x-auth-token', 'session-token'].forEach(key => {
      if (authHeaders[key]) {
        commonHeaders[key] = authHeaders[key];
      }
    });
    if (Object.keys(commonHeaders).length > 0) {
      combinations.push(commonHeaders);
    }

    // If no auth headers found, add empty combination
    if (combinations.length === 0) {
      combinations.push({});
    }

    return combinations;
  }

  async makeRequest(originalRequest, authHeaders) {
    const config = {
      method: originalRequest.method.toLowerCase(),
      url: originalRequest.url,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ...authHeaders
      },
      timeout: 30000
    };

    if (originalRequest.payload && ['POST', 'PUT', 'PATCH'].includes(originalRequest.method.toUpperCase())) {
      config.data = typeof originalRequest.payload === 'string' ? 
        JSON.parse(originalRequest.payload) : originalRequest.payload;
    }

    const response = await axios(config);
    return response;
  }

  generateTestSummary() {
    console.log('\n' + '='.repeat(60));
    console.log('📊 HEADER REPLICATION TEST SUMMARY');
    console.log('='.repeat(60));

    const totalTests = this.testResults.replicationTests.length;
    const successfulTests = this.testResults.successfulAuth.length;
    const successRate = totalTests > 0 ? (successfulTests / totalTests * 100).toFixed(1) : 0;

    console.log(`\n📈 Test Results:`);
    console.log(`   Total Tests: ${totalTests}`);
    console.log(`   Successful: ${successfulTests}`);
    console.log(`   Success Rate: ${successRate}%`);

    if (successfulTests > 0) {
      console.log(`\n🎉 SUCCESSFUL AUTHENTICATION FOUND!`);
      console.log(`\n🔑 Working Authentication Methods:`);
      
      this.testResults.successfulAuth.forEach((success, index) => {
        console.log(`\n${index + 1}. ${success.testName}`);
        console.log(`   Status: ${success.status}`);
        console.log(`   Headers: ${Object.keys(success.headers).join(', ')}`);
        
        if (success.response && success.response.choices && success.response.choices[0]) {
          const content = success.response.choices[0].message?.content || 'No content';
          console.log(`   Response: ${content.substring(0, 100)}${content.length > 100 ? '...' : ''}`);
        }
      });

      console.log(`\n✅ Next Steps:`);
      console.log(`1. Use the working headers in DirectAPI agent`);
      console.log(`2. Test with different models and prompts`);
      console.log(`3. Implement session management for long-term use`);

    } else {
      console.log(`\n❌ No Working Authentication Found`);
      console.log(`\n🔧 Troubleshooting:`);
      console.log(`1. Try manual login before capture`);
      console.log(`2. Check if JavaScript-based authentication is required`);
      console.log(`3. Consider WebSocket approach`);
      console.log(`4. Look for additional API endpoints`);
    }

    // Save detailed results
    this.saveTestResults();
  }

  saveTestResults() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `${this.captureData.siteName}-auth-test-results-${timestamp}.json`;
    const filepath = path.join(__dirname, '..', 'captured-apis', filename);
    
    fs.writeFileSync(filepath, JSON.stringify({
      siteName: this.captureData.siteName,
      testTime: new Date().toISOString(),
      testResults: this.testResults,
      captureData: this.captureData
    }, null, 2));
    
    console.log(`\n💾 Detailed test results saved to: ${filepath}`);
  }
}

// Command line interface
function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.log('Usage: node header-replication-tester.js <capture-file>');
    console.log('');
    console.log('Example:');
    console.log('  node header-replication-tester.js captured-apis/eqing-tech-advanced-capture-*.json');
    process.exit(1);
  }

  const captureFile = args[0];
  
  // Support wildcards - find the latest matching file
  if (captureFile.includes('*')) {
    const capturedDir = path.join(__dirname, '..', 'captured-apis');
    const files = fs.readdirSync(capturedDir)
      .filter(f => f.includes(captureFile.replace('*', '').replace('captured-apis/', '')))
      .sort()
      .reverse();
    
    if (files.length > 0) {
      const latestFile = path.join(capturedDir, files[0]);
      console.log(`📁 Using latest capture file: ${latestFile}`);
      
      const tester = new HeaderReplicationTester(latestFile);
      tester.testHeaderReplication().catch(console.error);
    } else {
      console.error('❌ No capture files found matching pattern:', captureFile);
      process.exit(1);
    }
  } else {
    if (!fs.existsSync(captureFile)) {
      console.error('❌ Capture file not found:', captureFile);
      process.exit(1);
    }
    
    const tester = new HeaderReplicationTester(captureFile);
    tester.testHeaderReplication().catch(console.error);
  }
}

if (require.main === module) {
  main();
}