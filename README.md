# SaturdayMorningPlex

A containerized web application designed for deployment on UnRAID servers.

## Features

- 🐳 Docker containerized
- 🚀 UnRAID ready with template
- 🔒 Non-root user for security
- ✅ Health check endpoints
- 🎨 Modern web interface
- 📊 RESTful API ready

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/SaturdayMorningPlex.git
   cd SaturdayMorningPlex
   ```

2. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Open browser: http://localhost:5000
   - Health check: http://localhost:5000/health
   - API info: http://localhost:5000/api/info

### Build Docker Image

```bash
# Build the image
docker build -t saturdaymorningplex:latest .

# Run the container
docker run -d \
  --name saturdaymorningplex \
  -p 5000:5000 \
  -e TZ=America/New_York \
  saturdaymorningplex:latest
```

## UnRAID Deployment

### Method 1: Community Applications (Recommended)

Once published to Community Applications:

1. Open UnRAID web interface
2. Go to **Apps** tab
3. Search for "SaturdayMorningPlex"
4. Click **Install**
5. Configure settings and click **Apply**

### Method 2: Manual Template Installation

1. Copy `unraid-template.xml` to your UnRAID template folder:
   ```bash
   /boot/config/plugins/dockerMan/templates-user/
   ```

2. In UnRAID, go to **Docker** tab
3. Click **Add Container**
4. Select **SaturdayMorningPlex** from template dropdown
5. Configure and click **Apply**

### Method 3: Docker Hub Pull

1. In UnRAID Docker tab, click **Add Container**
2. Set **Repository**: `yourdockerhub/saturdaymorningplex:latest`
3. Set **Port**: `5000` → `5000`
4. Add environment variables:
   - `TZ`: Your timezone (e.g., `America/New_York`)
5. Click **Apply**

## Publishing to Docker Hub

1. **Create Docker Hub account** at https://hub.docker.com

2. **Login to Docker Hub**
   ```bash
   docker login
   ```

3. **Tag your image**
   ```bash
   docker tag saturdaymorningplex:latest yourdockerhub/saturdaymorningplex:latest
   docker tag saturdaymorningplex:latest yourdockerhub/saturdaymorningplex:1.0.0
   ```

4. **Push to Docker Hub**
   ```bash
   docker push yourdockerhub/saturdaymorningplex:latest
   docker push yourdockerhub/saturdaymorningplex:1.0.0
   ```

## Publishing to UnRAID Community Applications

1. **Fork the Community Applications repository**
   - Go to https://github.com/Squidly271/dockerTemplates
   - Click **Fork**

2. **Add your template**
   - Copy your `unraid-template.xml` to the forked repo
   - Update the XML with correct Docker Hub URLs

3. **Create Pull Request**
   - Submit PR to main repository
   - Wait for approval from moderators

4. **Alternative: Custom Repository**
   - Host your template XML on GitHub
   - Users can add your repository URL to their UnRAID:
     - Go to **Apps** → **Settings**
     - Add your template repository URL

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_PORT` | `5000` | Application listening port |
| `APP_HOST` | `0.0.0.0` | Host binding address |
| `TZ` | `America/New_York` | Timezone for container |

### Ports

| Container Port | Description |
|----------------|-------------|
| `5000` | Web interface and API |

### Volumes (Optional)

Uncomment in `docker-compose.yml` or UnRAID template:

| Container Path | Description |
|----------------|-------------|
| `/app/data` | Application data storage |
| `/app/config` | Configuration files |

## API Endpoints

- `GET /` - Main web interface
- `GET /health` - Health check endpoint
- `GET /api/info` - Application information

## Customization

### Modify the Application

1. Edit `app.py` to add your functionality
2. Update `templates/index.html` for UI changes
3. Add dependencies to `requirements.txt`
4. Rebuild the Docker image

### Example: Add New Route

```python
@app.route('/api/custom')
def custom_endpoint():
    return jsonify({'message': 'Custom endpoint'})
```

## Development

### Prerequisites

- Python 3.11+
- Docker
- Docker Compose

### Local Development Without Docker

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

## Testing

```bash
# Test health endpoint
curl http://localhost:5000/health

# Test info endpoint
curl http://localhost:5000/api/info
```

## Troubleshooting

### Container won't start
- Check logs: `docker logs saturdaymorningplex`
- Verify port 5000 is not in use
- Check file permissions

### Can't access web interface
- Ensure container is running: `docker ps`
- Check firewall settings
- Verify correct port mapping

### Health check failing
- Check application logs
- Verify Python dependencies installed
- Test endpoint manually: `curl http://localhost:5000/health`

## Security Notes

- Container runs as non-root user (UID 1000)
- No privileged mode required
- Health checks enabled
- Minimal base image (Python slim)

## License

MIT License - feel free to modify and distribute

## Support

- Issues: https://github.com/yourusername/SaturdayMorningPlex/issues
- Discussions: https://github.com/yourusername/SaturdayMorningPlex/discussions

## Contributing

Pull requests are welcome! For major changes, please open an issue first.

## Changelog

### v1.0.0 (2025-12-08)
- Initial release
- Basic web interface
- Health check endpoints
- UnRAID template
- Docker Hub ready

---

**Note**: Replace `yourdockerhub` and `yourusername` with your actual Docker Hub username and GitHub username throughout the files.
