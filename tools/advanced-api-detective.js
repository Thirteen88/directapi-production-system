const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

class AdvancedAPIDetective {
  constructor(siteName, url) {
    this.siteName = siteName;
    this.url = url;
    this.capturedData = {
      siteName,
      url,
      captureTime: new Date().toISOString(),
      successfulRequests: [],
      failedRequests: [],
      authHeaders: {},
      cookies: [],
      patterns: [],
      notes: []
    };
    
    this.outputDir = path.join(__dirname, '..', 'captured-apis');
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
  }

  async initialize(useDisplay = false) {
    console.log(`\n🔍 Initializing Advanced API Detective for ${this.capturedData.siteName}...`);
    console.log(`📺 Display mode: ${useDisplay ? 'Enabled' : 'Headless'}\n`);
    
    const launchOptions = {
      headless: !useDisplay,
      slowMo: useDisplay ? 100 : 0,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--no-first-run',
        '--no-default-browser-check',
        '--disable-default-apps',
        '--disable-popup-blocking'
      ]
    };

    if (useDisplay) {
      launchOptions.devtools = true;
    }

    this.browser = await chromium.launch(launchOptions);
    
    this.context = await this.browser.newContext({
      viewport: { width: 1920, height: 1080 },
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      ignoreHTTPSErrors: true,
      acceptDownloads: false
    });

    // Set up comprehensive request interception
    await this.setupAdvancedInterception();
  }

  async setupAdvancedInterception() {
    if (!this.context) return;

    // Intercept all requests
    await this.context.route('**/*', async (route) => {
      const request = route.request();
      const reqUrl = request.url();
      
      // Focus on API-like requests
      if (this.isAPIRequest(reqUrl)) {
        const reqHeaders = request.headers();
        const postData = request.postData();
        
        console.log(`\n📡 ${request.method()} ${reqUrl}`);
        console.log('📋 Request Headers:', JSON.stringify(reqHeaders, null, 2));
        
        if (postData) {
          console.log('📦 Request Payload:', postData.substring(0, 500));
        }

        // Capture all auth-related headers
        this.extractAuthData(reqHeaders);

        // Store request data
        const requestData = {
          timestamp: new Date().toISOString(),
          url: reqUrl,
          method: request.method(),
          headers: reqHeaders,
          payload: postData,
          resourceType: request.resourceType()
        };

        await route.continue();
        
        // Wait for response and capture it
        try {
          const response = await Promise.race([
            new Promise(resolve => request.response().then(resolve)),
            new Promise(resolve => setTimeout(() => resolve(null), 10000))
          ]);

          if (response) {
            const responseData = await this.captureResponse(response);
            requestData.response = responseData;
            
            if (response.status() < 400) {
              this.capturedData.successfulRequests.push(requestData);
              console.log(`✅ ${response.status()} ${request.method()} ${reqUrl}`);
            } else {
              this.capturedData.failedRequests.push(requestData);
              console.log(`❌ ${response.status()} ${request.method()} ${reqUrl}`);
            }
          } else {
            console.log(`⏰ Timeout waiting for response: ${reqUrl}`);
            this.capturedData.failedRequests.push(requestData);
          }
        } catch (error) {
          console.log(`💥 Error capturing response: ${error.message}`);
          this.capturedData.failedRequests.push(requestData);
        }
      } else {
        await route.continue();
      }
    });
  }

  async captureResponse(response) {
    try {
      const contentType = response.headers()['content-type'] || '';
      let body;
      let isStreaming = false;
      
      if (contentType.includes('application/json')) {
        body = await response.json();
      } else if (contentType.includes('text/event-stream')) {
        isStreaming = true;
        body = await response.text();
        console.log('🌊 Streaming response detected');
      } else if (contentType.includes('text/')) {
        body = await response.text();
      } else {
        body = `<Binary data: ${contentType}>`;
      }

      // Show response preview
      const responseStr = typeof body === 'string' ? body : JSON.stringify(body, null, 2);
      console.log('📄 Response preview:', responseStr.substring(0, 300) + (responseStr.length > 300 ? '...' : ''));

      return {
        status: response.status(),
        statusText: response.statusText(),
        headers: response.headers(),
        body: body,
        contentType: contentType,
        isStreaming: isStreaming,
        size: JSON.stringify(body).length
      };
    } catch (error) {
      console.log('❌ Error reading response:', error.message);
      return {
        status: response.status(),
        statusText: response.statusText(),
        headers: response.headers(),
        error: error.message
      };
    }
  }

  extractAuthData(headers) {
    // Capture all potentially auth-related headers
    const authPatterns = [
      'authorization', 'auth', 'token', 'key', 'session', 'cookie',
      'csrf', 'xsrf', 'nonce', 'bearer', 'jwt', 'api-key', 'apikey'
    ];

    Object.keys(headers).forEach(key => {
      const lowerKey = key.toLowerCase();
      
      if (authPatterns.some(pattern => lowerKey.includes(pattern))) {
        this.capturedData.authHeaders[key] = headers[key];
        console.log(`🔐 Auth Header Captured: ${key} = ${headers[key].substring(0, 50)}...`);
      }
    });
  }

  isAPIRequest(url) {
    const apiPatterns = [
      '/api/', '/chat', '/v1/', '/v2/', '/stream', '/completion',
      '/generate', '/models', '/auth', '/token', '/session',
      '/conversation', '/message', '/prompt', '/infer', '/llm'
    ];
    
    return apiPatterns.some(pattern => url.includes(pattern)) ||
           url.includes('openai') || url.includes('anthropic') ||
           url.includes('claude') || url.includes('gpt');
  }

  async captureInteractiveSession() {
    if (!this.context) {
      throw new Error('Context not initialized');
    }

    const page = await this.context.newPage();
    
    console.log(`\n🚀 Navigating to ${this.url}...`);
    await page.goto(this.url, { 
      waitUntil: 'networkidle',
      timeout: 60000 
    });

    // Capture cookies after page load
    const cookies = await this.context.cookies();
    this.capturedData.cookies = cookies;
    console.log(`🍪 Captured ${cookies.length} cookies`);

    console.log('\n🎯 INTERACTIVE INSTRUCTIONS:');
    console.log('1. Log in to the site if required');
    console.log('2. Select a model (e.g., Claude, GPT-4, etc.)');
    console.log('3. Send a test message: "Write hello world in Python"');
    console.log('4. Wait for the response to complete');
    console.log('5. Send 2-3 more test messages');
    console.log('6. Press Ctrl+C here to save captured data\n');
    console.log('📡 Capturing all API traffic... (Press Ctrl+C to stop)\n');

    // Wait for manual interaction
    await new Promise(() => {}); // Infinite wait until Ctrl+C
  }

  async saveAdvancedData() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `${this.siteName}-advanced-capture-${timestamp}.json`;
    const filepath = path.join(this.outputDir, filename);
    
    // Analyze captured data
    this.capturedData.analysis = this.analyzeCapturedData();
    
    fs.writeFileSync(filepath, JSON.stringify(this.capturedData, null, 2));
    console.log(`\n💾 Advanced capture saved to: ${filepath}`);
    
    // Generate authentication summary
    const authSummary = this.generateAuthSummary();
    const summaryFile = path.join(this.outputDir, `${this.siteName}-auth-summary-${timestamp}.md`);
    fs.writeFileSync(summaryFile, authSummary);
    console.log(`📄 Authentication summary saved to: ${summaryFile}`);
    
    return { filepath, summaryFile };
  }

  analyzeCapturedData() {
    const analysis = {
      totalRequests: this.capturedData.successfulRequests.length + this.capturedData.failedRequests.length,
      successfulRequests: this.capturedData.successfulRequests.length,
      failedRequests: this.capturedData.failedRequests.length,
      successRate: this.capturedData.successfulRequests.length / (this.capturedData.successfulRequests.length + this.capturedData.failedRequests.length) * 100,
      authHeadersFound: Object.keys(this.capturedData.authHeaders).length,
      cookiesFound: this.capturedData.cookies.length,
      endpoints: [...new Set([...this.capturedData.successfulRequests, ...this.capturedData.failedRequests].map(r => r.url))],
      workingEndpoints: this.capturedData.successfulRequests.map(r => r.url),
      failedEndpoints: this.capturedData.failedRequests.map(r => r.url),
      patterns: this.identifyPatterns()
    };

    console.log(`\n📊 Capture Analysis:`);
    console.log(`   Total Requests: ${analysis.totalRequests}`);
    console.log(`   Successful: ${analysis.successfulRequests}`);
    console.log(`   Failed: ${analysis.failedRequests}`);
    console.log(`   Success Rate: ${analysis.successRate.toFixed(1)}%`);
    console.log(`   Auth Headers: ${analysis.authHeadersFound}`);
    console.log(`   Cookies: ${analysis.cookiesFound}`);
    console.log(`   Unique Endpoints: ${analysis.endpoints.length}`);

    return analysis;
  }

  identifyPatterns() {
    const patterns = [];
    
    // Analyze successful requests
    this.capturedData.successfulRequests.forEach(req => {
      if (req.response && req.response.body) {
        // Check for chat completion patterns
        if (this.isChatResponse(req.response.body)) {
          patterns.push({
            type: 'chat_completion',
            url: req.url,
            method: req.method,
            payloadStructure: this.analyzePayloadStructure(req.payload),
            responseStructure: this.analyzeResponseStructure(req.response.body)
          });
        }
        
        // Check for models list patterns
        if (this.isModelsResponse(req.response.body)) {
          patterns.push({
            type: 'models_list',
            url: req.url,
            method: req.method,
            responseStructure: this.analyzeResponseStructure(req.response.body)
          });
        }
      }
    });

    return patterns;
  }

  isChatResponse(body) {
    if (!body || typeof body !== 'object') return false;
    
    return body.choices || body.message || body.content || body.text;
  }

  isModelsResponse(body) {
    if (!body || typeof body !== 'object') return false;
    
    return (body.data && Array.isArray(body.data) && body.data[0]?.id) ||
           (body.models && Array.isArray(body.models));
  }

  analyzePayloadStructure(payload) {
    if (!payload) return null;
    
    try {
      const parsed = typeof payload === 'string' ? JSON.parse(payload) : payload;
      return {
        hasModel: !!parsed.model,
        hasMessages: !!(parsed.messages && Array.isArray(parsed.messages)),
        hasSystemPrompt: !!(parsed.system_prompt || (parsed.messages && parsed.messages.some(m => m.role === 'system'))),
        hasTemperature: parsed.temperature !== undefined,
        hasMaxTokens: parsed.max_tokens !== undefined,
        keys: Object.keys(parsed)
      };
    } catch {
      return { error: 'Could not parse payload', rawType: typeof payload };
    }
  }

  analyzeResponseStructure(body) {
    if (!body || typeof body !== 'object') return { type: typeof body };
    
    return {
      hasChoices: !!(body.choices && Array.isArray(body.choices)),
      hasUsage: !!body.usage,
      hasMessage: !!(body.choices?.[0]?.message),
      hasContent: !!(body.choices?.[0]?.message?.content || body.content),
      keys: Object.keys(body)
    };
  }

  generateAuthSummary() {
    const authHeaders = this.capturedData.authHeaders;
    const cookies = this.capturedData.cookies;
    const analysis = this.capturedData.analysis;

    let summary = `# Authentication Analysis Summary: ${this.siteName}\n\n`;
    summary += `**Capture Time:** ${this.capturedData.captureTime}\n`;
    summary += `**Success Rate:** ${analysis.successRate.toFixed(1)}%\n\n`;

    // Auth Headers Section
    summary += `## 🔐 Authentication Headers Found (${authHeaders.length})\n\n`;
    if (authHeaders.length > 0) {
      Object.entries(authHeaders).forEach(([key, value]) => {
        summary += `- **${key}**: \`${value.substring(0, 100)}${value.length > 100 ? '...' : ''}\`\n`;
      });
    } else {
      summary += `❌ No authentication headers captured\n`;
    }

    // Cookies Section
    summary += `\n## 🍪 Cookies Captured (${cookies.length})\n\n`;
    if (cookies.length > 0) {
      const importantCookies = cookies.filter(c => 
        c.name.toLowerCase().includes('session') ||
        c.name.toLowerCase().includes('auth') ||
        c.name.toLowerCase().includes('token') ||
        c.name.toLowerCase().includes('key')
      );
      
      if (importantCookies.length > 0) {
        summary += `### Important Cookies:\n`;
        importantCookies.forEach(cookie => {
          summary += `- **${cookie.name}**: \`${cookie.value.substring(0, 50)}${cookie.value.length > 50 ? '...' : ''}\`\n`;
        });
      }
      
      summary += `\n### All Cookies:\n`;
      cookies.forEach(cookie => {
        summary += `- ${cookie.name}\n`;
      });
    } else {
      summary += `❌ No cookies captured\n`;
    }

    // Working Endpoints
    summary += `\n## ✅ Working Endpoints (${analysis.workingEndpoints.length})\n\n`;
    analysis.workingEndpoints.forEach(url => {
      summary += `- ${url}\n`;
    });

    // Next Steps
    summary += `\n## 🎯 Next Steps for DirectAPI Integration\n\n`;
    
    if (authHeaders.length > 0 || cookies.length > 0) {
      summary += `### ✅ Authentication Data Available\n`;
      summary += `1. **Test DirectAPI with captured headers**\n`;
      summary += `2. **Implement cookie management**\n`;
      summary += `3. **Add header replication**\n`;
      
      if (analysis.successRate > 50) {
        summary += `\n🎉 **High Success Rate Detected!** DirectAPI integration should work.\n`;
      }
    } else {
      summary += `### ⚠️ Limited Authentication Data\n`;
      summary += `1. **Try manual login before capture**\n`;
      summary += `2. **Check for JavaScript-based auth**\n`;
      summary += `3. **Consider WebSocket approach**\n`;
    }

    summary += `\n---\n*Generated by Advanced API Detective*`;

    return summary;
  }

  async cleanup() {
    if (this.browser) {
      await this.browser.close();
    }
  }
}

// Main execution with display support
async function runAdvancedAPIDetective(siteName, url, useDisplay = false) {
  const detective = new AdvancedAPIDetective(siteName, url);
  
  try {
    await detective.initialize(useDisplay);
    await detective.captureInteractiveSession();
  } catch (error) {
    console.error('❌ Error:', error.message);
  } finally {
    await detective.saveAdvancedData();
    await detective.cleanup();
  }
}

// Handle Ctrl+C gracefully
process.on('SIGINT', async () => {
  console.log('\n\n🛑 Stopping capture and saving data...');
  process.exit(0);
});

// Command line interface
const sites = [
  { name: 'eqing-tech', url: 'https://chat3.eqing.tech' },
  { name: 'ish-chat', url: 'https://ish.chat' }
];

// Parse command line arguments
const args = process.argv.slice(2);
const siteArg = args.find(arg => arg.startsWith('--site='));
const displayArg = args.includes('--display');

const targetSite = siteArg ? 
  sites.find(s => s.name === siteArg.split('=')[1]) || sites[0] : 
  sites[0];

console.log(`🚀 Starting Advanced API Detective for ${targetSite.name}...`);
console.log(`📺 Display: ${displayArg ? 'Enabled - you can interact with the browser' : 'Headless mode'}`);

if (!displayArg) {
  console.log('\n💡 Tip: Use --display flag to interact with the browser');
  console.log('💡 Example: node advanced-api-detective.js --site=eqing-tech --display');
}

runAdvancedAPIDetective(targetSite.name, targetSite.url, displayArg);