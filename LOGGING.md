# Logging Documentation

## Overview

SaturdayMorningPlex implements comprehensive logging compatible with both Docker and UnRAID deployments. Logs are output to both stdout (for Docker logs command) and persistent files (for UnRAID log viewer).

## Configuration

### Environment Variables

| Variable | Default | Options | Description |
|----------|---------|---------|-------------|
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | Controls logging verbosity |
| `LOG_DIR` | `/config/logs` | Any valid path | Directory for persistent log files |

### Docker Compose Example

```yaml
environment:
  - LOG_LEVEL=INFO
  - LOG_DIR=/config/logs
volumes:
  - ./config:/config  # Required for persistent logs
```

### UnRAID Configuration

Set via UnRAID template in Community Applications:
- **Log Level**: Advanced settings → `LOG_LEVEL`
- **Log Directory**: Advanced settings → `LOG_DIR`
- **Config Storage**: Path mapping → `/config` → `/mnt/user/appdata/saturdaymorningplex/config`

## Log Levels

### ERROR
**When to use**: Production deployments where you only want critical failures

**What gets logged**:
- Authentication failures
- Plex API errors
- Playlist creation failures
- Exception tracebacks

**Example output**:
```
2024-01-15 10:30:45 - plex_connection - ERROR - [plex_connection.py:80] - Authentication failed: Invalid token
```

### WARNING (includes ERROR)
**When to use**: Production with interest in non-critical issues

**What gets logged**:
- All ERROR logs
- Fallback behaviors (e.g., using /tmp for logs when /config unavailable)
- Missing optional configuration
- Playlist deletion operations

**Example output**:
```
2024-01-15 10:30:45 - app - WARNING - [app.py:52] - Could not create log directory, using /tmp: Permission denied
```

### INFO (default, includes WARNING and ERROR)
**When to use**: Recommended for all deployments

**What gets logged**:
- All WARNING and ERROR logs
- Plex connection status
- Playlist generation progress
- Summary statistics (X playlists created, Y shows processed)
- Web interface access

**Example output**:
```
2024-01-15 10:30:45 - app - INFO - [app.py:156] - Playlist generation requested
2024-01-15 10:30:46 - playlist_generator - INFO - [playlist_generator.py:26] - Fetching shows with content ratings: ['G', 'PG']
2024-01-15 10:30:48 - playlist_generator - INFO - [playlist_generator.py:50] - Found 12 shows matching criteria
2024-01-15 10:32:15 - app - INFO - [app.py:308] - Playlist generation complete: 52 playlists created
```

### DEBUG (includes all above)
**When to use**: Troubleshooting issues, development

**What gets logged**:
- All INFO, WARNING, and ERROR logs
- Detailed Plex API calls
- Show filtering details (each show included/excluded with reason)
- Episode distribution algorithm steps
- Connection initialization details
- Internal state during operations

**Example output**:
```
2024-01-15 10:30:45 - app - DEBUG - [app.py:100] - Environment: PLEX_URL=set, PLEX_TOKEN=set, TV_LIBRARY=TV Shows, CONTENT_RATINGS=['G', 'PG']
2024-01-15 10:30:46 - playlist_generator - DEBUG - [playlist_generator.py:46] - Included: SpongeBob SquarePants (TV-Y7)
2024-01-15 10:30:46 - playlist_generator - DEBUG - [playlist_generator.py:48] - Excluded: The Walking Dead (TV-MA)
2024-01-15 10:31:00 - playlist_generator - DEBUG - [playlist_generator.py:137] - Year 1, Week 1: 12 episodes
```

## Log Output Locations

### Docker

**View real-time logs**:
```bash
docker logs -f saturdaymorningplex
docker-compose logs -f
```

**View last N lines**:
```bash
docker logs --tail 100 saturdaymorningplex
```

**Search logs**:
```bash
docker logs saturdaymorningplex | grep ERROR
docker logs saturdaymorningplex | grep "playlist generation"
```

### UnRAID

**Web UI**:
1. Docker tab
2. Click container name → "Logs" button
3. Live updating view

**Persistent file**:
- Location: `/mnt/user/appdata/saturdaymorningplex/config/logs/saturdaymorningplex.log`
- Access via terminal: `tail -f /mnt/user/appdata/saturdaymorningplex/config/logs/saturdaymorningplex.log`
- Access via network share: `\\UNRAID-SERVER\appdata\saturdaymorningplex\config\logs\saturdaymorningplex.log`

## Log Rotation

- **Max file size**: 10MB per log file
- **Backup count**: 5 files
- **Total storage**: ~50MB maximum
- **Automatic**: No manual intervention required

**File naming**:
```
saturdaymorningplex.log         # Current log
saturdaymorningplex.log.1       # Previous rotation
saturdaymorningplex.log.2       # 2nd previous
saturdaymorningplex.log.3       # 3rd previous
saturdaymorningplex.log.4       # 4th previous
saturdaymorningplex.log.5       # Oldest (gets deleted on next rotation)
```

## Log Format

**Standard format**:
```
YYYY-MM-DD HH:MM:SS - module_name - LEVEL - [filename.py:line] - message
```

**Example**:
```
2024-01-15 10:30:45 - playlist_generator - INFO - [playlist_generator.py:198] - Created: Saturday Morning - Year 1 Week 01 (12 episodes)
```

**Components**:
- **Timestamp**: ISO 8601 format (YYYY-MM-DD HH:MM:SS)
- **Module**: Python module name (app, plex_connection, playlist_generator)
- **Level**: DEBUG, INFO, WARNING, ERROR
- **Location**: Source file and line number in brackets
- **Message**: Human-readable description

## Common Log Patterns

### Successful Playlist Generation

```
2024-01-15 10:30:45 - app - INFO - [app.py:70] - ============================================================
2024-01-15 10:30:45 - app - INFO - [app.py:71] - SaturdayMorningPlex Starting
2024-01-15 10:30:45 - app - INFO - [app.py:72] - Log Level: INFO
2024-01-15 10:30:45 - app - INFO - [app.py:75] - ============================================================
2024-01-15 10:30:45 - app - INFO - [app.py:156] - Playlist generation requested
2024-01-15 10:30:45 - app - INFO - [app.py:167] - Generation parameters: library=TV Shows, ratings=['G', 'PG'], prefix='Saturday Morning', weeks=52
2024-01-15 10:30:46 - playlist_generator - INFO - [playlist_generator.py:26] - Fetching shows with content ratings: ['G', 'PG']
2024-01-15 10:30:48 - playlist_generator - INFO - [playlist_generator.py:50] - Found 12 shows matching criteria
2024-01-15 10:30:48 - playlist_generator - INFO - [playlist_generator.py:79] - Total episodes collected: 624
2024-01-15 10:30:48 - playlist_generator - INFO - [playlist_generator.py:112] - Distributing episodes across weeks...
2024-01-15 10:30:49 - playlist_generator - INFO - [playlist_generator.py:147] - Created 52 years of playlists
2024-01-15 10:32:15 - playlist_generator - INFO - [playlist_generator.py:198] - Successfully created 52 playlists
2024-01-15 10:32:15 - playlist_generator - INFO - [playlist_generator.py:265] - ============================================================
2024-01-15 10:32:15 - playlist_generator - INFO - [playlist_generator.py:266] - Playlist generation complete!
2024-01-15 10:32:15 - playlist_generator - INFO - [playlist_generator.py:267] - Shows: 12
2024-01-15 10:32:15 - playlist_generator - INFO - [playlist_generator.py:268] - Total Episodes: 624
2024-01-15 10:32:15 - playlist_generator - INFO - [playlist_generator.py:269] - Years: 1
2024-01-15 10:32:15 - playlist_generator - INFO - [playlist_generator.py:270] - Playlists Created: 52
2024-01-15 10:32:15 - playlist_generator - INFO - [playlist_generator.py:271] - ============================================================
```

### Connection Failure

```
2024-01-15 10:30:45 - plex_connection - INFO - [plex_connection.py:48] - Connecting to Plex server at http://plex:32400
2024-01-15 10:30:50 - plex_connection - ERROR - [plex_connection.py:79] - Failed to connect to Plex server: [Errno 111] Connection refused
Traceback (most recent call last):
  File "/app/plex_connection.py", line 48, in connect
    self.plex = PlexServer(self.baseurl, self.token)
  ...
2024-01-15 10:30:50 - app - ERROR - [app.py:173] - Plex connection test failed: [Errno 111] Connection refused
```

### No Shows Found

```
2024-01-15 10:30:45 - playlist_generator - INFO - [playlist_generator.py:26] - Fetching shows with content ratings: ['TV-MA']
2024-01-15 10:30:48 - playlist_generator - INFO - [playlist_generator.py:50] - Found 0 shows matching criteria
2024-01-15 10:30:48 - playlist_generator - WARNING - [playlist_generator.py:230] - No shows found matching criteria!
```

## Troubleshooting

### Enable Debug Logging Temporarily

**Docker**:
```bash
docker stop saturdaymorningplex
docker run -e LOG_LEVEL=DEBUG ... saturdaymorningplex
```

**Docker Compose**:
```yaml
# Edit docker-compose.yml
environment:
  - LOG_LEVEL=DEBUG

# Restart
docker-compose restart
```

**UnRAID**:
1. Docker tab → Container → Edit
2. Change `LOG_LEVEL` to `DEBUG`
3. Apply

### Common Issues

**Logs not appearing in file**:
- Check `/config` volume is mounted correctly
- Verify permissions: Container runs as user `plex` (uid 1000)
- Check `LOG_DIR` environment variable

**Too many logs/disk space**:
- Log rotation happens automatically at 10MB
- Reduce to ERROR level: `LOG_LEVEL=ERROR`
- Check for infinite loops or repeated errors

**Can't find specific error**:
```bash
# Search by level
docker logs saturdaymorningplex 2>&1 | grep "ERROR"

# Search by module
docker logs saturdaymorningplex 2>&1 | grep "plex_connection"

# Search by message content
docker logs saturdaymorningplex 2>&1 | grep "Failed to"
```

## Development Tips

### Adding New Logging

```python
import logging

logger = logging.getLogger(__name__)

# Start of operation
logger.info(f"Starting operation with param1={param1}")

# Detailed debugging
logger.debug(f"Internal state: {variable}")

# Warnings
logger.warning(f"Using fallback behavior: {reason}")

# Errors (always include exc_info=True for tracebacks)
try:
    risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise
```

### Testing Logging

```python
# Test different levels
import logging
logging.basicConfig(level=logging.DEBUG)

# Verify output
logger.debug("This is DEBUG")
logger.info("This is INFO")
logger.warning("This is WARNING")
logger.error("This is ERROR")
```

## Best Practices

1. **Use appropriate levels**:
   - DEBUG: Internal state, detailed tracing
   - INFO: User-facing operations, summaries
   - WARNING: Recoverable issues, fallbacks
   - ERROR: Failures requiring attention

2. **Include context**:
   ```python
   # Good
   logger.info(f"Processing {show_count} shows with ratings {ratings}")
   
   # Bad
   logger.info("Processing shows")
   ```

3. **Always log exceptions with traceback**:
   ```python
   # Good
   except Exception as e:
       logger.error(f"Failed: {e}", exc_info=True)
   
   # Bad
   except Exception as e:
       logger.error(f"Failed: {e}")
   ```

4. **Use structured messages**:
   ```python
   # Good
   logger.info(f"Operation complete: {count} items processed in {duration}s")
   
   # Bad
   logger.info(f"Done! We processed some stuff and it took a while")
   ```

5. **Log entry and exit of major operations**:
   ```python
   logger.info("Starting playlist generation")
   # ... operation ...
   logger.info(f"Playlist generation complete: {result}")
   ```

## Performance Considerations

- **DEBUG level**: Can impact performance with large libraries (10-20% slowdown)
- **INFO level**: Minimal performance impact (<5%)
- **File logging**: Buffered writes, negligible impact
- **Log rotation**: Happens in background, no blocking

## Support

For logging-related issues:
1. Enable DEBUG logging
2. Reproduce the issue
3. Capture full logs: `docker logs saturdaymorningplex > debug.log 2>&1`
4. Open issue at: https://github.com/jozefaz/SaturdayMorningPlex/issues
