# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Docker container support for easier deployment
- WebSocket support for real-time vehicle status updates
- JWT token-based authentication (in addition to API keys)
- Multiple vehicle support
- Home Assistant integration add-on
- Prometheus metrics endpoint

## [0.1.0] - 2026-02-03

### Added
- Initial release of HondaLink Controller
- FastAPI-based REST API for vehicle control
- Core vehicle commands: lock, unlock, remote start, stop
- Vehicle status monitoring (odometer, fuel, locks, oil life)
- Remote start status monitoring with timer and cabin temperature
- Android device automation via uiautomator2
- Comprehensive security features:
  - API key authentication
  - IP whitelist with CIDR notation support
  - Two-tier rate limiting (API and command levels)
  - Audit logging in JSONL format
  - HTTPS/TLS support
- Mock driver for testing without physical Android device
- Automatic retry logic for flaky UI automation (3 retries, 2s delay)
- Debug endpoint for UI hierarchy inspection
- Interactive API documentation (Swagger UI, ReDoc)
- Comprehensive test suite with >80% coverage
- Environment-based configuration via Pydantic settings
- Support for wireless and USB ADB connections

### Security
- All endpoints (except health check) require authentication
- Rate limiting prevents abuse (10 commands/min, 30 API calls/min)
- IP whitelist restricts access to trusted networks
- Complete audit trail for all vehicle operations
- Secure API key generation and validation

### Documentation
- Comprehensive README with quick start guide
- Security hardening guide (SECURITY.md)
- Contributing guidelines (CONTRIBUTING.md)
- Code of Conduct (CODE_OF_CONDUCT.md)
- Architecture documentation and design patterns
- Troubleshooting guide
- API usage examples (curl, Python, JavaScript, Home Assistant)

### Technical Details
- Python 3.11+ required
- FastAPI 0.128+ with async/await support
- uiautomator2 3.5+ for Android automation
- uv package manager for fast dependency management
- Ruff for linting and code formatting
- pytest with coverage reporting

## [0.0.1] - 2026-01-15

### Added
- Initial prototype with basic vehicle control
- Proof of concept for uiautomator2 integration
- Basic FastAPI endpoints without security

---

## Version History

- **0.1.0** (2026-02-03) - First public release with security features
- **0.0.1** (2026-01-15) - Initial prototype

## Links

- [GitHub Repository](https://github.com/tahmidul612/hondalink-app-controller)
- [Report a Bug](https://github.com/tahmidul612/hondalink-app-controller/issues/new?labels=bug)
- [Request a Feature](https://github.com/tahmidul612/hondalink-app-controller/issues/new?labels=enhancement)

---

**Note**: This changelog is manually maintained. For a complete list of changes, see the [commit history](https://github.com/tahmidul612/hondalink-app-controller/commits/main).
