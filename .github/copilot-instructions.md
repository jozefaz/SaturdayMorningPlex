# SaturdayMorningPlex - AI Agent Instructions

## Project Overview

**Purpose**: Automated Plex playlist generator that creates Saturday morning cartoon-style weekly schedules. Filters TV shows by content rating (G, PG, etc.) and distributes episodes round-robin across 52 weekly playlists per year.

**Core Algorithm**: Round-robin distribution - Week 1 gets episode 1 from all shows, Week 2 gets episode 2 from all shows, continuing across seasons until all episodes are distributed (may span multiple years).

## Architecture (3-Tier)

```
Web UI (templates/index.html)
    ↓ AJAX calls
Flask API (app.py) - REST endpoints, env config
    ↓ uses
Plex Integration Layer
    ├── plex_connection.py - Auth & server connection
    └── playlist_generator.py - Core algorithm & Plex API calls
```

**Key Data Flow**: User triggers generation → `app.py` initializes `PlexConnection` → `PlaylistGenerator` filters shows by rating → `distribute_episodes_to_weeks()` creates round-robin schedule → `create_plex_playlists()` calls Plex API to create playlist objects.

## Critical Patterns

### 1. Plex Authentication (Two Methods)
```python
# Method 1: Direct (preferred for containers)
PlexConnection(baseurl="http://192.168.1.100:32400", token="abc123")

# Method 2: MyPlex account (for remote servers)
PlexConnection(username="user@email.com", password="pass", servername="Home Server")
```
**Why**: Direct token method works in Docker without exposing credentials; MyPlex useful for multi-server setups.

### 2. Content Rating Filter - EXACT MATCH ONLY
```python
# CONTENT_RATINGS="G" → Only G-rated shows (NOT PG)
# CONTENT_RATINGS="G,PG" → G OR PG shows (explicit opt-in)
if show.contentRating in content_ratings:  # Exact string match
```
**Critical**: This is intentional for parental control. Never implement fuzzy matching or "G includes everything".

### 3. Global Connection Pattern
```python
# app.py maintains global plex_conn
plex_conn = None  # Initialized on first API call, reused thereafter

def generate_playlists():
    global plex_conn
    if not plex_conn:
        plex_conn = PlexConnection(...)
        plex_conn.connect()
```
**Why**: Avoids reconnecting on every request; connection is expensive (~2-3 seconds).

### 4. Round-Robin Distribution Algorithm
```python
# playlist_generator.py: distribute_episodes_to_weeks()
show_indices = {show: 0 for show in show_episodes.keys()}
active_shows = set(show_episodes.keys())

while active_shows:
    for show_title in sorted(active_shows):  # sorted() ensures consistent ordering
        episode = episodes[show_indices[show_title]]
        week_episodes.append(episode)
        show_indices[show_title] += 1
```
**Critical**: `sorted()` is essential - ensures deterministic playlist ordering across regenerations.

### 5. Environment Variable Configuration
All config via env vars (12-factor app):
- `PLEX_URL` + `PLEX_TOKEN` (primary auth)
- `TV_LIBRARY_NAME` (default: "TV Shows")
- `CONTENT_RATINGS` (CSV string, split in app.py line 32)

**Never hardcode** Plex credentials or library names.

### 6. Logging System - Docker & UnRAID Compatible
```python
# app.py: setup_logging() - Dual output configuration
def setup_logging():
    # Console handler (stdout) - Docker logs
    console_handler = logging.StreamHandler(sys.stdout)
    
    # File handler - UnRAID persistent logs  
    log_file = os.path.join(LOG_DIR, 'saturdaymorningplex.log')
    file_handler = RotatingFileHandler(log_file, maxBytes=10MB, backupCount=5)
```

**Log Levels** (configured via `LOG_LEVEL` env var):
- `DEBUG`: Detailed tracing (connection details, API calls, algorithm steps)
- `INFO`: General operations (playlist generation, Plex connections, summaries)
- `WARNING`: Non-critical issues (fallback behaviors, missing optional config)
- `ERROR`: Failures requiring attention (auth errors, API failures, exceptions)

**Logging Pattern**:
```python
logger.info(f"Starting operation: {param1}, {param2}")  # Start of operation
logger.debug(f"Detailed context: {internal_state}")      # Debug details
logger.error(f"Failed: {e}", exc_info=True)              # Always include traceback
```

**Docker Logs**: Use `docker logs <container>` or `docker-compose logs -f` to view real-time logs.

**UnRAID Logs**: View in UnRAID web UI (Docker tab → container → Logs) or persistent file at `/mnt/user/appdata/saturdaymorningplex/config/logs/saturdaymorningplex.log`.

**Log Rotation**: Automatic rotation at 10MB with 5 backup files (total 50MB max).

**Critical**: All log output goes to stdout (Docker-compatible). File logging is supplementary for UnRAID persistence.

## Key Files & Responsibilities

- **app.py**: Flask routes, env loading, global connection state
- **plex_connection.py**: Auth only - no business logic
- **playlist_generator.py**: Pure algorithm - no Flask/HTTP concerns
- **templates/index.html**: Standalone SPA - all API calls via fetch()

**Separation**: Business logic (playlist_generator) has ZERO Flask imports. Can be tested independently.

## Development Workflows

### Local Testing Without Plex
```bash
# Test connection module only
python3 -c "from plex_connection import PlexConnection; print('Import OK')"

# Run Flask without starting (syntax check)
python3 -c "import app; print('App loads OK')"
```

### Docker Build & Test
```bash
docker build -t saturdaymorningplex:test .
docker run -e PLEX_URL=http://plex:32400 -e PLEX_TOKEN=test saturdaymorningplex:test
```

### Troubleshooting Import Errors
PlexAPI imports will show lint errors until installed:
```bash
pip install -r requirements.txt
# or ignore - they're valid at runtime in Docker
```

## API Endpoint Patterns

All endpoints follow this structure:
```python
@app.route('/api/playlists/generate', methods=['POST'])
def generate_playlists():
    try:
        data = request.get_json() or {}
        # Extract params with defaults
        content_ratings = data.get('content_ratings', CONTENT_RATINGS)
        # ... process ...
        return jsonify({'success': True, ...})
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
```

**Always**: Return `{'success': bool, ...}`, log with `exc_info=True`, HTTP 500 for errors.

## Dependencies & Integration

**PlexAPI (v4.17.2)**: 
- `PlexServer.library.section('TV Shows')` - Get library
- `show.episodes()` - Returns episodes in natural order (S01E01, S01E02...)
- `Playlist.create(server, title, items)` - Create playlist

**Critical**: `show.episodes()` returns episodes in Plex's internal order. For different orderings, use `show.episodes(sort='originallyAvailableAt:asc')`.

## Common Pitfalls

1. **Never** use `localhost` for `PLEX_URL` in Docker - use `host.docker.internal` or LAN IP
2. **Content ratings** vary by library (US vs International) - always use "Load Available Ratings" button first
3. **Playlist names** must be unique - generator deletes existing before creating (see `create_plex_playlists()` line 181)
4. **Episode ordering** from PlexAPI may differ from expected - trust Plex's order or implement custom sort

## Testing & Validation

No formal test suite (yet). Manual validation:
1. Test connection via `/api/plex/test`
2. Check available ratings via `/api/plex/content-ratings`  
3. Generate with small library first (3-4 shows)
4. Verify in Plex UI: Playlists section should show "Saturday Morning - Year X Week YY"

## UnRAID Deployment Notes

- Template: `unraid-template.xml` - XML format required by Community Apps
- Environment vars exposed as UnRAID form fields (line 16-20 in template)
- WebUI auto-detected via `<WebUI>` tag at line 10

## Future Enhancements Roadmap

See `PROJECT.md` section "Future Enhancements" for planned features. When implementing:
- Movie support: Create `MoviePlaylistGenerator` subclass of `PlaylistGenerator`
- Custom week counts: Add `weeks_per_year` param (already supported in algorithm)
- Multiple sets: Requires user/profile system - significant architectural change

## Documentation

- **PROJECT.md**: Complete architecture & design decisions (read this for "why")
- **README.md**: User-facing setup & usage
- **UNRAID_DEPLOYMENT.md**: UnRAID-specific deployment guide

When context is lost, read `PROJECT.md` first for full system understanding.
