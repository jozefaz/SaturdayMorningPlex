# SaturdayMorningPlex - Project Overview

## Project Purpose

SaturdayMorningPlex is an automated playlist generator for Plex Media Server that creates Saturday morning cartoon-style weekly viewing schedules. It replicates the nostalgic experience of Saturday morning cartoons by generating 52 weekly playlists per year, distributing TV show episodes evenly across weeks.

## Core Concept

### User Problem
Parents want to recreate the Saturday morning cartoon experience for their kids, with:
- Age-appropriate content filtering (G, PG, TV-Y, etc.)
- Predictable weekly viewing schedules
- Variety - different shows each week
- Automatic progression through seasons

### Solution
Automatically generate playlists that:
1. Filter TV shows by content rating (e.g., only "G" rated shows, or "G,PG" combined)
2. Create 52 weekly playlists per year
3. Distribute episodes round-robin style (one episode per show per week)
4. Continue to next seasons automatically when shows run out of episodes
5. Generate multiple years until all matching episodes are included

## How It Works

### Algorithm Example

**Input:**
- Content Rating Filter: "G"
- TV Shows Library contains:
  - Show A: 26 episodes (2 seasons × 13 episodes)
  - Show B: 39 episodes (3 seasons × 13 episodes)
  - Show C: 52 episodes (4 seasons × 13 episodes)

**Output:**
- **Year 1, Week 1**: Show A S01E01, Show B S01E01, Show C S01E01
- **Year 1, Week 2**: Show A S01E02, Show B S01E02, Show C S01E02
- ...
- **Year 1, Week 52**: Show A S04E13, Show B S03E13, Show C S04E13
- **Year 2, Week 1**: Continue with remaining episodes
- **Year 3, Week 1**: Final episodes from Show C

Total: 3 years × 52 weeks = 156 playlists covering all 117 episodes

### Round-Robin Distribution Logic

```
For each week (1-52):
  For each show in library:
    Add next unwatched episode from that show
  Move to next week
  
When week > 52:
  Start new year (Year 2, Year 3, etc.)
  
Continue until all episodes from all shows are distributed
```

## Architecture

### File Structure

```
SaturdayMorningPlex/
├── app.py                    # Flask web application & API endpoints
├── plex_connection.py        # Plex server authentication & connection
├── playlist_generator.py     # Core playlist generation algorithm
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container image definition
├── docker-compose.yml       # Docker Compose configuration
├── unraid-template.xml      # UnRAID Community Apps template
├── templates/
│   └── index.html          # Web UI for configuration & control
├── README.md               # User documentation
├── UNRAID_DEPLOYMENT.md    # UnRAID-specific deployment guide
└── PROJECT.md              # This file - project overview
```

### Key Components

#### 1. Plex Connection (`plex_connection.py`)
- **Purpose**: Handle authentication and connection to Plex servers
- **Methods**:
  - Direct connection via URL + token
  - MyPlex account login (username/password + server name)
  - Test connection functionality
  - Get TV library sections

#### 2. Playlist Generator (`playlist_generator.py`)
- **Purpose**: Core algorithm for generating playlists
- **Key Functions**:
  - `get_filtered_shows()`: Filter shows by content rating
  - `get_all_episodes()`: Collect episodes from shows
  - `distribute_episodes_to_weeks()`: Round-robin distribution algorithm
  - `create_plex_playlists()`: Create actual Plex playlist objects
  - `generate_all_playlists()`: Complete workflow orchestration

#### 3. Web Application (`app.py`)
- **Purpose**: Flask-based web server with REST API
- **Endpoints**:
  - `GET /` - Web interface
  - `GET /health` - Health check
  - `POST /api/plex/test` - Test Plex connection
  - `GET /api/plex/content-ratings` - Get available ratings
  - `POST /api/playlists/generate` - Generate playlists
  - `GET /api/playlists/summary` - View existing playlists
  - `POST /api/playlists/delete` - Delete playlists

#### 4. Web Interface (`templates/index.html`)
- **Purpose**: User-friendly control panel
- **Features**:
  - Configuration forms for content ratings and library name
  - Connection testing
  - Playlist generation with progress feedback
  - View and manage existing playlists
  - Real-time API calls with loading indicators

## Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `PLEX_URL` | Direct URL to Plex server | `http://192.168.1.100:32400` |
| `PLEX_TOKEN` | Plex authentication token | `aBc123XyZ...` |
| `PLEX_USERNAME` | MyPlex email (alt. auth) | `user@example.com` |
| `PLEX_PASSWORD` | MyPlex password (alt. auth) | `password123` |
| `PLEX_SERVER_NAME` | Server name for MyPlex auth | `Home Media Server` |
| `TV_LIBRARY_NAME` | TV library section name | `TV Shows` |
| `CONTENT_RATINGS` | Comma-separated ratings | `G,PG,TV-Y,TV-Y7` |
| `APP_PORT` | Web interface port | `5000` |
| `TZ` | Container timezone | `America/New_York` |

### Content Rating Filter Behavior

**IMPORTANT**: The filter uses exact matching:
- `CONTENT_RATINGS=G` → Only G-rated shows (not PG or G+PG)
- `CONTENT_RATINGS=PG` → Only PG-rated shows
- `CONTENT_RATINGS=G,PG` → Shows rated G OR PG (combined)
- `CONTENT_RATINGS=TV-Y,TV-Y7` → Shows rated TV-Y OR TV-Y7

This allows precise control over content appropriateness.

## Deployment

### Docker Compose (Development/Home Server)
```bash
docker-compose up -d
```

### UnRAID (Production)
- Copy `unraid-template.xml` to UnRAID templates folder
- Configure Plex URL and token in UnRAID Docker UI
- Set content ratings and TV library name
- Deploy container

### Docker Hub (Distribution)
```bash
docker build -t yourdockerhub/saturdaymorningplex:latest .
docker push yourdockerhub/saturdaymorningplex:latest
```

## Dependencies

### Python Packages
- `Flask==3.0.0` - Web framework
- `PlexAPI==4.17.2` - Plex server integration
- `gunicorn==21.2.0` - Production WSGI server
- `requests==2.31.0` - HTTP library

### External Services
- **Plex Media Server** - Required, must have TV Shows library
- **Plex Account** - Required for authentication token

## Usage Workflow

1. **Initial Setup**
   - Deploy container with Plex credentials
   - Access web interface at `http://server-ip:5000`

2. **Configuration**
   - Test Plex connection
   - View available content ratings in library
   - Set desired content ratings filter

3. **Generate Playlists**
   - Click "Generate Playlists"
   - Wait for processing (may take minutes for large libraries)
   - View results showing number of shows, episodes, years created

4. **Use in Plex**
   - Open Plex app
   - Navigate to Playlists section
   - See "Saturday Morning - Year X Week YY" playlists
   - Play playlists sequentially each week

5. **Management**
   - View existing playlists anytime
   - Delete and regenerate with different settings
   - Add new shows to library and regenerate

## Technical Decisions

### Why Round-Robin Distribution?
- **Fairness**: Every show gets equal representation each week
- **Variety**: Kids see different shows each week, not binge-watching
- **Predictability**: Parents know the schedule repeats annually
- **Nostalgia**: Mimics traditional TV broadcast scheduling

### Why 52 Weeks?
- Standard year length
- Manageable playlist count
- Natural annual cycle
- Configurable if needed in future

### Why Exact Rating Match?
- Maximum parental control
- Prevents accidentally including inappropriate content
- Explicit opt-in for each rating level
- Clear, predictable behavior

### Why Multiple Years?
- Ensures all content is used
- Provides multi-year viewing schedules
- Useful for long-running series
- Can cycle through again after completion

## Future Enhancements

### Planned Features
- [ ] Movie playlist support
- [ ] Custom week counts (26, 39, etc.)
- [ ] Shuffle episodes within weeks
- [ ] Multiple playlist sets per user
- [ ] Scheduled auto-regeneration
- [ ] Episode exclusion rules
- [ ] Minimum episode count per week
- [ ] Genre filtering in addition to ratings
- [ ] Integration with Trakt/IMDB for better metadata

### Technical Improvements
- [ ] Background task queue for long operations
- [ ] Progress tracking during generation
- [ ] Playlist preview before creation
- [ ] Undo/redo playlist operations
- [ ] Configuration file persistence
- [ ] Multi-user support
- [ ] Logging dashboard

## Troubleshooting

### Common Issues

**Connection Failed**
- Verify Plex URL includes `http://` and port `:32400`
- Check token validity
- Ensure Docker container can reach Plex server
- Use local IP (192.168.x.x) not localhost

**No Shows Found**
- Check content rating spelling
- Use "Load Available Ratings" button
- Verify TV library name matches Plex
- Ensure shows have content ratings in Plex metadata

**Playlists Not Appearing**
- Refresh Plex client
- Check Plex server logs
- Verify sufficient permissions
- Try regenerating playlists

## Development

### Local Testing
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Building Docker Image
```bash
docker build -t saturdaymorningplex:latest .
docker run -p 5000:5000 -e PLEX_URL=... -e PLEX_TOKEN=... saturdaymorningplex:latest
```

### Code Style
- Python 3.11+
- PEP 8 compliant
- Type hints where beneficial
- Comprehensive logging
- Error handling at all API boundaries

## Repository

- **GitHub**: https://github.com/jozefaz/SaturdayMorningPlex
- **License**: MIT
- **Author**: jozefaz
- **Created**: December 2025

## Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Documentation**: README.md and this file

---

**Last Updated**: December 8, 2025
**Version**: 2.0.0
