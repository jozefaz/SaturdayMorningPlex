# SaturdayMorningPlex

Automatically generate Saturday morning cartoon-style weekly playlists for your Plex server!

## ✨ Features

- 🎬 **Automated Playlist Generation** - Creates 52 weekly playlists per year
- 🎯 **Interactive Content Rating Selector** - Toggle buttons to select/deselect ratings (G, PG, TV-Y, etc.)
- 📚 **Multi-Library Support** - Combine shows from multiple Plex libraries (e.g., "TV Shows, Anime, Kids")
- 🎨 **Smart Quality Selection** - Automatically picks highest quality version when duplicates exist (bitrate → filesize → random)
- 📅 **Air Date Sorting** - Episodes sorted chronologically for authentic viewing order
- 📺 **Smart Distribution** - Each week gets one episode from each show (round-robin)
- 🔄 **Multi-Season Support** - Automatically continues to next seasons
- 📅 **Multi-Year Generation** - Creates playlists until all episodes are included
- ✅ **Content Validation** - Verifies selected ratings exist in your library before generating
- 🔁 **Smart Playlist Replacement** - Detects and replaces incomplete/outdated playlists
- ⏱️ **Duration Display** - Shows total playlist duration in minutes
- 📊 **Aggregate Statistics** - Shows comprehensive stats after generation (episode counts, runtime, rating breakdown, top shows)
- 🌙 **Dark Mode** - Toggle between light and dark themes with persistent preference
- 🐳 **Docker & UnRAID Ready** - Easy deployment with Docker or UnRAID
- 🌐 **Modern Web Interface** - Interactive UI with real-time feedback

## 🎯 How It Works

1. **Connect to Plex** - Authenticate with your Plex Media Server
2. **Select Libraries** - Click "Load Available Libraries" to see all TV libraries, select one or multiple
3. **Choose Content Ratings** - Click "Load Available Ratings" and toggle ratings on/off with interactive buttons
4. **Generate Playlists** - Creates weekly playlists with smart features:
   - **Air Date Sorting**: Episodes sorted chronologically (oldest first)
   - **Round-Robin Distribution**: Week 1 gets episode 1 from all shows, Week 2 gets episode 2, etc.
   - **Quality Selection**: When same episode exists in multiple libraries, automatically picks highest bitrate version
   - **Multi-Season**: Automatically continues to next seasons when shows run out of episodes
   - **Deduplication**: Prevents duplicate episodes across libraries
5. **Multiple Years** - Continues creating years until all episodes are used
6. **Smart Replacement** - Regenerating updates existing playlists intelligently

### Web Interface Features

- **Interactive Content Rating Selector**: Click ratings to toggle them on/off (selected ratings show in blue with ✓)
- **Multi-Library Selector**: Click "Select All TV Libraries" to include all libraries at once
- **Real-Time Validation**: System checks if selected ratings exist before generating
- **Live Status Updates**: Progress messages show what's happening during generation
- **Playlist Summary**: View all existing playlists with episode counts and durations

### Example Output

If you have 3 shows with content rating "G":
- Show A: 26 episodes (2 seasons, 13 each)
- Show B: 39 episodes (3 seasons, 13 each)
- Show C: 52 episodes (4 seasons, 13 each)

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

## 🚀 Quick Start

### Prerequisites

- Plex Media Server with TV Shows library
- Docker or UnRAID server
- Plex authentication token (see [Getting Your Plex Token](#getting-your-plex-token))

### Option 1: Docker Run (Recommended)

```bash
docker run -d \
  --name saturdaymorningplex \
  -p 5000:5000 \
  -e PLEX_URL=http://192.168.1.100:32400 \
  -e PLEX_TOKEN=your_token_here \
  -e TV_LIBRARY_NAME="TV Shows" \
  -e CONTENT_RATINGS="G,PG" \
  -e TZ=UTC \
  -v /path/to/config:/config \
  ghcr.io/jozefaz/saturdaymorningplex:latest
```

### Option 2: Docker Compose

1. **Create docker-compose.yml**
   ```yaml
   version: '3.8'
   services:
     saturdaymorningplex:
       image: ghcr.io/jozefaz/saturdaymorningplex:latest
       container_name: saturdaymorningplex
       ports:
         - "5000:5000"
       environment:
         - PLEX_URL=http://192.168.1.100:32400
         - PLEX_TOKEN=your_token_here
         - TV_LIBRARY_NAME=TV Shows
         - CONTENT_RATINGS=G,PG
         - TZ=UTC
         - LOG_LEVEL=INFO
       volumes:
         - /path/to/config:/config
       restart: unless-stopped
   ```

2. **Start the container**
   ```bash
   docker-compose up -d
   ```

4. **Access the web interface**
   - Open: `http://your-server-ip:5000`

### Option 3: UnRAID

**Quick Install:**
1. Go to Docker tab → Add Container
2. Click "Template repositories" and add:
   ```
   https://raw.githubusercontent.com/jozefaz/SaturdayMorningPlex/main/unraid-template.xml
   ```
3. Select "SaturdayMorningPlex" from the template list
4. Fill in your Plex URL and Token
5. Click Apply

See [UNRAID_DEPLOYMENT.md](UNRAID_DEPLOYMENT.md) for detailed instructions.

## 🔧 Configuration

**Note**: Most users should use the web interface to configure libraries and content ratings dynamically. Environment variables are only needed for initial Plex connection.

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PLEX_URL` | Yes* | - | Direct URL to Plex server (e.g., `http://192.168.1.100:32400`) |
| `PLEX_TOKEN` | Yes* | - | Plex authentication token |
| `PLEX_USERNAME` | Yes** | - | MyPlex email (alternative to token) |
| `PLEX_PASSWORD` | Yes** | - | MyPlex password (alternative to token) |
| `PLEX_SERVER_NAME` | No | - | Server name (required if using username/password) |
| `TV_LIBRARY_NAME` | No | `TV Shows` | Name of your TV Shows library in Plex |
| `CONTENT_RATINGS` | No | `G,PG` | Comma-separated content ratings to include |
| `TZ` | No | `UTC` | Timezone for container |
| `LOG_LEVEL` | No | `INFO` | Logging detail: DEBUG, INFO, WARNING, ERROR |

\* Use either `PLEX_URL` + `PLEX_TOKEN` OR `PLEX_USERNAME` + `PLEX_PASSWORD` + `PLEX_SERVER_NAME`

**Note**: `APP_PORT` and `APP_HOST` are internal settings (5000 and 0.0.0.0) and should not be changed.

### Getting Your Plex Token

**Method 1: From Plex Web App**
1. Open Plex Web App
2. Play any media item
3. Click the three dots (...) → "Get Info"
4. Click "View XML"
5. Look in the URL for `X-Plex-Token=` - copy the value after it

**Method 2: From Server Settings**
1. Go to Settings → Server → Network
2. Show Advanced
3. The token is displayed there

**Method 3: Using curl**
```bash
curl -u 'YOUR_EMAIL:YOUR_PASSWORD' 'https://plex.tv/users/sign_in.xml' \\
  -X POST -H 'X-Plex-Client-Identifier: MyApp'
```

### Content Rating Examples

- **G Only**: `CONTENT_RATINGS=G`
- **PG Only**: `CONTENT_RATINGS=PG`
- **G and PG**: `CONTENT_RATINGS=G,PG`
- **TV-Y and TV-Y7**: `CONTENT_RATINGS=TV-Y,TV-Y7`
- **Multiple**: `CONTENT_RATINGS=G,PG,TV-Y,TV-Y7,TV-G`

**Note**: The filter is exact match only. If you set `PG`, it will ONLY include PG-rated shows, not G or PG-13.

## 📊 Logging & Monitoring

### Docker Logs

View real-time logs from your container:
```bash
# Follow logs (live view)
docker logs -f saturdaymorningplex

# View last 100 lines
docker logs --tail 100 saturdaymorningplex

# Using docker-compose
docker-compose logs -f
```

### UnRAID Logs

1. **Web UI**: Docker tab → SaturdayMorningPlex → Logs button
2. **Persistent Logs**: Access log file at `/mnt/user/appdata/saturdaymorningplex/config/logs/saturdaymorningplex.log`

### Log Levels

Configure logging detail via `LOG_LEVEL` environment variable:

- `ERROR` - Only errors (minimal logging)
- `WARNING` - Warnings and errors
- `INFO` - General operations (default, recommended)
- `DEBUG` - Detailed tracing (for troubleshooting)

**Example docker-compose.yml:**
```yaml
environment:
  - LOG_LEVEL=DEBUG  # Enable detailed logging
```

### Log Rotation

- Log files automatically rotate at **10MB**
- Keeps **5 backup files** (50MB total maximum)
- Prevents disk space issues on long-running containers

### What Gets Logged

- **INFO**: Plex connections, playlist generation progress, summary statistics
- **DEBUG**: Detailed API calls, show filtering, episode distribution steps
- **WARNING**: Fallback behaviors, missing configuration
- **ERROR**: Authentication failures, API errors, playlist creation failures

### Troubleshooting with Logs

**Connection Issues:**
```bash
docker logs saturdaymorningplex | grep -i "connection"
```

**Playlist Generation:**
```bash
docker logs saturdaymorningplex | grep -i "playlist"
```

**All Errors:**
```bash
docker logs saturdaymorningplex | grep -i "error"
```

## 📖 Usage

### Web Interface

1. **Access the Interface**
   - Navigate to `http://your-server-ip:5000`

2. **Test Connection**
   - Click "Test Plex Connection" to verify your Plex server is accessible

3. **Configure Content Ratings**
   - Enter desired content ratings (comma-separated)
   - Click "Load Available Ratings" to see what's in your library

4. **Generate Playlists**
   - Click "Generate Playlists"
   - Wait for processing (may take a few minutes for large libraries)
   - View the results

5. **View/Delete Playlists**
   - Use the interface to manage your generated playlists

## 🤝 Contributing

Contributions are welcome! Issues and PRs at: https://github.com/jozefaz/SaturdayMorningPlex

## 📝 License

MIT License

---

**Made with ❤️ for Saturday morning cartoon lovers everywhere!**
