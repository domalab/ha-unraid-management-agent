# Testing Implementation Plan
## Unraid Management Agent Integration

**Goal:** Implement comprehensive automated testing to achieve Silver tier quality rating (≥90% test coverage)

---

## Why pytest-homeassistant-custom-component?

### Benefits

1. **Home Assistant Test Infrastructure**
   - Provides `hass` fixture for testing with a real Home Assistant instance
   - Includes `aioclient_mock` for mocking HTTP requests
   - Provides `hass_ws_client` for WebSocket testing
   - Includes all Home Assistant test utilities

2. **Pytest Ecosystem**
   - Industry-standard testing framework
   - Excellent plugin ecosystem
   - Great IDE integration
   - Powerful fixtures and parametrization

3. **Coverage Reporting**
   - Built-in coverage.py integration
   - HTML and terminal reports
   - Coverage badges for README

4. **CI/CD Integration**
   - Easy GitHub Actions integration
   - Automated testing on every PR
   - Prevents regressions

5. **Community Standard**
   - Used by most Home Assistant custom integrations
   - Well-documented patterns
   - Active community support

### Recommendation

**✅ STRONGLY RECOMMENDED** - This is the industry standard for Home Assistant custom component testing and is essential for achieving any quality tier rating.

---

## Implementation Roadmap

### Phase 1: Setup (Estimated: 2-4 hours)

**Goal:** Set up testing infrastructure

#### Step 1.1: Install Dependencies

Create `requirements_test.txt`:
```txt
pytest>=7.4.0
pytest-homeassistant-custom-component>=0.13.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.0
pytest-timeout>=2.1.0
aiohttp>=3.9.0
```

#### Step 1.2: Configure pytest

Create `pytest.ini`:
```ini
[pytest]
testpaths = tests
norecursedirs = .git
asyncio_mode = auto
timeout = 30

# Coverage settings
addopts =
    --cov=custom_components.unraid_management_agent
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    --strict-markers
    -v
```

#### Step 1.3: Create Test Directory Structure

```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures
├── const.py                       # Test constants
├── test_init.py                   # Integration setup/unload tests
├── test_config_flow.py            # Config flow tests
├── test_api_client.py             # API client tests
├── test_websocket_client.py       # WebSocket client tests
├── test_coordinator.py            # Coordinator tests
├── test_sensor.py                 # Sensor platform tests
├── test_binary_sensor.py          # Binary sensor tests
├── test_switch.py                 # Switch platform tests
├── test_button.py                 # Button platform tests
├── test_repairs.py                # Repair flow tests
└── fixtures/
    ├── api_responses.json         # Mock API responses
    └── websocket_events.json      # Mock WebSocket events
```

#### Step 1.4: Create Base Fixtures (`conftest.py`)

See example below in "Example Test Files" section.

---

### Phase 2: Core Tests (Estimated: 8-12 hours)

**Goal:** Test core functionality (config flow, API client, coordinator)

#### Priority Tests:

1. **Config Flow Tests** (`test_config_flow.py`)
   - User flow (successful setup)
   - User flow (connection errors)
   - User flow (timeout errors)
   - User flow (already configured)
   - Options flow (update interval)
   - Options flow (WebSocket toggle)
   - Import flow (if applicable)

2. **API Client Tests** (`test_api_client.py`)
   - Successful API calls
   - Timeout handling
   - Connection errors
   - Invalid JSON responses
   - Empty responses
   - HTTP error codes
   - All endpoint methods

3. **Coordinator Tests** (`test_coordinator.py`)
   - Initial data fetch
   - Update data
   - Error handling
   - WebSocket integration
   - Service calls

**Estimated Coverage After Phase 2:** ~60%

---

### Phase 3: Platform Tests (Estimated: 10-15 hours)

**Goal:** Test all entity platforms

#### Priority Tests:

1. **Sensor Tests** (`test_sensor.py`)
   - CPU usage sensor
   - RAM usage sensor
   - Temperature sensors
   - Disk usage sensors
   - UPS sensors
   - Network sensors
   - GPU sensors
   - Array sensors
   - Unique IDs
   - Device info
   - State attributes

2. **Binary Sensor Tests** (`test_binary_sensor.py`)
   - Array status
   - Parity check status
   - UPS status
   - Disk status
   - State changes

3. **Switch Tests** (`test_switch.py`)
   - Container switches
   - VM switches
   - Turn on/off
   - State updates

4. **Button Tests** (`test_button.py`)
   - Array start/stop
   - Parity check start/stop
   - Button press actions

**Estimated Coverage After Phase 3:** ~85%

---

### Phase 4: Advanced Tests (Estimated: 6-10 hours)

**Goal:** Achieve ≥90% coverage and test edge cases

#### Priority Tests:

1. **WebSocket Tests** (`test_websocket_client.py`)
   - Connection
   - Disconnection
   - Reconnection with backoff
   - Event handling
   - Error scenarios

2. **Repair Flow Tests** (`test_repairs.py`)
   - Connection failure repair
   - Disk issue repair
   - Repair flow creation

3. **Integration Tests** (`test_init.py`)
   - Setup entry
   - Unload entry
   - Reload entry
   - Service registration
   - Multiple entries

4. **Edge Cases**
   - Missing data handling
   - Null values
   - Invalid data types
   - Concurrent updates

**Estimated Coverage After Phase 4:** ≥90%

---

### Phase 5: CI/CD Setup (Estimated: 2-4 hours)

**Goal:** Automate testing on every PR

#### Step 5.1: Create GitHub Actions Workflow

Create `.github/workflows/test.yml`:
```yaml
name: Test

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements_test.txt

      - name: Run tests with coverage
        run: |
          pytest --cov --cov-report=xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true
```

#### Step 5.2: Add Coverage Badge to README

```markdown
[![Coverage](https://codecov.io/gh/domalab/unraid-management-agent/branch/main/graph/badge.svg)](https://codecov.io/gh/domalab/unraid-management-agent)
```

---

## Effort Estimation

| Phase | Tasks | Estimated Hours | Complexity |
|-------|-------|----------------|------------|
| Phase 1: Setup | Infrastructure setup | 2-4 hours | Low |
| Phase 2: Core Tests | Config flow, API, coordinator | 8-12 hours | Medium |
| Phase 3: Platform Tests | All entity platforms | 10-15 hours | Medium-High |
| Phase 4: Advanced Tests | WebSocket, edge cases | 6-10 hours | High |
| Phase 5: CI/CD | GitHub Actions, badges | 2-4 hours | Low |
| **TOTAL** | **Full test suite** | **28-45 hours** | **Medium-High** |

**Recommended Approach:** Implement in phases over 1-2 weeks, starting with Phase 1 and 2 to get basic coverage, then incrementally add more tests.

---

## Success Metrics

### Minimum (Silver Tier)
- ✅ Test coverage ≥90%
- ✅ All config flows tested
- ✅ All platforms have basic tests
- ✅ CI/CD pipeline running

### Target (Gold Tier)
- ✅ Test coverage ≥95%
- ✅ Integration tests included
- ✅ Edge cases covered
- ✅ Performance tests added

### Stretch (Platinum Tier)
- ✅ Test coverage ≥98%
- ✅ Load tests included
- ✅ Security tests added
- ✅ Mutation testing

---

## Testing Best Practices

1. **Use Fixtures for Common Setup**
   - Mock API responses
   - Mock WebSocket events
   - Reusable test data

2. **Test Both Success and Failure Paths**
   - Happy path
   - Error handling
   - Edge cases

3. **Use Parametrize for Similar Tests**
   - Test multiple sensors with same pattern
   - Test different error scenarios

4. **Mock External Dependencies**
   - Don't make real API calls
   - Use `aioclient_mock`
   - Mock WebSocket connections

5. **Test Async Code Properly**
   - Use `pytest-asyncio`
   - Await all async calls
   - Test concurrent operations

6. **Keep Tests Fast**
   - Use mocks instead of real delays
   - Parallel test execution
   - Target: <30 seconds for full suite

7. **Write Descriptive Test Names**
   - `test_config_flow_user_success`
   - `test_api_client_timeout_error`
   - `test_sensor_cpu_usage_value`

---

## Next Steps

1. **Review this plan** with the development team
2. **Set up Phase 1** (testing infrastructure)
3. **Implement Phase 2** (core tests) to get initial coverage
4. **Iterate through Phases 3-5** to reach ≥90% coverage
5. **Monitor coverage** and add tests for uncovered code
6. **Maintain tests** as new features are added

See `EXAMPLE_TESTS.md` for detailed example test files.


