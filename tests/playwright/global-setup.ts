// tests/playwright/global-setup.ts
import { chromium, FullConfig } from '@playwright/test'

async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting TraderTerminal Playwright Test Suite')
  console.log('===============================================')
  
  // Create reports directory
  const fs = require('fs')
  const reportsDir = 'tests/reports'
  const screenshotsDir = 'tests/screenshots'
  
  if (!fs.existsSync(reportsDir)) {
    fs.mkdirSync(reportsDir, { recursive: true })
  }
  
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true })
  }
  
  // Wait for backend to be ready
  const browser = await chromium.launch()
  const page = await browser.newPage()
  
  console.log('⏳ Waiting for backend to start...')
  
  let backendReady = false
  let attempts = 0
  const maxAttempts = 60 // 2 minutes
  
  while (!backendReady && attempts < maxAttempts) {
    try {
      const response = await page.goto('http://localhost:8000/health', { 
        waitUntil: 'networkidle',
        timeout: 5000 
      })
      
      if (response && response.ok()) {
        backendReady = true
        console.log('✅ Backend is ready')
      }
    } catch (error) {
      attempts++
      await new Promise(resolve => setTimeout(resolve, 2000))
    }
  }
  
  if (!backendReady) {
    throw new Error('❌ Backend failed to start within 2 minutes')
  }
  
  // Test basic API functionality
  try {
    await page.goto('http://localhost:8000/api/health')
    const healthCheck = await page.evaluate(() => {
      return fetch('/api/health').then(r => r.json()).catch(() => null)
    })
    
    if (healthCheck && healthCheck.status === 'healthy') {
      console.log('✅ API health check passed')
    } else {
      console.log('⚠️  API health check failed, but continuing...')
    }
  } catch (error) {
    console.log('⚠️  Could not perform API health check, but continuing...')
  }
  
  // Test WebSocket connection
  try {
    const wsConnected = await page.evaluate(() => {
      return new Promise((resolve) => {
        const ws = new WebSocket('ws://localhost:8000/ws')
        ws.onopen = () => {
          ws.close()
          resolve(true)
        }
        ws.onerror = () => resolve(false)
        setTimeout(() => resolve(false), 5000)
      })
    })
    
    if (wsConnected) {
      console.log('✅ WebSocket connection test passed')
    } else {
      console.log('⚠️  WebSocket connection test failed, but continuing...')
    }
  } catch (error) {
    console.log('⚠️  Could not test WebSocket connection, but continuing...')
  }
  
  await browser.close()
  
  console.log('🎯 Setup complete - starting tests')
  console.log('')
}

export default globalSetup