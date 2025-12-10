# SaturdayMorningPlex

Recreate the Saturday morning cartoon experience with automated weekly playlists for your Plex server.

## Features

- Creates 52 weekly playlists per year from your TV library
- Toggle content ratings on/off (G, PG, TV-Y, etc.) via web interface
- Handles multiple Plex libraries simultaneously
- Picks highest quality versions when episodes exist in multiple places
- Episodes play in air date order
- Round-robin distribution - each week gets one episode from every show
- Continues across seasons and years until all episodes are scheduled
- Shows detailed statistics after generation
- Dark mode with saved preference
- Works on Docker and UnRAID

## How It Works

Point it at your Plex server, pick some content ratings, and hit generate. The app creates a year's worth of weekly playlists using a simple algorithm: Week 1 gets the first episode from each show, Week 2 gets the second episode from each show, and so on. When shows have different episode counts, it keeps going until everything's scheduled.

Example: 3 shows with 26, 39, and 52 episodes will create about 52 playlists (one year), with the longest show determining how many weeks you get.

After generation, check the logs for a breakdown: total episodes, runtime hours, rating percentages, and which shows contributed the most episodes.

The generator creates:
- **Year 1**: 52 weeks, each with 3 episodes (one from each show)
- **Year 2**: Continues with remaining episodes
- **Year 3**: Final episodes from Show C

Result: **3 years × 52 weeks = 156 playlists** covering all 117 episodes!

### Statistics Output

After generation, detailed statistics are logged:

```
Shows processed: 33
Total episodes distributed: 1,734
Average episodes per show: 52.5
Total runtime: 616.9 hours (25.7 days)
Years generated: 1
Playlists created: 52
Average episodes per playlist: 33.3

Content Rating Breakdown:
  TV-Y: 65.9% (1,143 episodes)
  TV-G: 34.1% (591 episodes)

Top 10 Shows by Episode Count:
  1. Show A: 156 episodes
  2. Show B: 143 episodes
  ...
```

## Installation

### Docker

```bash
docker run -d \
  --name saturdaymorningplex \
  -p 5000:5000 \
  -e PLEX_URL=http://192.168.1.100:32400 \
  -e PLEX_TOKEN=your_token_here \
  -v /path/to/config:/config \
  ghcr.io/jozefaz/saturdaymorningplex:latest
```

Or use docker-compose.yml:

```yaml
services:
  saturdaymorningplex:
    image: ghcr.io/jozefaz/saturdaymorningplex:latest
    container_name: saturdaymorningplex
    ports:
      - "5000:5000"
    environment:
      - PLEX_URL=http://192.168.1.100:32400
      - PLEX_TOKEN=your_token_here
      - TZ=UTC
    volumes:
      - /path/to/config:/config
    restart: unless-stopped
```

Then: `docker-compose up -d`

Access at `http://your-server-ip:5000`

### UnRAID

In the Docker tab, click "Add Container" → "Template repositories" and add:
```
https://raw.githubusercontent.com/jozefaz/SaturdayMorningPlex/main/unraid-template.xml
```

Select SaturdayMorningPlex from the list, fill in your Plex URL and token, then hit Apply.

For more details: [UNRAID_DEPLOYMENT.md](UNRAID_DEPLOYMENT.md)

## Configuration

The web interface handles library selection and content ratings - you don't need to set those via environment variables. Just provide your Plex connection details:

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `PLEX_URL` | Yes* | - | Your Plex server URL (e.g., `http://192.168.1.100:32400`) |
| `PLEX_TOKEN` | Yes* | - | Authentication token from Plex |
| `PLEX_USERNAME` | Yes** | - | MyPlex email (use instead of token) |
| `PLEX_PASSWORD` | Yes** | - | MyPlex password (use instead of token) |
| `PLEX_SERVER_NAME` | No | - | Required if using username/password |
| `TV_LIBRARY_NAME` | No | `TV Shows` | Default library name |
| `CONTENT_RATINGS` | No | `G,PG` | Default ratings filter |
| `TZ` | No | `UTC` | Container timezone |
| `LOG_LEVEL` | No | `INFO` | DEBUG, INFO, WARNING, or ERROR |

\* Either use `PLEX_URL` + `PLEX_TOKEN` or `PLEX_USERNAME` + `PLEX_PASSWORD` + `PLEX_SERVER_NAME`

The app runs on port 5000 internally - map it however you want with `-p` flag.

### Getting Your Plex Token

Open Plex Web App, play any media, click the three dots (⋯) → "Get Info" → "View XML". Look in the URL bar for `X-Plex-Token=` and copy everything after it.

Or go to Settings → Server → Network → Show Advanced - the token is displayed there.

### Content Rating Filter

The rating filter uses exact matches: `CONTENT_RATINGS=G` only includes G-rated shows, not PG or anything else. For multiple ratings, separate with commas: `G,PG,TV-Y,TV-Y7`

This is intentional for parental control - no fuzzy matching or "G includes everything below PG-13" logic.

## Logging

View container logs:
```bash
docker logs -f saturdaymorningplex
docker logs --tail 100 saturdaymorningplex
```

For UnRAID: Docker tab → container → Logs button, or check `/mnt/user/appdata/saturdaymorningplex/config/logs/`

Set `LOG_LEVEL=DEBUG` for detailed output. Logs auto-rotate at 10MB and keep 5 backups (50MB total).

## Usage

Navigate to `http://your-server-ip:5000` and:

1. Test your Plex connection with the button
2. Load available libraries and select one or more
3. Load available ratings and toggle the ones you want
4. Hit Generate and wait (large libraries take a few minutes)
5. Check your Plex server for the new playlists

The interface shows progress and will display statistics when done. Regenerating updates existing playlists rather than creating duplicates.

## License

MIT

---

Made for Saturday morning cartoon nostalgia.
