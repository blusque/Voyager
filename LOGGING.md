# Voyager Logging System

This document describes the comprehensive logging system added to the Voyager project.

## Overview

A structured logging system has been implemented across the Voyager codebase to improve debugging, monitoring, and operational visibility. The system includes:

- **Colored console output** for better readability
- **Rotating file logs** to prevent disk space issues
- **Configurable log levels** via environment variables
- **Component-specific loggers** for fine-grained control
- **Automatic silencing** of noisy third-party libraries

## Quick Start

### Basic Usage

```python
from voyager import Voyager
from voyager.utils import configure_root_logger, silence_noisy_loggers

# Set up logging (already done in run.py)
configure_root_logger(log_dir="logs")
silence_noisy_loggers()

# Now all Voyager operations will be logged
voyager = Voyager(...)
```

### Setting Log Level

**Via environment variable (recommended):**
```bash
# Windows PowerShell
$env:VOYAGER_LOG_LEVEL="DEBUG"
python run.py

# Linux/Mac
export VOYAGER_LOG_LEVEL=DEBUG
python run.py
```

**Via code:**
```python
import logging
from voyager.utils import configure_root_logger

configure_root_logger(log_dir="logs", level=logging.DEBUG)
```

## Log Levels

| Level | Usage | Example |
|-------|-------|---------|
| `DEBUG` | Detailed diagnostic information | Skill retrieval queries, code execution details |
| `INFO` | General informational messages | Task initialization, agent setup, progress updates |
| `WARNING` | Warning messages for potential issues | Configuration warnings, retries |
| `ERROR` | Error messages for failures | Task failures, API errors, exceptions |
| `CRITICAL` | Critical errors requiring immediate attention | System crashes, unrecoverable errors |

## Log File Locations

Logs are stored in the `logs/` directory with the following structure:

```
logs/
├── voyager_20251101.log              # Main application log
├── voyager_voyager_20251101.log      # Voyager main class
├── voyager_agents_skill_20251101.log # Skill manager
├── voyager_agents_action_20251101.log# Action agent
├── voyager_env_bridge_20251101.log   # Environment bridge
└── run_20251101.log                  # Run script logs
```

### Log Rotation

- **Max file size:** 10 MB per log file
- **Backup count:** 5 backup files kept
- **Naming:** Older files get `.1`, `.2`, etc. suffix

## Logging in Your Code

### Getting a Logger

```python
from voyager.utils import get_logger

logger = get_logger(__name__)
```

### Logging Examples

```python
# Informational messages
logger.info("Starting task execution")
logger.info(f"Retrieved {count} skills for context")

# Debug messages (only shown when DEBUG level is set)
logger.debug(f"Processing message: {msg[:100]}...")

# Warnings
logger.warning("API rate limit approaching")

# Errors with stack traces
try:
    risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
```

## Key Features

### 1. Colored Console Output

Console logs are color-coded for easy identification:
- 🔵 **DEBUG** - Cyan
- 🟢 **INFO** - Green  
- 🟡 **WARNING** - Yellow
- 🔴 **ERROR** - Red
- ⚫ **CRITICAL** - Red background

### 2. Structured Messages

All log entries include:
- Timestamp (YYYY-MM-DD HH:MM:SS)
- Logger name (module path)
- Log level
- Function name and line number (file logs only)
- Message

**Console format:**
```
2025-11-01 14:23:45 - voyager.voyager - INFO - Initializing Voyager
```

**File format:**
```
2025-11-01 14:23:45 - voyager.voyager - INFO - __init__:115 - Initializing Voyager
```

### 3. Silenced Third-Party Loggers

The following libraries are automatically set to WARNING level to reduce noise:
- `urllib3`, `requests`, `httpx`, `httpcore`
- `openai`, `langchain`, `chromadb`, `posthog`

## What Gets Logged

### Voyager Main Class (`voyager/voyager.py`)
- ✅ Initialization with all configuration details
- ✅ Environment setup and agent initialization
- ✅ Task reset and execution steps
- ✅ Success/failure outcomes
- ✅ Learning loop iterations and progress
- ✅ Exception handling with full stack traces

### Skill Manager (`voyager/agents/skill.py`)
- ✅ Model selection (GPT/QwQ)
- ✅ Skill retrieval queries and results
- ✅ Skill library operations

### Environment Bridge (`voyager/env/bridge.py`)
- ✅ Minecraft instance startup
- ✅ Mineflayer process management
- ✅ Server connection status

### Run Script (`run.py`)
- ✅ Application startup
- ✅ Configuration loading
- ✅ Initialization success/failure

## Troubleshooting

### No logs appearing

**Check log level:**
```bash
$env:VOYAGER_LOG_LEVEL="DEBUG"
```

**Verify logs directory exists:**
```python
import os
os.makedirs("logs", exist_ok=True)
```

### Too much output

**Reduce verbosity:**
```bash
$env:VOYAGER_LOG_LEVEL="WARNING"
```

**Silence specific loggers:**
```python
import logging
logging.getLogger("langchain").setLevel(logging.ERROR)
```

### Log files too large

The system automatically rotates log files. If you want to adjust:

```python
from voyager.utils import setup_logger

logger = setup_logger(
    "my_module",
    max_bytes=5 * 1024 * 1024,  # 5 MB
    backup_count=3               # Keep 3 backups
)
```

## Best Practices

1. **Use appropriate log levels:**
   - `DEBUG` for diagnostic details
   - `INFO` for significant events
   - `WARNING` for recoverable issues
   - `ERROR` for failures
   - `CRITICAL` for system-threatening errors

2. **Include context in messages:**
   ```python
   # Good
   logger.info(f"Task '{task}' completed in {duration:.2f}s")
   
   # Not as helpful
   logger.info("Task completed")
   ```

3. **Use exc_info=True for exceptions:**
   ```python
   try:
       dangerous_operation()
   except Exception as e:
       logger.error(f"Failed: {e}", exc_info=True)
   ```

4. **Avoid logging sensitive data:**
   ```python
   # Bad - exposes API key
   logger.debug(f"API key: {api_key}")
   
   # Good - masks sensitive data
   logger.debug(f"API key: {api_key[:8]}...")
   ```

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VOYAGER_LOG_LEVEL` | `INFO` | Global log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `LOG_LEVEL` | `INFO` | Alternative to VOYAGER_LOG_LEVEL (used in run.py) |

### Programmatic Configuration

```python
from voyager.utils import configure_root_logger, get_logger, silence_noisy_loggers
import logging

# Configure root logger
configure_root_logger(
    log_dir="custom_logs",
    level=logging.DEBUG
)

# Silence noisy libraries
silence_noisy_loggers()

# Get a module-specific logger
logger = get_logger(__name__, log_dir="custom_logs")
```

## Migration Notes

The logging system coexists with existing `print()` statements, which are gradually being replaced. Color-coded console output using ANSI escape codes (`\033[32m...`) is preserved for backward compatibility.

## Future Enhancements

Potential improvements for the logging system:

- [ ] JSON-formatted logs for machine parsing
- [ ] Remote log aggregation (e.g., to ELK stack)
- [ ] Performance metrics logging
- [ ] Log filtering by component
- [ ] Integration with monitoring tools (Prometheus, Grafana)

## Examples

### Example 1: Debug a Failed Task

```bash
# Enable debug logging
$env:VOYAGER_LOG_LEVEL="DEBUG"
python run.py

# Check the main log
cat logs/voyager_voyager_*.log | grep "FAILED"

# Check specific agent logs
cat logs/voyager_agents_action_*.log
```

### Example 2: Monitor Learning Progress

```python
from voyager.utils import get_logger

logger = get_logger(__name__)

# This will appear in both console and file logs
logger.info("Starting learning loop")
voyager.learn()
```

### Example 3: Custom Logger for Plugin

```python
from voyager.utils import setup_logger

# Create a custom logger for your plugin
plugin_logger = setup_logger(
    name="voyager.plugins.my_plugin",
    log_dir="logs",
    log_level=logging.INFO
)

plugin_logger.info("Plugin initialized")
```

## Support

For issues related to logging:

1. Check log files in `logs/` directory
2. Verify `VOYAGER_LOG_LEVEL` environment variable
3. Ensure `logs/` directory has write permissions
4. Review this documentation

For additional help, refer to the main Voyager documentation or open an issue on GitHub.
