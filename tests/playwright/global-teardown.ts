// tests/playwright/global-teardown.ts
import { FullConfig } from '@playwright/test'

async function globalTeardown(config: FullConfig) {
  console.log('')
  console.log('🏁 TraderTerminal Playwright Tests Complete')
  console.log('==========================================')
  
  // Generate final test report
  const fs = require('fs')
  const path = require('path')
  
  const reportsDir = 'tests/reports'
  const screenshotsDir = 'tests/screenshots'
  
  try {
    // Count test artifacts
    const reports = fs.existsSync(reportsDir) ? fs.readdirSync(reportsDir) : []
    const screenshots = fs.existsSync(screenshotsDir) ? fs.readdirSync(screenshotsDir) : []
    
    console.log(`📊 Generated ${reports.length} test reports`)
    console.log(`📸 Captured ${screenshots.length} screenshots`)
    
    // Generate summary report
    const summary = {
      timestamp: new Date().toISOString(),
      testRun: {
        duration: Date.now(),
        reports: reports.length,
        screenshots: screenshots.length,
        config: {
          baseURL: config.use?.baseURL,
          projects: config.projects?.map(p => p.name) || [],
          workers: config.workers
        }
      },
      artifacts: {
        reports: reports.filter(f => f.endsWith('.json')),
        networkReports: reports.filter(f => f.includes('network-report')),
        performanceReports: reports.filter(f => f.includes('performance')),
        screenshots: screenshots.filter(f => f.endsWith('.png'))
      }
    }
    
    fs.writeFileSync(
      path.join(reportsDir, 'test-run-summary.json'),
      JSON.stringify(summary, null, 2)
    )
    
    console.log(`📋 Test summary: ${path.join(reportsDir, 'test-run-summary.json')}`)
    
    // Show key metrics if available
    const performanceReports = reports.filter(f => f.includes('performance'))
    if (performanceReports.length > 0) {
      try {
        const latestPerf = performanceReports[performanceReports.length - 1]
        const perfData = JSON.parse(fs.readFileSync(path.join(reportsDir, latestPerf), 'utf8'))
        
        if (perfData.summary) {
          console.log('')
          console.log('⚡ Performance Summary:')
          console.log(`   Page Load: ${perfData.summary.pageLoadTime || 0}ms`)
          console.log(`   Memory Usage: ${perfData.summary.memoryUsageMB || 0}MB`)
          console.log(`   Network Calls: ${perfData.summary.networkCalls || 0}`)
          console.log(`   WebSocket Latency: ${perfData.summary.webSocketLatency || 0}ms`)
        }
      } catch (e) {
        // Performance report parsing failed, but continue
      }
    }
    
    // Show network summary if available
    const networkReports = reports.filter(f => f.includes('network-report'))
    if (networkReports.length > 0) {
      try {
        const latestNetwork = networkReports[networkReports.length - 1]
        const networkData = JSON.parse(fs.readFileSync(path.join(reportsDir, latestNetwork), 'utf8'))
        
        if (networkData.summary) {
          console.log('')
          console.log('🌐 Network Summary:')
          console.log(`   Total Requests: ${networkData.summary.totalRequests || 0}`)
          console.log(`   Success Rate: ${networkData.summary.successRate || 0}%`)
          console.log(`   Failed Requests: ${networkData.summary.failedRequests || 0}`)
          console.log(`   WebSocket Messages: ${networkData.summary.webSocketMessages || 0}`)
        }
      } catch (e) {
        // Network report parsing failed, but continue
      }
    }
    
  } catch (error) {
    console.log('⚠️  Could not generate test summary, but tests completed')
  }
  
  console.log('')
  console.log('📁 Test artifacts:')
  console.log(`   Reports: ${reportsDir}/`)
  console.log(`   Screenshots: ${screenshotsDir}/`)
  console.log(`   HTML Report: playwright-report/index.html`)
  console.log('')
  console.log('✅ TraderTerminal testing framework ready!')
  console.log('   Run: npx playwright test')
  console.log('   View: npx playwright show-report')
}

export default globalTeardown