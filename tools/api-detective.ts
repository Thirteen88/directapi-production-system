import { chromium, Browser, BrowserContext, Page } from 'playwright';
import * as fs from 'fs';
import * as path from 'path';

interface APICall {
  timestamp: string;
  url: string;
  method: string;
  headers: Record<string, string>;
  payload?: any;
  response?: any;
  responseHeaders?: Record<string, string>;
  status?: number;
}

interface CapturedData {
  siteName: string;
  url: string;
  captureTime: string;
  apiCalls: APICall[];
  authHeaders: Record<string, string>;
  notes: string[];
}

class APIDetective {
  private browser: Browser | null = null;
  private context: BrowserContext | null = null;
  private capturedData: CapturedData;
  private outputDir: string;

  constructor(siteName: string, url: string) {
    this.capturedData = {
      siteName,
      url,
      captureTime: new Date().toISOString(),
      apiCalls: [],
      authHeaders: {},
      notes: []
    };
    
    this.outputDir = path.join(__dirname, '..', 'captured-apis');
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
  }

  async initialize(): Promise<void> {
    console.log(`\n🔍 Initializing API Detective for ${this.capturedData.siteName}...\n`);
    
    this.browser = await chromium.launch({ 
      headless: false, // Set to true for headless mode
      devtools: true,
      slowMo: 100 // Slow down by 100ms to better see what's happening
    });
    
    this.context = await this.browser.newContext({
      viewport: { width: 1920, height: 1080 },
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    });

    // Set up request interception
    await this.setupRequestInterception();
    
    // Set up response handling
    await this.setupResponseHandling();
  }

  private async setupRequestInterception(): Promise<void> {
    if (!this.context) return;

    await this.context.route('**/*', async (route) => {
      const request = route.request();
      const reqUrl = request.url();
      
      // Look for API-like patterns
      if (this.isAPIRequest(reqUrl)) {
        console.log(`\n📡 ${request.method()} ${reqUrl}`);
        
        const reqHeaders = request.headers();
        console.log('📋 Request Headers:', JSON.stringify(reqHeaders, null, 2));
        
        // Capture payload for POST/PUT requests
        let payload;
        try {
          const postData = request.postData();
          if (postData) {
            // Try to parse as JSON first
            try {
              payload = JSON.parse(postData);
            } catch {
              payload = postData;
            }
            console.log('📦 Request Payload:', JSON.stringify(payload, null, 2));
          }
        } catch (error) {
          console.log('⚠️ Error reading payload:', error.message);
        }

        // Store the API call
        const apiCall: APICall = {
          timestamp: new Date().toISOString(),
          url: reqUrl,
          method: request.method(),
          headers: reqHeaders,
          payload: payload
        };

        this.capturedData.apiCalls.push(apiCall);

        // Capture auth-related headers
        this.extractAuthHeaders(reqHeaders);
      }
      
      await route.continue();
    });
  }

  private async setupResponseHandling(): Promise<void> {
    if (!this.context) return;

    const page = await this.context.newPage();
    
    page.on('response', async (response) => {
      const resUrl = response.url();
      
      if (this.isAPIRequest(resUrl)) {
        console.log(`\n📨 ${response.status()} ${resUrl}`);
        
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
          
          // Show response (truncated for large responses)
          const responseStr = typeof body === 'string' ? body : JSON.stringify(body, null, 2);
          console.log('📄 Response:', responseStr.substring(0, 500) + (responseStr.length > 500 ? '...' : ''));
          
          // Find and update the corresponding request
          const call = this.capturedData.apiCalls.find(c => c.url === resUrl && !c.response);
          if (call) {
            call.response = body;
            call.responseHeaders = response.headers();
            call.status = response.status();
            
            if (isStreaming) {
              this.capturedData.notes.push(`Streaming endpoint detected: ${resUrl}`);
            }
          }
        } catch (error: any) {
          console.log('❌ Error reading response:', error.message);
          
          // Still record the attempt
          const call = this.capturedData.apiCalls.find(c => c.url === resUrl && !c.response);
          if (call) {
            call.response = `<Error reading response: ${error.message}>`;
            call.responseHeaders = response.headers();
            call.status = response.status();
          }
        }
      }
    });

    return page;
  }

  private isAPIRequest(url: string): boolean {
    const apiPatterns = [
      '/api/',
      '/chat',
      '/v1/',
      '/v2/',
      '/stream',
      '/completion',
      '/generate',
      '/models',
      '/auth',
      '/token',
      '/session',
      '/conversation',
      '/message',
      '/prompt',
      '/infer',
      '/llm'
    ];
    
    return apiPatterns.some(pattern => url.includes(pattern)) ||
           url.includes('openai') ||
           url.includes('anthropic') ||
           url.includes('claude') ||
           url.includes('gpt');
  }

  private extractAuthHeaders(headers: Record<string, string>): void {
    Object.keys(headers).forEach(key => {
      const lowerKey = key.toLowerCase();
      if (lowerKey.includes('auth') || 
          lowerKey.includes('token') ||
          lowerKey.includes('key') ||
          lowerKey.includes('bearer') ||
          lowerKey.includes('session')) {
        this.capturedData.authHeaders[key] = headers[key];
      }
    });
  }

  async capture(): Promise<Page> {
    if (!this.context) {
      throw new Error('Context not initialized');
    }

    const page = await this.context.newPage();
    
    console.log(`\n🚀 Navigating to ${this.capturedData.url}...\n`);
    await page.goto(this.capturedData.url, { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });
    
    console.log('\n🎯 INSTRUCTIONS:');
    console.log('1. Select a model (e.g., Claude 4, GPT-5, etc.)');
    console.log('2. Send a test message: "Write hello world in Python"');
    console.log('3. Wait for the response to complete');
    console.log('4. Try sending a few more test messages');
    console.log('5. Press Ctrl+C here to save the captured data\n');
    console.log('📡 Capturing API calls... (Press Ctrl+C to stop)\n');
    
    return page;
  }

  async saveData(): Promise<void> {
    const filename = `${this.capturedData.siteName}-${Date.now()}.json`;
    const filepath = path.join(this.outputDir, filename);
    
    // Add summary statistics
    const summary = {
      totalApiCalls: this.capturedData.apiCalls.length,
      uniqueEndpoints: [...new Set(this.capturedData.apiCalls.map(call => call.url))].length,
      hasAuth: Object.keys(this.capturedData.authHeaders).length > 0,
      streamingEndpoints: this.capturedData.apiCalls.filter(call => 
        call.responseHeaders?.['content-type']?.includes('text/event-stream')
      ).length,
      postRequests: this.capturedData.apiCalls.filter(call => call.method === 'POST').length,
      getRequests: this.capturedData.apiCalls.filter(call => call.method === 'GET').length
    };
    
    const output = {
      ...this.capturedData,
      summary,
      analysis: this.generateAnalysis()
    };
    
    fs.writeFileSync(filepath, JSON.stringify(output, null, 2));
    console.log(`\n💾 Data saved to: ${filepath}`);
    
    // Also save a readable summary
    const summaryFile = path.join(this.outputDir, `${this.capturedData.siteName}-summary-${Date.now()}.md`);
    fs.writeFileSync(summaryFile, this.generateMarkdownSummary(summary));
    console.log(`📄 Summary saved to: ${summaryFile}`);
  }

  private generateAnalysis(): any {
    const endpoints = [...new Set(this.capturedData.apiCalls.map(call => call.url))];
    const authTypes = Object.keys(this.capturedData.authHeaders).map(key => ({
      header: key,
      type: this.inferAuthType(key, this.capturedData.authHeaders[key])
    }));
    
    return {
      endpoints,
      authTypes,
      streamingDetected: this.capturedData.apiCalls.some(call => 
        call.responseHeaders?.['content-type']?.includes('text/event-stream')
      ),
      likelyChatEndpoint: this.findLikelyChatEndpoint(),
      likelyModelsEndpoint: this.findLikelyModelsEndpoint()
    };
  }

  private inferAuthType(headerName: string, headerValue: string): string {
    const value = headerValue || '';
    if (value.startsWith('Bearer ')) return 'Bearer Token';
    if (value.startsWith('sk-')) return 'API Key (OpenAI-style)';
    if (headerName.toLowerCase().includes('session')) return 'Session Cookie';
    if (headerName.toLowerCase().includes('csrf')) return 'CSRF Token';
    return 'Unknown';
  }

  private findLikelyChatEndpoint(): string | null {
    const chatPatterns = ['/chat', '/completion', '/generate', '/prompt', '/message'];
    const endpoints = this.capturedData.apiCalls.filter(call => 
      call.method === 'POST' && 
      chatPatterns.some(pattern => call.url.includes(pattern))
    );
    
    return endpoints.length > 0 ? endpoints[0].url : null;
  }

  private findLikelyModelsEndpoint(): string | null {
    const modelsPatterns = ['/models', '/v1/models', '/available-models'];
    const endpoints = this.capturedData.apiCalls.filter(call => 
      call.method === 'GET' && 
      modelsPatterns.some(pattern => call.url.includes(pattern))
    );
    
    return endpoints.length > 0 ? endpoints[0].url : null;
  }

  private generateMarkdownSummary(summary: any): string {
    return `# API Capture Summary: ${this.capturedData.siteName}

## Basic Info
- **Site**: ${this.capturedData.url}
- **Capture Time**: ${this.capturedData.captureTime}
- **Total API Calls**: ${summary.totalApiCalls}
- **Unique Endpoints**: ${summary.uniqueEndpoints}

## Authentication
- **Auth Detected**: ${summary.hasAuth ? '✅ Yes' : '❌ No'}
- **Auth Headers**: ${Object.keys(this.capturedData.authHeaders).length}

${summary.hasAuth ? `
### Auth Headers Found:
${Object.entries(this.capturedData.authHeaders).map(([key, value]) => 
  `- **${key}**: \`${value.substring(0, 20)}...\``
).join('\n')}
` : ''}

## Request Types
- **POST Requests**: ${summary.postRequests}
- **GET Requests**: ${summary.getRequests}
- **Streaming Endpoints**: ${summary.streamingEndpoints}

## Key Endpoints
${this.generateAnalysis().likelyChatEndpoint ? 
  `- **Chat**: \`${this.generateAnalysis().likelyChatEndpoint}\`` : ''
}
${this.generateAnalysis().likelyModelsEndpoint ? 
  `- **Models**: \`${this.generateAnalysis().likelyModelsEndpoint}\`` : ''
}

## Next Steps
1. Review the full JSON data file for detailed request/response structures
2. Identify authentication requirements
3. Extract the exact payload structure for chat requests
4. Build DirectAPIAgent based on these findings

---
*Generated by API Detective*`;
  }

  async cleanup(): Promise<void> {
    if (this.browser) {
      await this.browser.close();
    }
  }
}

// Main execution function
async function runAPIDetective(siteName: string, url: string): Promise<void> {
  const detective = new APIDetective(siteName, url);
  
  try {
    await detective.initialize();
    const page = await detective.capture();
    
    // Wait for manual interaction (Ctrl+C to stop)
    await new Promise(() => {}); // Infinite wait
    
  } catch (error: any) {
    console.error('❌ Error:', error.message);
  } finally {
    await detective.saveData();
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
  { name: 'ish-chat', url: 'https://ish.chat' },
  { name: 'eqing-tech', url: 'https://chat3.eqing.tech' }
];

// Run first site by default, or accept command line argument
const targetSite = process.argv[2] ? 
  sites.find(s => s.name === process.argv[2]) || sites[0] : 
  sites[0];

console.log(`🚀 Starting API Detective for ${targetSite.name}...`);
runAPIDetective(targetSite.name, targetSite.url);