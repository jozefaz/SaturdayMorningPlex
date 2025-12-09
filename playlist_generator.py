"""
Playlist generation logic for Saturday Morning Plex
Creates weekly playlists distributed across the year
"""
import logging
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class PlaylistGenerator:
    """Generates Saturday morning-style weekly playlists"""
    
    def __init__(self, plex_connection):
        """
        Initialize playlist generator
        
        Args:
            plex_connection: PlexConnection instance
        """
        self.plex = plex_connection.plex
        if not self.plex:
            raise ValueError("Plex connection not established")
    
    def get_filtered_shows(self, tv_section, content_ratings):
        """
        Get TV shows filtered by content rating
        
        Args:
            tv_section: Plex TV library section
            content_ratings: List of content ratings to include (e.g., ['G', 'PG'])
        
        Returns:
            list: Filtered TV show objects
        """
        logger.info(f"Fetching shows with content ratings: {content_ratings}")
        
        all_shows = tv_section.all()
        filtered_shows = []
        
        for show in all_shows:
            # Check if show's content rating matches any in the list
            if show.contentRating in content_ratings:
                filtered_shows.append(show)
                logger.debug(f"Included: {show.title} ({show.contentRating})")
            else:
                logger.debug(f"Excluded: {show.title} ({show.contentRating})")
        
        logger.info(f"Found {len(filtered_shows)} shows matching criteria")
        return filtered_shows
    
    def get_all_episodes(self, shows):
        """
        Get all episodes from the shows, organized by show
        
        Args:
            shows: List of Show objects
        
        Returns:
            dict: {show_title: [episodes_in_order]}
        """
        show_episodes = {}
        total_episodes = 0
        
        for show in shows:
            try:
                # Get all episodes for this show (in order)
                episodes = show.episodes()
                if episodes:
                    show_episodes[show.title] = episodes
                    total_episodes += len(episodes)
                    logger.info(f"{show.title}: {len(episodes)} episodes")
            except Exception as e:
                logger.error(f"Error fetching episodes for {show.title}: {e}")
        
        logger.info(f"Total episodes collected: {total_episodes}")
        return show_episodes
    
    def distribute_episodes_to_weeks(self, show_episodes, weeks_per_year=52):
        """
        Distribute episodes across weeks in a round-robin fashion
        Each week gets one episode from each show (if available)
        
        Args:
            show_episodes: Dict of {show_title: [episodes]}
            weeks_per_year: Number of weeks to create (default 52)
        
        Returns:
            dict: {year: {week: [episodes]}}
        """
        logger.info("Distributing episodes across weeks...")
        
        # Track episode index for each show
        show_indices = {show: 0 for show in show_episodes.keys()}
        
        # Track which shows still have episodes available
        active_shows = set(show_episodes.keys())
        
        # Structure: {year: {week: [episodes]}}
        yearly_playlists = defaultdict(lambda: defaultdict(list))
        
        year = 1
        week = 1
        
        while active_shows:
            # For this week, add one episode from each active show
            week_episodes = []
            
            for show_title in sorted(active_shows):  # Sort for consistent ordering
                episodes = show_episodes[show_title]
                current_index = show_indices[show_title]
                
                if current_index < len(episodes):
                    episode = episodes[current_index]
                    week_episodes.append({
                        'show': show_title,
                        'episode': episode,
                        'season': episode.parentIndex,
                        'episode_num': episode.index,
                        'title': episode.title
                    })
                    show_indices[show_title] += 1
                else:
                    # This show has no more episodes
                    active_shows.discard(show_title)
            
            if week_episodes:
                yearly_playlists[year][week] = week_episodes
                logger.debug(f"Year {year}, Week {week}: {len(week_episodes)} episodes")
            
            week += 1
            
            # Move to next year after 52 weeks
            if week > weeks_per_year:
                if not active_shows:
                    break
                logger.info(f"Completed Year {year} with {weeks_per_year} weeks")
                year += 1
                week = 1
        
        logger.info(f"Created {year} years of playlists")
        return dict(yearly_playlists)
    
    def create_plex_playlists(self, yearly_playlists, playlist_prefix="Saturday Morning"):
        """
        Create actual Plex playlists from the generated structure
        
        Args:
            yearly_playlists: Dict from distribute_episodes_to_weeks()
            playlist_prefix: Prefix for playlist names
        
        Returns:
            list: Created playlist objects
        """
        logger.info("Creating Plex playlists...")
        created_playlists = []
        
        for year, weeks in yearly_playlists.items():
            for week, episode_data in weeks.items():
                if not episode_data:
                    continue
                
                # Extract episode objects
                episodes = [ep['episode'] for ep in episode_data]
                
                # Create playlist name
                playlist_title = f"{playlist_prefix} - Year {year} Week {week:02d}"
                
                try:
                    # Check if playlist already exists
                    existing = None
                    try:
                        existing = self.plex.playlist(playlist_title)
                        logger.info(f"Playlist '{playlist_title}' already exists, deleting...")
                        existing.delete()
                    except:
                        pass
                    
                    # Create new playlist
                    from plexapi.playlist import Playlist
                    playlist = Playlist.create(
                        server=self.plex,
                        title=playlist_title,
                        items=episodes
                    )
                    
                    created_playlists.append(playlist)
                    logger.info(f"Created: {playlist_title} ({len(episodes)} episodes)")
                    
                except Exception as e:
                    logger.error(f"Failed to create playlist '{playlist_title}': {e}")
        
        logger.info(f"Successfully created {len(created_playlists)} playlists")
        return created_playlists
    
    def generate_all_playlists(self, tv_section_name, content_ratings, 
                               playlist_prefix="Saturday Morning", 
                               weeks_per_year=52):
        """
        Complete workflow: filter shows, distribute episodes, create playlists
        
        Args:
            tv_section_name: Name of TV library section
            content_ratings: List of content ratings (e.g., ['G', 'PG'])
            playlist_prefix: Prefix for playlist names
            weeks_per_year: Number of weeks per year
        
        Returns:
            dict: Summary of operation
        """
        logger.info("="*60)
        logger.info("Starting playlist generation workflow")
        logger.info(f"TV Section: {tv_section_name}")
        logger.info(f"Content Ratings: {content_ratings}")
        logger.info(f"Playlist Prefix: {playlist_prefix}")
        logger.info(f"Weeks per Year: {weeks_per_year}")
        logger.info("="*60)
        
        try:
            # Get TV section
            logger.debug(f"Fetching TV section: {tv_section_name}")
            tv_section = self.plex.library.section(tv_section_name)
            
            # Filter shows by content rating
            shows = self.get_filtered_shows(tv_section, content_ratings)
            
            if not shows:
                logger.warning("No shows found matching criteria!")
                return {
                    'success': False,
                    'error': f'No shows found with ratings: {content_ratings}'
                }
            
            # Get all episodes
            logger.info("Collecting episodes from shows...")
            show_episodes = self.get_all_episodes(shows)
            
            if not show_episodes:
                logger.error("No episodes found in selected shows")
                return {
                    'success': False,
                    'error': 'No episodes found in selected shows'
                }
            
            # Distribute episodes to weeks
            yearly_playlists = self.distribute_episodes_to_weeks(
                show_episodes, 
                weeks_per_year
            )
            
            # Create Plex playlists
            created_playlists = self.create_plex_playlists(
                yearly_playlists, 
                playlist_prefix
            )
            
            # Calculate statistics
            total_episodes = sum(
                len(week_eps) 
                for year_data in yearly_playlists.values() 
                for week_eps in year_data.values()
            )
            
            logger.info("="*60)
            logger.info("Playlist generation complete!")
            logger.info(f"Shows: {len(shows)}")
            logger.info(f"Total Episodes: {total_episodes}")
            logger.info(f"Years: {len(yearly_playlists)}")
            logger.info(f"Playlists Created: {len(created_playlists)}")
            logger.info("="*60)
            
            return {
                'success': True,
                'shows_count': len(shows),
                'shows': [s.title for s in shows],
                'total_episodes': total_episodes,
                'years_generated': len(yearly_playlists),
                'playlists_created': len(created_playlists),
                'playlist_names': [p.title for p in created_playlists[:10]]  # First 10
            }
            
        except Exception as e:
            logger.error(f"Failed to generate playlists: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_playlist_summary(self, playlist_prefix="Saturday Morning"):
        """
        Get summary of existing Saturday Morning playlists
        
        Args:
            playlist_prefix: Prefix to filter playlists
        
        Returns:
            dict: Summary of existing playlists
        """
        logger.debug(f"Getting playlist summary for prefix: {playlist_prefix}")
        try:
            all_playlists = self.plex.playlists()
            matching = [p for p in all_playlists if p.title.startswith(playlist_prefix)]
            
            logger.info(f"Found {len(matching)} playlists with prefix '{playlist_prefix}'")
            
            return {
                'success': True,
                'total_playlists': len(matching),
                'playlists': [
                    {
                        'title': p.title,
                        'item_count': p.leafCount,
                        'duration': p.durationInSeconds
                    }
                    for p in matching
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get playlist summary: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_all_playlists(self, playlist_prefix="Saturday Morning"):
        """
        Delete all playlists with the given prefix
        
        Args:
            playlist_prefix: Prefix to filter playlists to delete
        
        Returns:
            dict: Summary of deletion
        """
        logger.info(f"Deleting all playlists with prefix: {playlist_prefix}")
        try:
            all_playlists = self.plex.playlists()
            matching = [p for p in all_playlists if p.title.startswith(playlist_prefix)]
            
            logger.debug(f"Found {len(matching)} playlists to delete")
            deleted_count = 0
            for playlist in matching:
                try:
                    playlist.delete()
                    deleted_count += 1
                    logger.info(f"Deleted: {playlist.title}")
                except Exception as e:
                    logger.error(f"Failed to delete {playlist.title}: {e}")
            
            logger.info(f"Deletion complete: {deleted_count}/{len(matching)} playlists deleted")
            
            return {
                'success': True,
                'deleted_count': deleted_count,
                'total_found': len(matching)
            }
        except Exception as e:
            logger.error(f"Failed to delete playlists: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
