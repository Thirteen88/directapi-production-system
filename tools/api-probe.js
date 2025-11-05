const axios = require('axios');
const fs = require('fs');
const path = require('path');

class APIProbe {
  constructor(siteName, baseUrl) {
    this.siteName = siteName;
    this.baseUrl = baseUrl;
    this.results = {
      siteName,
      baseUrl,
      probeTime: new Date().toISOString(),
      endpoints: [],
      workingEndpoints: [],
      authRequired: [],
      errors: []
    };
    
    this.outputDir = path.join(__dirname, '..', 'captured-apis');
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
  }

  async testEndpoint(endpoint, method = 'GET', data = null, headers = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;
    const config = {
      method,
      url,
      timeout: 10000,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Origin': this.baseUrl,
        'Referer': this.baseUrl + '/',
        ...headers
      }
    };

    if (data && (method === 'POST' || method === 'PUT')) {
      config.data = data;
      config.headers['Content-Type'] = 'application/json';
    }

    const result = {
      url,
      method,
      status: null,
      response: null,
      error: null,
      responseHeaders: null,
      testTime: new Date().toISOString()
    };

    try {
      console.log(`🔍 Testing ${method} ${url}`);
      const response = await axios(config);
      result.status = response.status;
      result.response = response.data;
      result.responseHeaders = response.headers;
      
      console.log(`✅ ${response.status} ${method} ${url}`);
      
      // Check if response looks like a chat API response
      if (this.isChatAPIResponse(response.data)) {
        console.log(`🎯 Chat API detected!`);
        result.isChatAPI = true;
      }
      
      if (this.isModelsAPIResponse(response.data)) {
        console.log(`🤖 Models API detected!`);
        result.isModelsAPI = true;
      }

    } catch (error) {
      result.error = error.message;
      if (error.response) {
        result.status = error.response.status;
        result.responseHeaders = error.response.headers;
        
        if (error.response.status === 401) {
          console.log(`🔒 Auth required: ${method} ${url}`);
          result.authRequired = true;
        } else if (error.response.status === 404) {
          console.log(`❌ Not found: ${method} ${url}`);
        } else {
          console.log(`⚠️ ${error.response.status} ${method} ${url}: ${error.message}`);
        }
      } else {
        console.log(`❌ Error testing ${method} ${url}: ${error.message}`);
      }
    }

    this.results.endpoints.push(result);
    
    if (result.status >= 200 && result.status < 300) {
      this.results.workingEndpoints.push(result);
    }
    
    if (result.authRequired) {
      this.results.authRequired.push(result);
    }

    return result;
  }

  isChatAPIResponse(data) {
    if (!data || typeof data !== 'object') return false;
    
    // Look for common chat API response patterns
    const chatKeys = ['choices', 'messages', 'content', 'text', 'completion', 'response', 'answer'];
    const dataKeys = Object.keys(data);
    
    return chatKeys.some(key => dataKeys.includes(key)) ||
           (data.choices && Array.isArray(data.choices) && data.choices[0]?.message) ||
           (data.messages && Array.isArray(data.messages)) ||
           (data.content && typeof data.content === 'string') ||
           (data.text && typeof data.text === 'string');
  }

  isModelsAPIResponse(data) {
    if (!data || typeof data !== 'object') return false;
    
    // Look for models list patterns
    return (data.data && Array.isArray(data.data) && data.data[0]?.id) ||
           (data.models && Array.isArray(data.models)) ||
           (Array.isArray(data) && data[0]?.id);
  }

  async probeCommonEndpoints() {
    console.log(`\n🚀 Probing common API endpoints for ${this.siteName}...\n`);

    // Common chat API endpoints
    const chatEndpoints = [
      '/api/chat',
      '/api/completion',
      '/api/generate',
      '/api/v1/chat/completions',
      '/api/v1/completions',
      '/v1/chat/completions',
      '/v1/completions',
      '/chat',
      '/completion',
      '/generate',
      '/api/conversation',
      '/api/message',
      '/api/prompt'
    ];

    // Common models endpoints
    const modelsEndpoints = [
      '/api/models',
      '/api/v1/models',
      '/v1/models',
      '/models',
      '/api/available-models',
      '/api/model-list'
    ];

    // Test chat endpoints with sample payload
    const samplePayloads = [
      {
        model: "gpt-3.5-turbo",
        messages: [{ role: "user", content: "Hello" }],
        max_tokens: 100
      },
      {
        prompt: "Hello",
        max_tokens: 100,
        model: "text-davinci-003"
      },
      {
        message: "Hello",
        model: "claude-3-sonnet"
      }
    ];

    // Test GET endpoints first
    console.log('📡 Testing GET endpoints...');
    for (const endpoint of [...modelsEndpoints, ...chatEndpoints]) {
      await this.testEndpoint(endpoint, 'GET');
    }

    // Test POST endpoints (chat)
    console.log('\n📤 Testing POST endpoints (chat)...');
    for (const endpoint of chatEndpoints) {
      for (const payload of samplePayloads) {
        await this.testEndpoint(endpoint, 'POST', payload);
      }
    }

    // Test with different base paths
    const alternativeBases = [
      'https://api.ish.chat',
      'https://ish.chat/api',
      'https://gateway.ish.chat',
      'https://ish.chat/gateway'
    ];

    console.log('\n🔄 Testing alternative base URLs...');
    for (const base of alternativeBases) {
      try {
        await this.testEndpoint(`${base}/models`, 'GET');
        await this.testEndpoint(`${base}/chat/completions`, 'POST', samplePayloads[0]);
      } catch (error) {
        // Continue testing other endpoints
      }
    }
  }

  async saveResults() {
    const filename = `${this.siteName}-probe-${Date.now()}.json`;
    const filepath = path.join(this.outputDir, filename);
    
    fs.writeFileSync(filepath, JSON.stringify(this.results, null, 2));
    console.log(`\n💾 Probe results saved to: ${filepath}`);
    
    // Generate summary
    const summary = this.generateSummary();
    const summaryFile = path.join(this.outputDir, `${this.siteName}-probe-summary-${Date.now()}.md`);
    fs.writeFileSync(summaryFile, summary);
    console.log(`📄 Summary saved to: ${summaryFile}`);
    
    return { filepath, summaryFile };
  }

  generateSummary() {
    const summary = [];
    
    summary.push(`# API Probe Summary: ${this.siteName}`);
    summary.push(``);
    summary.push(`**Base URL:** ${this.baseUrl}`);
    summary.push(`**Probe Time:** ${this.probeTime}`);
    summary.push(``);
    
    summary.push(`## Results Overview`);
    summary.push(`- **Total Endpoints Tested:** ${this.results.endpoints.length}`);
    summary.push(`- **Working Endpoints:** ${this.results.workingEndpoints.length}`);
    summary.push(`- **Auth Required:** ${this.results.authRequired.length}`);
    summary.push(`- **Chat APIs Found:** ${this.results.workingEndpoints.filter(e => e.isChatAPI).length}`);
    summary.push(`- **Models APIs Found:** ${this.results.workingEndpoints.filter(e => e.isModelsAPI).length}`);
    summary.push(``);

    if (this.results.workingEndpoints.length > 0) {
      summary.push(`## Working Endpoints`);
      this.results.workingEndpoints.forEach(endpoint => {
        summary.push(`- **${endpoint.method} ${endpoint.url}** (Status: ${endpoint.status})`);
        if (endpoint.isChatAPI) summary.push(`  - 🎯 Chat API detected`);
        if (endpoint.isModelsAPI) summary.push(`  - 🤖 Models API detected`);
        if (endpoint.response && typeof endpoint.response === 'object') {
          const preview = JSON.stringify(endpoint.response).substring(0, 200);
          summary.push(`  - Response preview: \`${preview}...\``);
        }
        summary.push(``);
      });
    }

    if (this.results.authRequired.length > 0) {
      summary.push(`## Endpoints Requiring Authentication`);
      this.results.authRequired.forEach(endpoint => {
        summary.push(`- **${endpoint.method} ${endpoint.url}** (Status: ${endpoint.status})`);
      });
      summary.push(``);
    }

    if (this.results.errors.length > 0) {
      summary.push(`## Errors`);
      this.results.errors.forEach(error => {
        summary.push(`- ${error}`);
      });
      summary.push(``);
    }

    summary.push(`## Next Steps`);
    if (this.results.workingEndpoints.filter(e => e.isChatAPI).length > 0) {
      summary.push(`1. ✅ Chat API found! Build DirectAPIAgent based on working endpoint`);
      summary.push(`2. Analyze request/response format from captured data`);
      summary.push(`3. Implement authentication if required`);
    } else if (this.results.authRequired.length > 0) {
      summary.push(`1. 🔒 Authentication required. Find auth method`);
      summary.push(`2. Look for login endpoints or API key setup`);
      summary.push(`3. Test with authentication headers`);
    } else {
      summary.push(`1. ❌ No obvious chat API endpoints found`);
      summary.push(`2. Site may use WebSocket or different API pattern`);
      summary.push(`3. Consider browser automation approach`);
    }

    summary.push(``);
    summary.push(`---`);
    summary.push(`*Generated by API Probe*`);

    return summary.join('\n');
  }
}

// Main execution
async function runAPIProbe(siteName, baseUrl) {
  const probe = new APIProbe(siteName, baseUrl);
  
  try {
    await probe.probeCommonEndpoints();
    const results = await probe.saveResults();
    
    console.log(`\n🎉 Probe completed for ${siteName}!`);
    console.log(`📊 Found ${probe.results.workingEndpoints.length} working endpoints`);
    console.log(`🎯 Found ${probe.results.workingEndpoints.filter(e => e.isChatAPI).length} chat APIs`);
    console.log(`🤖 Found ${probe.results.workingEndpoints.filter(e => e.isModelsAPI).length} models APIs`);
    
  } catch (error) {
    console.error('❌ Probe failed:', error.message);
  }
}

// Command line interface
const sites = [
  { name: 'ish-chat', url: 'https://ish.chat' },
  { name: 'eqing-tech', url: 'https://chat3.eqing.tech' }
];

// Run first site by default, or accept command line argument
const targetSite = process.argv[2] ? 
  sites.find(s => s.name === process.argv[2]) || sites[0] : 
  sites[0];

console.log(`🚀 Starting API Probe for ${targetSite.name}...`);
runAPIProbe(targetSite.name, targetSite.url);