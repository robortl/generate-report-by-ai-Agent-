# Testing Documentation
# テストドキュメント

This document details the testing strategy and execution methods for the report generation system.

## Table of Contents
## 目次

- [Testing Strategy](#testing-strategy)
- [Backend Testing](#backend-testing)
- [Frontend Testing](#frontend-testing)
- [Integration Testing](#integration-testing)
- [Test Coverage](#test-coverage)

## Testing Strategy
## テスト戦略

This project adopts a multi-level testing strategy:

1. **Unit Testing**: Testing individual components and functions
2. **Integration Testing**: Testing component interactions and API calls
3. **End-to-End Testing**: Testing complete user workflows

Testing Tools:
- Backend: pytest
- Frontend: Jest and React Testing Library

## Backend Testing
## バックエンドテスト

### Running Backend Tests
### バックエンドテストの実行

Execute the following command in the project root directory:

```bash
cd backend
python tests/run_tests.py
```

To run specific test files:

```bash
python tests/run_tests.py tests/test_upload.py
```

### Backend Test Coverage
### バックエンドテストカバレッジ

1. **API Unit Tests**:
   - `test_upload.py`: Tests file upload related APIs
   - `test_files.py`: Tests file list related APIs
   - `test_report.py`: Tests report generation related APIs

2. **API Integration Tests**:
   - `integration/test_api_integration.py`: Tests integration between API endpoints

## Frontend Testing
## フロントエンドテスト

### Running Frontend Tests
### フロントエンドテストの実行

Execute the following command in the project root directory:

```bash
cd frontend
node src/run_tests.js
```

To run specific test files:

```bash
node src/run_tests.js src/components/__tests__/FileUploader.test.js
```

Or use npm directly:

```bash
npm test
```

### Frontend Test Coverage
### フロントエンドテストカバレッジ

1. **Service Tests**:
   - `services/__tests__/api.test.js`: Tests API services

2. **Component Tests**:
   - `components/__tests__/FileUploader.test.js`: Tests file upload component

3. **Application Integration Tests**:
   - `__tests__/App.test.js`: Tests application integration features

## Integration Testing
## 統合テスト

Integration tests verify interactions between frontend and backend.

### Running Integration Tests
### 統合テストの実行

1. First, start the backend service:

```bash
cd backend
flask run
```

2. Then run the integration tests:

```bash
cd backend
python tests/integration/test_api_integration.py
```

## Test Coverage
## テストカバレッジ

### Backend Test Coverage
### バックエンドテストカバレッジ

- **Upload Functionality**:
  - File type validation
  - File upload processing
  - Metadata saving
  - Error handling

- **File Management**:
  - File list retrieval
  - Category filtering
  - Pagination functionality

- **Report Generation**:
  - Report creation
  - Report retrieval
  - Report updates

### Frontend Test Coverage
### フロントエンドテストカバレッジ

- **API Services**:
  - API calls
  - Error handling

- **Component Functionality**:
  - File upload
  - Category selection
  - Form validation
  - Error messages

- **Application Flow**:
  - Navigation functionality
  - Page rendering
  - User interactions
  - Complete workflow testing

## Continuous Integration
## 継続的インテグレーション

This project can be configured with CI/CD workflows to automatically run tests on each code commit.

### GitHub Actions Configuration Example
### GitHub Actions設定例

Add the following configuration to `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest pytest-cov
    - name: Run tests
      run: |
        cd backend
        python tests/run_tests.py

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Node.js
      uses: actions/setup-node@v2
      with:
        node-version: 16
    - name: Install dependencies
      run: |
        cd frontend
        npm install
    - name: Run tests
      run: |
        cd frontend
        npm test
``` 