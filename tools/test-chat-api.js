const axios = require('axios');

class ChatAPITester {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
    this.client = axios.create({
      baseURL: baseUrl,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      }
    });
  }

  async testModelsEndpoint() {
    try {
      console.log('🔍 Testing models endpoint...');
      const response = await this.client.get('/v1/models');
      console.log('✅ Models endpoint works!');
      console.log(`Found ${response.data.data.length} models`);
      
      // Extract model IDs
      const models = response.data.data.map(model => model.id);
      console.log('Available models:', models);
      
      return models;
    } catch (error) {
      console.error('❌ Models endpoint failed:', error.response?.status, error.message);
      return [];
    }
  }

  async testChatCompletion(model, message = "Hello! Write a simple hello world in Python.") {
    try {
      console.log(`\n🔍 Testing chat completion with model: ${model}`);
      
      const payload = {
        model: model,
        messages: [
          {
            role: "user",
            content: message
          }
        ],
        max_tokens: 150,
        temperature: 0.7
      };

      const response = await this.client.post('/v1/chat/completions', payload);
      console.log('✅ Chat completion works!');
      console.log('Response:', response.data.choices[0].message.content);
      
      return response.data;
    } catch (error) {
      console.error(`❌ Chat completion failed for ${model}:`, error.response?.status, error.message);
      
      if (error.response?.data) {
        console.error('Error details:', error.response.data);
      }
      
      return null;
    }
  }

  async runTests() {
    console.log(`🚀 Testing Chat API at: ${this.baseUrl}\n`);
    
    // Test models endpoint first
    const models = await this.testModelsEndpoint();
    
    if (models.length === 0) {
      console.log('❌ No models found, cannot test chat completions');
      return;
    }

    // Test chat completions with available models
    const results = [];
    
    // Test first few models to avoid too many requests
    const testModels = models.slice(0, 3);
    
    for (const model of testModels) {
      const result = await this.testChatCompletion(model);
      if (result) {
        results.push({
          model,
          response: result,
          success: true
        });
      }
    }

    // Summary
    console.log(`\n📊 Test Summary:`);
    console.log(`- Total models available: ${models.length}`);
    console.log(`- Models tested: ${testModels.length}`);
    console.log(`- Successful chat completions: ${results.length}`);
    
    if (results.length > 0) {
      console.log(`\n🎉 Working models:`);
      results.forEach(result => {
        console.log(`  ✅ ${result.model}`);
      });
      
      // Return the first successful result for further analysis
      return results[0];
    } else {
      console.log(`\n❌ No working chat completions found`);
      return null;
    }
  }
}

// Test different sites
async function testSites() {
  const sites = [
    { name: 'eqing-tech', url: 'https://chat3.eqing.tech' },
    { name: 'ish-chat-gateway', url: 'https://ish.chat/gateway' },
    { name: 'ish-chat-api', url: 'https://ish.chat/api' }
  ];

  const results = [];

  for (const site of sites) {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`Testing: ${site.name} (${site.url})`);
    console.log(`${'='.repeat(60)}`);
    
    const tester = new ChatAPITester(site.url);
    const result = await tester.runTests();
    
    if (result) {
      results.push({
        site: site.name,
        url: site.url,
        ...result
      });
    }
    
    // Add delay between sites to avoid rate limiting
    await new Promise(resolve => setTimeout(resolve, 2000));
  }

  // Final summary
  console.log(`\n${'='.repeat(60)}`);
  console.log(`FINAL SUMMARY`);
  console.log(`${'='.repeat(60)}`);
  
  if (results.length > 0) {
    console.log(`🎉 Found ${results.length} working Chat API endpoints:`);
    results.forEach(result => {
      console.log(`  ✅ ${result.site}: ${result.url} (model: ${result.model})`);
    });
    
    console.log(`\n📝 Ready to build DirectAPIAgent! Use the endpoint information above.`);
  } else {
    console.log(`❌ No working Chat API endpoints found.`);
    console.log(`\n💡 Recommendations:`);
    console.log(`1. Sites may require authentication (API keys, tokens)`);
    console.log(`2. Sites may use different endpoint patterns`);
    console.log(`3. Sites may require browser session/cookies`);
  }

  return results;
}

// Run the tests
if (require.main === module) {
  testSites().catch(console.error);
}

module.exports = { ChatAPITester };