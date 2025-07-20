#!/usr/bin/env node
/**
 * Automated TraderTerminal Dashboard Testing with Playwright
 * 
 * This script uses headless Chromium to:
 * 1. Navigate to the TraderTerminal dashboard
 * 2. Monitor network requests and console errors
 * 3. Identify specific connection issues
 * 4. Test frontend-backend integration
 * 5. Provide detailed debugging information
 */

const { chromium } = require('playwright');

async function testTraderTerminalDashboard() {
    console.log('🚀 Starting TraderTerminal Dashboard Automated Test');
    console.log('=' * 60);

    const browser = await chromium.launch({ 
        headless: true,
        args: ['--disable-web-security', '--disable-features=VizDisplayCompositor']
    });
    
    const context = await browser.newContext({
        userAgent: 'TraderTerminal-Automation/1.0 (Playwright)',
    });

    const page = await context.newPage();

    // Collect network requests and errors
    const networkRequests = [];
    const consoleErrors = [];
    const networkFailures = [];

    // Monitor network requests
    page.on('request', (request) => {
        networkRequests.push({
            url: request.url(),
            method: request.method(),
            timestamp: new Date().toISOString()
        });
        console.log(`📡 REQUEST: ${request.method()} ${request.url()}`);
    });

    // Monitor network responses
    page.on('response', (response) => {
        const status = response.status();
        const url = response.url();
        
        if (status >= 400) {
            networkFailures.push({
                url,
                status,
                statusText: response.statusText(),
                timestamp: new Date().toISOString()
            });
            console.log(`❌ FAILED: ${status} ${url}`);
        } else {
            console.log(`✅ SUCCESS: ${status} ${url}`);
        }
    });

    // Monitor console messages
    page.on('console', (msg) => {
        const type = msg.type();
        const text = msg.text();
        
        if (type === 'error') {
            consoleErrors.push({
                text,
                timestamp: new Date().toISOString()
            });
            console.log(`🔴 CONSOLE ERROR: ${text}`);
        } else if (type === 'warning') {
            console.log(`🟡 CONSOLE WARNING: ${text}`);
        } else {
            console.log(`📝 CONSOLE: ${text}`);
        }
    });

    // Monitor page errors
    page.on('pageerror', (error) => {
        consoleErrors.push({
            text: error.message,
            stack: error.stack,
            timestamp: new Date().toISOString()
        });
        console.log(`💥 PAGE ERROR: ${error.message}`);
    });

    try {
        console.log('\n🌐 Step 1: Navigating to TraderTerminal Dashboard');
        
        // Navigate to the dashboard
        const response = await page.goto('http://localhost:8000', {
            waitUntil: 'domcontentloaded',
            timeout: 30000
        });

        console.log(`📊 Initial page load: ${response.status()}`);

        // Wait for the page to fully load
        console.log('\n⏳ Step 2: Waiting for page initialization');
        await page.waitForTimeout(3000);

        // Check if the main dashboard elements are present
        console.log('\n🔍 Step 3: Checking dashboard elements');
        
        const dashboardTitle = await page.textContent('h1, h2, .dashboard-title').catch(() => null);
        console.log(`📋 Dashboard title: ${dashboardTitle || 'Not found'}`);

        // Look for connection status indicators
        const connectionElements = await page.$$eval('[class*="connect"], [class*="status"], [id*="status"]', 
            elements => elements.map(el => ({
                text: el.textContent,
                className: el.className,
                id: el.id
            }))
        ).catch(() => []);

        console.log('\n🔌 Step 4: Connection Status Analysis');
        connectionElements.forEach(el => {
            console.log(`   Status Element: "${el.text}" (class: ${el.className}, id: ${el.id})`);
        });

        // Check for error dialogs or messages
        const errorElements = await page.$$eval('[class*="error"], [class*="alert"], .connection-error', 
            elements => elements.map(el => ({
                text: el.textContent,
                visible: el.offsetParent !== null
            }))
        ).catch(() => []);

        console.log('\n⚠️  Step 5: Error Message Analysis');
        errorElements.forEach(el => {
            if (el.visible) {
                console.log(`   🚨 VISIBLE ERROR: "${el.text}"`);
            }
        });

        // Test API endpoints directly from the browser
        console.log('\n🧪 Step 6: Testing API endpoints from browser context');
        
        const apiTests = [
            'http://localhost:8080/health',
            'http://localhost:8080/status',
            'http://localhost:8000/health',
            'http://localhost:8000/api/v1/health'
        ];

        for (const endpoint of apiTests) {
            try {
                const apiResponse = await page.evaluate(async (url) => {
                    try {
                        const response = await fetch(url);
                        return {
                            status: response.status,
                            ok: response.ok,
                            data: await response.text()
                        };
                    } catch (error) {
                        return {
                            status: 0,
                            ok: false,
                            error: error.message
                        };
                    }
                }, endpoint);

                if (apiResponse.ok) {
                    console.log(`   ✅ ${endpoint}: ${apiResponse.status}`);
                } else {
                    console.log(`   ❌ ${endpoint}: ${apiResponse.status || 'FAILED'} - ${apiResponse.error || 'Unknown error'}`);
                }
            } catch (error) {
                console.log(`   💥 ${endpoint}: Exception - ${error.message}`);
            }
        }

        // Check local storage and session storage
        console.log('\n💾 Step 7: Storage Analysis');
        const localStorage = await page.evaluate(() => Object.keys(localStorage));
        const sessionStorage = await page.evaluate(() => Object.keys(sessionStorage));
        
        console.log(`   Local Storage keys: ${localStorage.join(', ') || 'None'}`);
        console.log(`   Session Storage keys: ${sessionStorage.join(', ') || 'None'}`);

        // Look for JavaScript variables that might indicate configuration
        console.log('\n⚙️  Step 8: JavaScript Configuration Analysis');
        const jsConfig = await page.evaluate(() => {
            const config = {};
            
            // Look for common configuration variables
            if (typeof window.API_BASE_URL !== 'undefined') config.API_BASE_URL = window.API_BASE_URL;
            if (typeof window.WS_URL !== 'undefined') config.WS_URL = window.WS_URL;
            if (typeof window.ENV !== 'undefined') config.ENV = window.ENV;
            
            return config;
        });

        console.log(`   JS Config: ${JSON.stringify(jsConfig, null, 2)}`);

        // Wait a bit longer to see if any delayed connections happen
        console.log('\n⏱️  Step 9: Waiting for delayed connections (10 seconds)');
        await page.waitForTimeout(10000);

        // Take a screenshot for visual debugging
        console.log('\n📸 Step 10: Taking screenshot for visual analysis');
        await page.screenshot({ 
            path: 'dashboard-test-screenshot.png', 
            fullPage: true 
        });

    } catch (error) {
        console.log(`💥 Navigation Error: ${error.message}`);
    }

    // Final report
    console.log('\n📊 FINAL ANALYSIS REPORT');
    console.log('=' * 40);
    
    console.log(`\n🌐 Network Requests: ${networkRequests.length}`);
    networkRequests.forEach(req => {
        console.log(`   ${req.method} ${req.url}`);
    });

    console.log(`\n❌ Network Failures: ${networkFailures.length}`);
    networkFailures.forEach(fail => {
        console.log(`   ${fail.status} ${fail.url} - ${fail.statusText}`);
    });

    console.log(`\n🔴 Console Errors: ${consoleErrors.length}`);
    consoleErrors.forEach(error => {
        console.log(`   ${error.text}`);
        if (error.stack) {
            console.log(`   Stack: ${error.stack.split('\n')[0]}`);
        }
    });

    // Recommendations
    console.log('\n💡 RECOMMENDATIONS');
    console.log('=' * 20);
    
    if (networkFailures.length > 0) {
        console.log('🔧 Network failures detected - check CORS configuration and endpoint availability');
    }
    
    if (consoleErrors.length > 0) {
        console.log('🐛 JavaScript errors detected - check browser console for details');
    }
    
    if (networkRequests.filter(req => req.url.includes('localhost:8080')).length === 0) {
        console.log('⚠️  No requests to localhost:8080 detected - frontend may be misconfigured');
    }

    console.log('\n✅ Test completed. Screenshot saved as: dashboard-test-screenshot.png');

    await browser.close();
}

// Run the test
testTraderTerminalDashboard()
    .then(() => {
        console.log('\n🎉 Automated test completed successfully');
        process.exit(0);
    })
    .catch((error) => {
        console.error('\n💥 Test failed:', error);
        process.exit(1);
    });