# UnRAID Deployment Guide

This guide provides detailed instructions for deploying SaturdayMorningPlex on your UnRAID server.

## Prerequisites

- UnRAID 6.9 or newer
- Community Applications plugin installed (recommended)
- Basic understanding of Docker containers

## Installation Methods

### Method 1: Using Community Applications (Once Published)

This is the easiest method once the app is published to the Community Applications repository.

1. Open your UnRAID web interface
2. Navigate to the **Apps** tab
3. Search for "SaturdayMorningPlex"
4. Click the app card
5. Click **Install**
6. Configure the settings:
   - **Port**: Default is 5000 (change if needed)
   - **Timezone**: Set your timezone (e.g., `America/New_York`)
7. Click **Apply**
8. Wait for the container to download and start

### Method 2: Manual Template Installation

Use this method if the app isn't in Community Applications yet.

1. Download the `unraid-template.xml` file from this repository

2. Copy it to your UnRAID server:
   ```bash
   # Using SCP or WinSCP
   scp unraid-template.xml root@your-unraid-ip:/boot/config/plugins/dockerMan/templates-user/
   ```

3. In UnRAID web interface:
   - Go to **Docker** tab
   - Click **Add Container**
   - Select **SaturdayMorningPlex** from the template dropdown
   - Configure settings
   - Click **Apply**

### Method 3: Direct Docker Command

For advanced users who prefer command line:

1. SSH into your UnRAID server

2. Run the Docker command:
   ```bash
   docker run -d \
     --name='SaturdayMorningPlex' \
     --net='bridge' \
     -e TZ="America/New_York" \
     -e APP_PORT='5000' \
     -e APP_HOST='0.0.0.0' \
     -p '5000:5000/tcp' \
     'yourdockerhub/saturdaymorningplex:latest'
   ```

### Method 4: Custom Repository URL

If you're hosting your own template repository:

1. In UnRAID, go to **Apps** → **Settings**
2. Scroll to "Template Repositories"
3. Add your repository URL:
   ```
   https://raw.githubusercontent.com/yourusername/SaturdayMorningPlex/main/
   ```
4. Click **Save**
5. Go back to **Apps** tab and search for your application

## Configuration

### Basic Settings

| Setting | Description | Default | Required |
|---------|-------------|---------|----------|
| **Container Name** | Name of the container | SaturdayMorningPlex | Yes |
| **Repository** | Docker Hub image | yourdockerhub/saturdaymorningplex | Yes |
| **WebUI Port** | External port to access app | 5000 | Yes |
| **Timezone** | Container timezone | America/New_York | No |

### Advanced Settings

| Setting | Description | Default |
|---------|-------------|---------|
| **Network Type** | Container network mode | bridge |
| **Privileged** | Privileged container mode | false |
| **APP_PORT** | Internal application port | 5000 |
| **APP_HOST** | Application host binding | 0.0.0.0 |

### Optional: Add Persistent Storage

If you want to save data between container updates:

1. In the Docker template, add paths:
   - **Data Path**: `/mnt/user/appdata/saturdaymorningplex/data` → `/app/data`
   - **Config Path**: `/mnt/user/appdata/saturdaymorningplex/config` → `/app/config`

2. UnRAID will automatically create these directories

## Accessing the Application

After installation:

1. Find the container IP or use your UnRAID server IP
2. Open browser: `http://your-unraid-ip:5000`
3. You should see the SaturdayMorningPlex interface

### Using UnRAID Dashboard

- Click the container icon in the Docker tab
- Select **WebUI** to open in browser

## Updating the Container

### Using UnRAID UI

1. Go to **Docker** tab
2. Click the container icon
3. Select **Check for Updates**
4. If update available, click **Update**
5. Container will stop, update, and restart

### Force Update

1. Stop the container
2. Click container icon → **Force Update**
3. Start the container

## Troubleshooting

### Container Won't Start

**Check logs:**
1. Docker tab → Container icon → **Logs**
2. Look for error messages

**Common issues:**
- Port 5000 already in use
  - Solution: Change external port in template
- Permission issues
  - Solution: Check appdata folder permissions

### Can't Access WebUI

1. Verify container is running (green icon in Docker tab)
2. Check correct port: `http://your-unraid-ip:5000`
3. Check UnRAID firewall settings
4. Try using UnRAID IP instead of hostname

### Container Crashes or Restarts

1. Check logs for errors
2. Verify environment variables are correct
3. Check available system resources
4. Try removing and reinstalling container

## Port Conflicts

If port 5000 is already in use:

1. Edit container template
2. Change **WebUI Port** from 5000 to another port (e.g., 5001)
3. Access via: `http://your-unraid-ip:5001`

## Data Backup

If using persistent storage:

1. Your data is in: `/mnt/user/appdata/saturdaymorningplex/`
2. Include this in your UnRAID backup strategy
3. Can be backed up with:
   - CA Backup/Restore Appdata plugin
   - Manual copy to backup location

## Removing the Container

1. Stop the container
2. Click container icon → **Remove**
3. Optionally delete appdata:
   ```bash
   rm -rf /mnt/user/appdata/saturdaymorningplex/
   ```

## Best Practices

1. **Set Resource Limits** (optional):
   - Click container → Edit
   - Advanced View → CPU Pinning
   - Set memory limits if needed

2. **Use Consistent Naming**:
   - Keep default name for easier support

3. **Regular Updates**:
   - Check for updates monthly
   - Read changelog before updating

4. **Monitor Logs**:
   - Periodically check logs for issues
   - Set up log rotation if needed

## Security Considerations

- Container runs as non-root user (UID 1000)
- No privileged mode required
- Runs in bridge network mode
- Only exposes necessary port (5000)

## Network Access

### Accessing from Outside Network

1. **Port Forwarding** (not recommended):
   - Forward port 5000 on your router
   - Use your public IP: `http://your-public-ip:5000`

2. **VPN** (recommended):
   - Use WireGuard or OpenVPN on UnRAID
   - Access via VPN tunnel

3. **Reverse Proxy** (recommended):
   - Use Nginx Proxy Manager or Swag
   - Enable HTTPS access
   - Use custom domain

## Performance Tuning

For better performance on UnRAID:

1. **Use cache drive** for appdata:
   - Ensure appdata is on cache/SSD
   - Helps with faster container operations

2. **Adjust worker count** (advanced):
   - Edit Dockerfile
   - Change gunicorn workers based on CPU cores

## Support

If you encounter issues:

1. Check container logs first
2. Review this guide
3. Check GitHub issues: https://github.com/yourusername/SaturdayMorningPlex/issues
4. Post in UnRAID forums with:
   - Container logs
   - UnRAID version
   - Docker template settings

## Advanced: Custom Docker Network

To use a custom Docker network:

1. Create custom network in UnRAID
2. Edit container template
3. Change **Network Type** to your custom network
4. Update any dependent containers

---

**Note**: Replace `yourdockerhub` and `yourusername` with actual values when deploying.
