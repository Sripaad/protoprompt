# Changelog

All notable changes to TinyContext will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.1] - 2024-12-19

### Added
- Initial MVP release of TinyContext
- FSM-based agent orchestration with TinyWorld (5 states: IDLE, THINKING, ACTING, HANDING_OFF, ERROR)
- TinyPerson agent definition using Protocol Buffers
- TinyFactory for loading agents from YAML/JSON
- TinyContextManager as central orchestrator
- ReAct-style reasoning and action loops
- TensorZero client integration (simulated for MVP)
- CLI interface with commands: run, agents, sessions, replay, init
- Session management with in-memory storage
- Sample agent templates (strategist, planner, analyzer)
- Support for agent handoffs between tasks
- Execution trace tracking and replay functionality
- uv package manager support

### Known Limitations
- TensorZero integration is simulated (not connected to real API)
- Protobuf compilation not automated (manual dataclasses used)
- No vector memory or persistent storage
- Basic agent selection heuristics

### Technical Details
- Python 3.11+ required
- No external dependencies except: click, protobuf, pyyaml, rich
- Fully type-hinted codebase
- Modular architecture for easy extension