# SaturdayMorningPlex

Automatically generate Saturday morning cartoon-style weekly playlists for your Plex server!

## ✨ Features

- 🎬 **Automated Playlist Generation** - Creates 52 weekly playlists per year
- 🎯 **Content Rating Filtering** - Filter shows by G, PG, PG-13, TV-Y, TV-Y7, etc.
- 📺 **Smart Distribution** - Each week gets one episode from each show
- 🔄 **Multi-Season Support** - Automatically continues to next seasons
- 📅 **Multi-Year Generation** - Creates playlists until all episodes are included
- 🐳 **Docker & UnRAID Ready** - Easy deployment with Docker or UnRAID
- 🌐 **Web Interface** - Simple, intuitive control panel

## 🎯 How It Works

1. **Connect to Plex** - Authenticate with your Plex Media Server
2. **Filter Shows** - Select content ratings (e.g., G, PG)
3. **Generate Playlists** - Creates weekly playlists:
   - Week 1: One episode from each show (S01E01 of all shows)
   - Week 2: Next episode from each show (S01E02 of all shows)
   - Week 3: Continue pattern...
   - When a show runs out of season 1, moves to season 2
4. **Multiple Years** - Continues creating years until all episodes are used

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

## 🚀 Quick Start

### Prerequisites

- Plex Media Server with TV Shows library
- Docker or UnRAID server
- Plex authentication token (see [Getting Your Plex Token](#getting-your-plex-token))

### Option 1: Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/jozefaz/SaturdayMorningPlex.git
   cd SaturdayMorningPlex
   ```

2. **Configure your settings** (choose one method):

   **Method A: Using .env file (Recommended for local dev/testing)**
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env with your settings
   nano .env  # or use your preferred editor
   ```
   
   Update these values in `.env`:
   ```bash
   PLEX_URL=http://192.168.1.100:32400  # Your Plex server URL
   PLEX_TOKEN=your_token_here            # Your Plex token
   TV_LIBRARY_NAME=TV Shows              # Your TV library name
   CONTENT_RATINGS=G,PG                  # Desired content ratings
   ```

   **Method B: Edit docker-compose.yml directly**
   ```yaml
   environment:
     - PLEX_URL=http://192.168.1.100:32400
     - PLEX_TOKEN=your_token_here
     - TV_LIBRARY_NAME=TV Shows
     - CONTENT_RATINGS=G,PG
   ```

3. **Start the container**
   ```bash
   docker-compose up -d
   ```

4. **Access the web interface**
   - Open: `http://your-server-ip:5000`

### Option 2: UnRAID

See [UNRAID_DEPLOYMENT.md](UNRAID_DEPLOYMENT.md) for detailed UnRAID installation instructions.

## 🔧 Configuration

### Using .env File (Recommended)

The `.env` file stores your configuration persistently - similar to how UnRAID saves container settings. This file is git-ignored, so your credentials stay private.

**Setup:**
```bash
cp .env.example .env
# Edit .env with your actual values
```

**Benefits:**
- ✅ Settings persist across restarts
- ✅ No need to edit docker-compose.yml
- ✅ Safe for version control (git-ignored)
- ✅ Easy to manage multiple environments

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
| `APP_PORT` | No | `5000` | Port for web interface |
| `TZ` | No | `America/New_York` | Timezone for container |

\* Use either `PLEX_URL` + `PLEX_TOKEN` OR `PLEX_USERNAME` + `PLEX_PASSWORD` + `PLEX_SERVER_NAME`

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
