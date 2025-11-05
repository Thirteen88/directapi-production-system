const axios = require('axios');
const fs = require('fs');
const path = require('path');

class SmartAuthTester {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
    this.testResults = {
      basicTests: [],
      headerTests: [],
      cookieTests: [],
      userAgentTests: [],
      successfulCombinations: []
    };
  }

  async runComprehensiveAuthTests() {
    console.log(`🧪 Smart Authentication Testing for ${this.baseUrl}`);
    console.log('=' .repeat(60));

    // Test 1: Basic endpoint testing
    await this.testBasicEndpoints();

    // Test 2: Common header patterns
    await this.testCommonHeaderPatterns();

    // Test 3: User agent variations
    await this.testUserAgentVariations();

    // Test 4: Referer testing
    await this.testRefererHeaders();

    // Test 5: Simulated session patterns
    await this.testSimulatedSessions();

    // Test 6: API key patterns
    await this.testAPIKeyPatterns();

    // Generate final summary
    this.generateComprehensiveSummary();
  }

  async testBasicEndpoints() {
    console.log('\n1️⃣ Testing Basic Endpoint Accessibility');
    console.log('-'.repeat(40));

    const endpoints = [
      '/v1/models',
      '/v1/chat/completions',
      '/models',
      '/chat/completions'
    ];

    for (const endpoint of endpoints) {
      try {
        const response = await axios.get(`${this.baseUrl}${endpoint}`, {
          timeout: 10000,
          headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
          }
        });

        this.testResults.basicTests.push({
          endpoint,
          status: response.status,
          success: response.status < 400,
          responseSize: JSON.stringify(response.data).length
        });

        console.log(`   ✅ ${endpoint}: ${response.status}`);

      } catch (error) {
        const status = error.response?.status || 'TIMEOUT';
        this.testResults.basicTests.push({
          endpoint,
          status,
          success: false,
          error: error.message
        });
        console.log(`   ❌ ${endpoint}: ${status}`);
      }
    }
  }

  async testCommonHeaderPatterns() {
    console.log('\n2️⃣ Testing Common Header Patterns');
    console.log('-'.repeat(40));

    const baseHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Accept-Language': 'en-US,en;q=0.9',
      'Accept-Encoding': 'gzip, deflate, br',
      'Cache-Control': 'no-cache',
      'Pragma': 'no-cache'
    };

    const commonHeaders = [
      { name: 'Origin', value: 'https://chat3.eqing.tech' },
      { name: 'Referer', value: 'https://chat3.eqing.tech/' },
      { name: 'Sec-Fetch-Dest', value: 'empty' },
      { name: 'Sec-Fetch-Mode', value: 'cors' },
      { name: 'Sec-Fetch-Site', value: 'same-origin' },
      { name: 'Sec-Ch-UA', value: '"Not_A Brand";v="8", "Chromium";v="120"' },
      { name: 'Sec-Ch-UA-Mobile', value: '?0' },
      { name: 'Sec-Ch-UA-Platform', value: '"Windows"' }
    ];

    // Test combinations
    const testPayload = {
      model: "gpt-4o-mini",
      messages: [{ role: "user", content: "Test message" }],
      max_tokens: 10
    };

    // Test 1: Minimal headers
    await this.testHeaderCombo('Minimal', baseHeaders, testPayload);

    // Test 2: Add Origin/Referer
    await this.testHeaderCombo('With Origin/Referer', {
      ...baseHeaders,
      'Origin': 'https://chat3.eqing.tech',
      'Referer': 'https://chat3.eqing.tech/'
    }, testPayload);

    // Test 3: Add security headers
    await this.testHeaderCombo('With Security Headers', {
      ...baseHeaders,
      'Origin': 'https://chat3.eqing.tech',
      'Referer': 'https://chat3.eqing.tech/',
      'Sec-Fetch-Dest': 'empty',
      'Sec-Fetch-Mode': 'cors',
      'Sec-Fetch-Site': 'same-origin'
    }, testPayload);

    // Test 4: Full browser headers
    const fullHeaders = {
      ...baseHeaders,
      'Origin': 'https://chat3.eqing.tech',
      'Referer': 'https://chat3.eqing.tech/',
      'Sec-Fetch-Dest': 'empty',
      'Sec-Fetch-Mode': 'cors',
      'Sec-Fetch-Site': 'same-origin',
      'Sec-Ch-UA': '"Not_A Brand";v="8", "Chromium";v="120"',
      'Sec-Ch-UA-Mobile': '?0',
      'Sec-Ch-UA-Platform': '"Windows"'
    };
    await this.testHeaderCombo('Full Browser', fullHeaders, testPayload);
  }

  async testUserAgentVariations() {
    console.log('\n3️⃣ Testing User Agent Variations');
    console.log('-'.repeat(40));

    const userAgents = [
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0',
      'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0',
      'curl/8.0.0',
      'axios/1.0.0'
    ];

    const testPayload = {
      model: "gpt-4o-mini",
      messages: [{ role: "user", content: "UA test" }],
      max_tokens: 5
    };

    const baseHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Origin': 'https://chat3.eqing.tech',
      'Referer': 'https://chat3.eqing.tech/'
    };

    for (let i = 0; i < userAgents.length; i++) {
      const ua = userAgents[i];
      const uaName = ua.split(' ')[0] + (ua.includes('Chrome') ? ' Chrome' : ua.includes('Firefox') ? ' Firefox' : ua.includes('curl') ? ' curl' : ua.includes('axios') ? ' axios' : ' Other');
      
      await this.testHeaderCombo(uaName, {
        ...baseHeaders,
        'User-Agent': ua
      }, testPayload);
    }
  }

  async testRefererHeaders() {
    console.log('\n4️⃣ Testing Referer Variations');
    console.log('-'.repeat(40));

    const referers = [
      'https://chat3.eqing.tech/',
      'https://chat3.eqing.tech',
      'https://eqing.tech/',
      'https://eqing.tech',
      'https://www.eqing.tech/',
      'https://www.eqing.tech',
      null // No referer
    ];

    const testPayload = {
      model: "gpt-4o-mini",
      messages: [{ role: "user", content: "Referer test" }],
      max_tokens: 5
    };

    const baseHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      'Origin': 'https://chat3.eqing.tech'
    };

    for (const referer of referers) {
      const refererName = referer || 'No Referer';
      const headers = referer ? { ...baseHeaders, 'Referer': referer } : baseHeaders;
      
      await this.testHeaderCombo(`Referer: ${refererName}`, headers, testPayload);
    }
  }

  async testSimulatedSessions() {
    console.log('\n5️⃣ Testing Simulated Session Patterns');
    console.log('-'.repeat(40));

    // Common session cookie patterns
    const sessionPatterns = [
      {
        name: 'Session ID',
        headers: {
          'Cookie': 'sessionid=abc123def456; Path=/; Secure'
        }
      },
      {
        name: 'Auth Token',
        headers: {
          'Cookie': 'auth_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9; Path=/'
        }
      },
      {
        name: 'JWT Token',
        headers: {
          'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ'
        }
      },
      {
        name: 'API Key',
        headers: {
          'X-API-Key': 'sk-1234567890abcdef',
          'Authorization': 'Bearer sk-1234567890abcdef'
        }
      },
      {
        name: 'Custom Auth',
        headers: {
          'X-Auth-Token': 'custom-token-123',
          'X-Session-ID': 'session-456'
        }
      }
    ];

    const testPayload = {
      model: "gpt-4o-mini",
      messages: [{ role: "user", content: "Session test" }],
      max_tokens: 5
    };

    const baseHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      'Origin': 'https://chat3.eqing.tech',
      'Referer': 'https://chat3.eqing.tech/'
    };

    for (const pattern of sessionPatterns) {
      await this.testHeaderCombo(pattern.name, {
        ...baseHeaders,
        ...pattern.headers
      }, testPayload);
    }
  }

  async testAPIKeyPatterns() {
    console.log('\n6️⃣ Testing Common API Key Patterns');
    console.log('-'.repeat(40));

    // Common API key formats that services might use
    const apiKeyPatterns = [
      { name: 'OpenAI Format', key: 'sk-1234567890abcdef1234567890abcdef12345678' },
      { name: 'Simple Key', key: '1234567890abcdef' },
      { name: 'UUID Key', key: '550e8400-e29b-41d4-a716-446655440000' },
      { name: 'JWT Key', key: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXkiOiJ2YWx1ZSJ9.invalid' },
      { name: 'Random String', key: 'abc123def456ghi789' }
    ];

    const testPayload = {
      model: "gpt-4o-mini",
      messages: [{ role: "user", content: "API key test" }],
      max_tokens: 5
    };

    const baseHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      'Origin': 'https://chat3.eqing.tech',
      'Referer': 'https://chat3.eqing.tech/'
    };

    for (const pattern of apiKeyPatterns) {
      // Test with Authorization header
      await this.testHeaderCombo(`${pattern.name} (Auth)`, {
        ...baseHeaders,
        'Authorization': `Bearer ${pattern.key}`
      }, testPayload);

      // Test with X-API-Key header
      await this.testHeaderCombo(`${pattern.name} (X-API-Key)`, {
        ...baseHeaders,
        'X-API-Key': pattern.key
      }, testPayload);
    }
  }

  async testHeaderCombo(testName, headers, payload) {
    try {
      const response = await axios.post(`${this.baseUrl}/v1/chat/completions`, payload, {
        headers,
        timeout: 15000
      });

      this.testResults.headerTests.push({
        testName,
        status: response.status,
        success: response.status < 400,
        responseSize: JSON.stringify(response.data).length,
        headers: Object.keys(headers),
        response: response.data
      });

      if (response.status < 400) {
        console.log(`   ✅ ${testName}: ${response.status} SUCCESS!`);
        this.testResults.successfulCombinations.push({
          testName,
          headers,
          response: response.data
        });
        
        // Show response preview
        if (response.data.choices && response.data.choices[0]) {
          const content = response.data.choices[0].message?.content || 'No content';
          console.log(`      Response: ${content.substring(0, 50)}${content.length > 50 ? '...' : ''}`);
        }
      } else {
        console.log(`   ❌ ${testName}: ${response.status}`);
      }

    } catch (error) {
      const status = error.response?.status || 'ERROR';
      
      // Check if we got a meaningful response despite the error
      if (error.response?.data) {
        this.testResults.headerTests.push({
          testName,
          status,
          success: false,
          error: error.message,
          headers: Object.keys(headers),
          responseData: error.response.data
        });

        // Check if response contains chat completion data
        if (error.response.data.choices && error.response.data.choices[0]) {
          const content = error.response.data.choices[0].message?.content || 'No content';
          console.log(`   🎯 ${testName}: ${status} - Got response despite error!`);
          console.log(`      Response: ${content.substring(0, 50)}${content.length > 50 ? '...' : ''}`);
          
          this.testResults.successfulCombinations.push({
            testName: `${testName} (from error)`,
            headers,
            response: error.response.data,
            status,
            note: 'Response extracted from error'
          });
        } else {
          console.log(`   ❌ ${testName}: ${status}`);
        }
      } else {
        console.log(`   💥 ${testName}: ${status} - ${error.message}`);
      }
    }
  }

  generateComprehensiveSummary() {
    console.log('\n' + '='.repeat(60));
    console.log('📊 COMPREHENSIVE AUTHENTICATION TEST SUMMARY');
    console.log('='.repeat(60));

    const totalTests = this.testResults.headerTests.length;
    const successfulTests = this.testResults.successfulCombinations.length;
    const successRate = totalTests > 0 ? (successfulTests / totalTests * 100).toFixed(1) : 0;

    console.log(`\n📈 Overall Results:`);
    console.log(`   Total Authentication Tests: ${totalTests}`);
    console.log(`   Successful Combinations: ${successfulTests}`);
    console.log(`   Success Rate: ${successRate}%`);

    if (successfulTests > 0) {
      console.log(`\n🎉 WORKING AUTHENTICATION COMBINATIONS FOUND!`);
      console.log(`\n🔑 Successful Methods:`);
      
      this.testResults.successfulCombinations.forEach((success, index) => {
        console.log(`\n${index + 1}. ${success.testName}`);
        console.log(`   Status: ${success.status || 'Unknown'}`);
        console.log(`   Headers: ${success.headers.join(', ')}`);
        
        if (success.response && success.response.choices && success.response.choices[0]) {
          const content = success.response.choices[0].message?.content || 'No content';
          console.log(`   Sample Response: ${content.substring(0, 100)}${content.length > 100 ? '...' : ''}`);
        }
        
        if (success.note) {
          console.log(`   Note: ${success.note}`);
        }
      });

      console.log(`\n✅ RECOMMENDATION:`);
      console.log(`1. Use the working header combination in your DirectAPI agent`);
      console.log(`2. Test with different models and prompts`);
      console.log(`3. Monitor for rate limiting or session expiration`);

    } else {
      console.log(`\n❌ No Working Authentication Found`);
      console.log(`\n🔧 Next Steps:`);
      console.log(`1. Manual browser session capture required`);
      console.log(`2. Check for JavaScript-based authentication`);
      console.log(`3. Consider WebSocket or alternative endpoints`);
      console.log(`4. Look for API key registration process`);
    }

    // Analyze patterns
    this.analyzePatterns();

    // Save results
    this.saveComprehensiveResults();
  }

  analyzePatterns() {
    console.log(`\n🔍 Pattern Analysis:`);
    
    // Analyze successful header patterns
    if (this.testResults.successfulCombinations.length > 0) {
      const headerFrequency = {};
      this.testResults.successfulCombinations.forEach(success => {
        success.headers.forEach(header => {
          headerFrequency[header] = (headerFrequency[header] || 0) + 1;
        });
      });

      console.log(`\n📊 Most Common Headers in Successful Requests:`);
      Object.entries(headerFrequency)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 10)
        .forEach(([header, count]) => {
          const percentage = (count / this.testResults.successfulCombinations.length * 100).toFixed(1);
          console.log(`   ${header}: ${count}/${this.testResults.successfulCombinations.length} (${percentage}%)`);
        });
    }

    // Analyze user agents if tested
    const uaTests = this.testResults.headerTests.filter(t => t.testName.includes('Chrome') || t.testName.includes('Firefox'));
    if (uaTests.length > 0) {
      const successfulUA = uaTests.filter(t => t.success).map(t => t.testName);
      if (successfulUA.length > 0) {
        console.log(`\n🌐 Successful User Agents:`);
        successfulUA.forEach(ua => console.log(`   ${ua}`));
      }
    }
  }

  saveComprehensiveResults() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `smart-auth-test-results-${timestamp}.json`;
    const filepath = path.join(__dirname, '..', 'captured-apis', filename);
    
    const results = {
      siteUrl: this.baseUrl,
      testTime: new Date().toISOString(),
      testResults: this.testResults,
      summary: {
        totalTests: this.testResults.headerTests.length,
        successfulCombinations: this.testResults.successfulCombinations.length,
        successRate: this.testResults.headerTests.length > 0 ? 
          (this.testResults.successfulCombinations.length / this.testResults.headerTests.length * 100).toFixed(1) : 0
      }
    };
    
    fs.writeFileSync(filepath, JSON.stringify(results, null, 2));
    console.log(`\n💾 Detailed results saved to: ${filepath}`);
  }
}

// Command line interface
async function main() {
  const baseUrl = 'https://chat3.eqing.tech/v1';
  
  console.log('🚀 Starting Smart Authentication Tester');
  console.log(`🎯 Target: ${baseUrl}`);
  console.log(`📝 This will test various authentication patterns automatically`);
  console.log(`⏱️  Estimated time: 2-3 minutes\n`);

  const tester = new SmartAuthTester(baseUrl);
  await tester.runComprehensiveAuthTests();
}

if (require.main === module) {
  main().catch(console.error);
}