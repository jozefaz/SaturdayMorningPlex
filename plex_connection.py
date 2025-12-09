"""
Plex connection and authentication module for SaturdayMorningPlex
"""
import logging
import urllib3
from plexapi.server import PlexServer
from plexapi.myplex import MyPlexAccount
from plexapi.exceptions import BadRequest, Unauthorized

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class PlexConnection:
    """Handles Plex server connections and authentication"""
    
    def __init__(self, baseurl=None, token=None, username=None, password=None, servername=None):
        """
        Initialize Plex connection
        
        Args:
            baseurl: Direct URL to Plex server (e.g., http://192.168.1.100:32400)
            token: Plex authentication token
            username: MyPlex username (for remote connection)
            password: MyPlex password (for remote connection)
            servername: Name of the Plex server (required if using username/password)
        """
        self.baseurl = baseurl
        self.token = token
        self.username = username
        self.password = password
        self.servername = servername
        self.plex = None
        self._account = None
    
    def connect(self):
        """
        Connect to Plex server using provided credentials
        
        Returns:
            PlexServer instance
        
        Raises:
            ValueError: If connection parameters are invalid
            Unauthorized: If authentication fails
        """
        try:
            # Method 1: Direct connection with baseurl and token
            if self.baseurl and self.token:
                logger.info(f"Connecting to Plex server at {self.baseurl}")
                # Create session with SSL verification disabled for local HTTPS connections
                session = None
                if self.baseurl.startswith('https://'):
                    import requests
                    session = requests.Session()
                    session.verify = False
                    logger.debug("SSL verification disabled for HTTPS connection")
                
                self.plex = PlexServer(self.baseurl, self.token, session=session)
                logger.info(f"Connected to Plex server: {self.plex.friendlyName}")
                return self.plex
            
            # Method 2: MyPlex account connection
            elif self.username and self.password:
                logger.info(f"Logging into MyPlex account: {self.username}")
                self._account = MyPlexAccount(self.username, self.password)
                
                if not self.servername:
                    # List available servers
                    resources = self._account.resources()
                    server_names = [r.name for r in resources if r.product == 'Plex Media Server']
                    raise ValueError(
                        f"Server name required. Available servers: {', '.join(server_names)}"
                    )
                
                logger.info(f"Connecting to server: {self.servername}")
                resource = self._account.resource(self.servername)
                self.plex = resource.connect()
                logger.info(f"Connected to Plex server: {self.plex.friendlyName}")
                return self.plex
            
            else:
                raise ValueError(
                    "Invalid connection parameters. Provide either:\n"
                    "1. baseurl + token, OR\n"
                    "2. username + password + servername"
                )
        
        except Unauthorized as e:
            logger.error(f"Authentication failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Plex server: {e}")
            raise
    
    def test_connection(self):
        """
        Test the Plex connection
        
        Returns:
            dict: Connection status and server info
        """
        logger.debug("Testing Plex connection")
        try:
            if not self.plex:
                self.connect()
            
            sections = [section.title for section in self.plex.library.sections()]
            logger.info(f"Connection test successful: {self.plex.friendlyName} ({len(sections)} sections)")
            
            return {
                'success': True,
                'server_name': self.plex.friendlyName,
                'version': self.plex.version,
                'platform': self.plex.platform,
                'platform_version': self.plex.platformVersion,
                'library_sections': sections
            }
        except Exception as e:
            logger.error(f"Connection test failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_tv_section(self, section_name='TV Shows'):
        """
        Get the TV Shows library section
        
        Args:
            section_name: Name of the TV library section
        
        Returns:
            LibrarySection for TV shows
        """
        if not self.plex:
            self.connect()
        
        logger.debug(f"Fetching TV section: {section_name}")
        try:
            section = self.plex.library.section(section_name)
            logger.info(f"Found TV section: {section_name}")
            return section
        except Exception as e:
            logger.error(f"Failed to get TV section '{section_name}': {e}")
            logger.debug("Attempting to find any TV section as fallback")
            # Try to find any TV section
            for section in self.plex.library.sections():
                if section.type == 'show':
                    logger.info(f"Found TV section: {section.title}")
                    return section
            raise ValueError(f"No TV library section found. Available sections: "
                           f"{[s.title for s in self.plex.library.sections()]}")
    
    def get_available_servers(self):
        """
        Get list of available Plex servers (requires MyPlex account)
        
        Returns:
            list: Available server names
        """
        logger.debug("Fetching available servers from MyPlex")
        if not self._account:
            if not (self.username and self.password):
                raise ValueError("MyPlex username and password required")
            logger.info("Logging into MyPlex to get server list")
            self._account = MyPlexAccount(self.username, self.password)
        
        resources = self._account.resources()
        servers = [
            {
                'name': r.name,
                'product': r.product,
                'platform': r.platform,
                'owned': r.owned
            }
            for r in resources if r.product == 'Plex Media Server'
        ]
        logger.info(f"Found {len(servers)} Plex servers")
        return servers
