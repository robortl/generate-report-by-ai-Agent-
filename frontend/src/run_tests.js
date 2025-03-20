#!/usr/bin/env node
/**
 * 前端测试运行脚本
 * 
 * 使用方法：
 * - 运行所有测试: node run_tests.js
 * - 运行特定测试: node run_tests.js components/FileUploader
 */

const { execSync } = require('child_process');
const path = require('path');

// 测试命令
const TEST_COMMAND = 'npm test';

// 运行测试
function runTests() {
  console.log('=== 开始运行前端测试 ===');
  
  try {
    // 如果指定了测试文件，则只运行指定的测试
    const testPath = process.argv[2];
    const command = testPath ? `${TEST_COMMAND} -- ${testPath}` : TEST_COMMAND;
    
    // 执行测试命令
    execSync(command, { stdio: 'inherit' });
    
    console.log('=== 前端测试完成 ===');
    process.exit(0);
  } catch (error) {
    console.error('测试失败:', error.message);
    process.exit(1);
  }
}

// 运行测试
runTests(); 