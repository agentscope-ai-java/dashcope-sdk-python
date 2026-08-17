# Changelog

## v1.26.2 (2025-01-13)

### Bug Fixes
- SSE idle_timeout uses queue+thread to actually unblock iter_sse()
- Align SDK params with server API and add SSE wall-clock timeout
- Resolve parameter shadowing in base_api.py update/put methods
- Resolve dict access errors and URL path issues in 5 CLI commands due to SDK dataclass return types
- Resolve UTF-8 encoding issues in HTTP request bodies
- Address code review findings in files, transport, and models
- Remove dead code, fix __del__ safety, make agents.update version explicit
- Resolve resource leak and exception handling issues in async iterator
- Restore assistants imports in __init__.py for Python 3.8 compatibility

### Features
- Add AgentStudio sub-SDK for managed agents
- Expand CLI commands and harden compatibility
- Add 12 generation parameters and fix Models.get

### Refactoring
- Remove custom tools, add vaults/credentials, region param, stop_reason/session_status properties
- Remove assistants-related CLI commands

### Chores
- Remove .acli and .idea from repository
- Update .gitignore to exclude .acli and .idea
