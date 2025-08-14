# Tests Directory

This directory contains all test files for the AI Keyword Strategy Generator, organized by test type.

## Directory Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── test_scoring.py      # Tests for scoring algorithms
│   ├── test_services.py     # Tests for service layer
│   ├── test_app.py          # Tests for main app functionality
│   ├── test_utils.py        # Tests for utility functions
│   ├── test_refactor.py     # Tests for refactored components
│   └── test_color_styling.py # Tests for UI styling
├── e2e/                     # End-to-end integration tests
│   └── test_complete_workflow.py # Full workflow testing
└── dev_utils/               # Development and debugging utilities
    ├── smoke_brief_renderer.py   # Quick functionality tests
    ├── debug_brief.py            # Debug utilities
    └── manual_smoke_test.py      # Manual testing utilities
```

## Test Categories

### Unit Tests (`tests/unit/`)
- **test_scoring.py** - Scoring algorithms and keyword prioritization
- **test_services.py** - Service layer functionality and API integration
- **test_app.py** - Main application functionality and UI components  
- **test_utils.py** - Utility functions and helpers
- **test_refactor.py** - Refactored components and backward compatibility
- **test_color_styling.py** - UI color coding and styling

### End-to-End Tests (`tests/e2e/`)
- **test_complete_workflow.py** - Full workflow integration testing

### Development Utilities (`tests/dev_utils/`)
- **smoke_brief_renderer.py** - Quick smoke test for brief renderer
- **debug_brief.py** - Debug utilities for content brief generation
- **manual_smoke_test.py** - Manual testing and validation utilities

## Running Tests

### Basic Test Run
```bash
# Activate virtual environment first
.\venv\Scripts\Activate.ps1

# Run all tests
python -m pytest tests/ -v

# Or use the test runner script
python run_tests.py
```

### Advanced Options
```bash
# Run specific test class
python -m pytest tests/test_app.py::TestUtilityFunctions -v

# Run specific test
python -m pytest tests/test_app.py::TestUtilityFunctions::test_slugify_basic -v

# Run with coverage (requires pytest-cov)
pip install pytest-cov
python run_tests.py --coverage
```

### Test Output
- ✅ **PASSED** - Test executed successfully
- ❌ **FAILED** - Test failed, check error message
- **SKIPPED** - Test was skipped (if any)

## Test Dependencies

### Required Packages
```
pytest>=7.0.0          # Testing framework
pytest-mock>=3.10.0    # Mocking utilities
pandas>=1.5.0          # Data processing (already required by app)
```

### Mocking
Tests use mocking for:
- OpenAI API calls (to avoid real API usage during testing)
- Streamlit components (to test without UI rendering)
- Environment variables (to test different configurations)

## Best Practices

### Writing New Tests
1. **Follow naming convention**: `test_function_name_scenario()`
2. **Use descriptive docstrings**: Explain what the test validates
3. **Test both success and failure cases**
4. **Mock external dependencies** (API calls, file operations)
5. **Use fixtures for common test data**

### Test Organization
- Group related tests in classes
- Use clear, descriptive test names
- Test one thing per test function
- Include both positive and negative test cases

### Example Test Structure
```python
class TestNewFeature:
    """Test new feature functionality."""
    
    def test_feature_success_case(self):
        """Test that feature works with valid input."""
        # Arrange
        input_data = "valid input"
        
        # Act
        result = new_feature(input_data)
        
        # Assert
        assert result == expected_output
    
    def test_feature_error_case(self):
        """Test that feature handles invalid input."""
        with pytest.raises(ValueError):
            new_feature("invalid input")
```

## Continuous Integration

### Local Testing Workflow
1. Make code changes
2. Run tests: `python run_tests.py`
3. Fix any failing tests
4. Commit changes

### CI/CD Integration
The test suite is designed to work with CI/CD systems:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    pip install -r requirements.txt
    python -m pytest tests/ -v
```

## Troubleshooting

### Common Issues

#### Import Errors
```
ModuleNotFoundError: No module named 'app'
```
**Solution**: Ensure you're running tests from the project root directory.

#### Pytest Not Found
```
pytest: command not found
```
**Solution**: Install pytest: `pip install pytest`

#### Mock Failures
```
AttributeError: Mock object has no attribute 'xyz'
```
**Solution**: Check that mocks are configured correctly for the objects being tested.

### Debug Mode
Run tests with more verbose output:
```bash
python -m pytest tests/ -v -s --tb=long
```

## Coverage Reporting

Generate test coverage reports to see which parts of your code are tested:

```bash
# Install coverage tools
pip install pytest-cov

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html

# View report
open htmlcov/index.html
```

## Future Enhancements

### Potential Test Additions
1. **Integration tests** - Test full workflow end-to-end
2. **Performance tests** - Test response times and memory usage
3. **Security tests** - Test API key handling and input sanitization
4. **UI tests** - Test Streamlit interface with selenium
5. **Load tests** - Test behavior under high usage

### Test Data Management
Consider adding:
- Fixture files with sample data
- Test database for integration tests
- Mock API responses for different scenarios
