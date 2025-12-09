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
        Get all episodes from the shows, organized by show.
        Deduplicates episodes across libraries by selecting highest quality version.
        
        Args:
            shows: List of Show objects (may contain duplicates from multiple libraries)
        
        Returns:
            dict: {show_title: [episodes_in_order]}
        """
        import random
        
        # First pass: collect all episodes with quality metrics
        # Key format: "ShowTitle|S01E01"
        episode_candidates = {}  # {episode_key: [episode_objects]}
        
        for show in shows:
            try:
                episodes = show.episodes()
                if not episodes:
                    continue
                    
                for episode in episodes:
                    # Create unique key for this episode
                    season = f"S{episode.parentIndex:02d}" if episode.parentIndex else "S00"
                    ep_num = f"E{episode.index:02d}" if episode.index else "E00"
                    episode_key = f"{show.title}|{season}{ep_num}"
                    
                    if episode_key not in episode_candidates:
                        episode_candidates[episode_key] = []
                    episode_candidates[episode_key].append(episode)
                    
            except Exception as e:
                logger.error(f"Error fetching episodes for {show.title}: {e}")
        
        # Second pass: select best quality version of each episode
        show_episodes = {}
        total_episodes = 0
        deduplication_stats = {'total_candidates': 0, 'duplicates_found': 0, 'selected': 0}
        
        for episode_key, candidates in episode_candidates.items():
            deduplication_stats['total_candidates'] += len(candidates)
            
            if len(candidates) > 1:
                deduplication_stats['duplicates_found'] += 1
                logger.debug(f"Found {len(candidates)} versions of {episode_key}")
            
            # Select best quality episode
            best_episode = self._select_best_episode(candidates)
            deduplication_stats['selected'] += 1
            
            # Extract show title from key
            show_title = episode_key.split('|')[0]
            
            if show_title not in show_episodes:
                show_episodes[show_title] = []
            show_episodes[show_title].append(best_episode)
        
        # Sort episodes by air date within each show
        for show_title in show_episodes:
            show_episodes[show_title] = sorted(
                show_episodes[show_title],
                key=lambda ep: ep.originallyAvailableAt if ep.originallyAvailableAt else ep.addedAt
            )
            total_episodes += len(show_episodes[show_title])
            logger.info(f"{show_title}: {len(show_episodes[show_title])} episodes")
        
        logger.info(f"Total episodes collected: {total_episodes}")
        logger.info(f"Deduplication: {deduplication_stats['total_candidates']} candidates, "
                   f"{deduplication_stats['duplicates_found']} duplicates found, "
                   f"{deduplication_stats['selected']} unique episodes selected")
        
        return show_episodes
    
    def _select_best_episode(self, candidates):
        """
        Select the best quality episode from multiple candidates.
        Priority: Highest bitrate > Largest filesize > Random
        
        Args:
            candidates: List of Episode objects
        
        Returns:
            Episode: The best quality episode
        """
        import random
        
        if len(candidates) == 1:
            return candidates[0]
        
        # Get quality metrics for each candidate
        candidates_with_metrics = []
        for ep in candidates:
            try:
                # Get media info
                media = ep.media[0] if ep.media else None
                bitrate = media.bitrate if media and hasattr(media, 'bitrate') else 0
                
                # Get file size
                parts = media.parts if media and hasattr(media, 'parts') else []
                filesize = parts[0].size if parts and hasattr(parts[0], 'size') else 0
                
                candidates_with_metrics.append({
                    'episode': ep,
                    'bitrate': bitrate or 0,
                    'filesize': filesize or 0
                })
                
                logger.debug(f"  {ep.grandparentTitle} {ep.seasonEpisode}: "
                           f"bitrate={bitrate}, size={filesize}")
            except Exception as e:
                logger.warning(f"Error getting metrics for episode: {e}")
                candidates_with_metrics.append({
                    'episode': ep,
                    'bitrate': 0,
                    'filesize': 0
                })
        
        # Sort by bitrate (descending), then filesize (descending)
        candidates_with_metrics.sort(
            key=lambda x: (x['bitrate'], x['filesize']),
            reverse=True
        )
        
        # Check if top candidates have same quality
        best = candidates_with_metrics[0]
        ties = [c for c in candidates_with_metrics 
                if c['bitrate'] == best['bitrate'] and c['filesize'] == best['filesize']]
        
        if len(ties) > 1:
            logger.debug(f"  Quality tie between {len(ties)} versions, selecting randomly")
            selected = random.choice(ties)
        else:
            selected = best
            logger.debug(f"  Selected version: bitrate={selected['bitrate']}, "
                       f"size={selected['filesize']}")
        
        return selected['episode']
    
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
            
            # Sort week episodes by air date (oldest first)
            if week_episodes:
                week_episodes.sort(
                    key=lambda ep: ep['episode'].originallyAvailableAt if ep['episode'].originallyAvailableAt else ep['episode'].addedAt
                )
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
                    should_replace = False
                    try:
                        existing = self.plex.playlist(playlist_title)
                        existing_count = len(existing.items())
                        expected_count = len(episodes)
                        
                        if existing_count != expected_count:
                            logger.warning(f"Playlist '{playlist_title}' exists but is incomplete: "
                                         f"{existing_count} episodes (expected {expected_count})")
                            should_replace = True
                        else:
                            logger.info(f"Playlist '{playlist_title}' already exists with correct episode count ({existing_count})")
                            should_replace = True  # Replace anyway to ensure fresh content
                        
                        if should_replace:
                            logger.info(f"Deleting existing playlist '{playlist_title}'...")
                            existing.delete()
                    except:
                        # Playlist doesn't exist, which is fine
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
            tv_section_name: Name of TV library section (string) or list of library names
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
            # Support both single library and multiple libraries
            if isinstance(tv_section_name, str):
                library_names = [tv_section_name]
            else:
                library_names = tv_section_name
            
            # Collect shows from all libraries
            all_shows = []
            for lib_name in library_names:
                logger.debug(f"Fetching TV section: {lib_name}")
                tv_section = self.plex.library.section(lib_name)
                shows = self.get_filtered_shows(tv_section, content_ratings)
                all_shows.extend(shows)
                logger.info(f"Found {len(shows)} shows in '{lib_name}'")
            
            if not all_shows:
                logger.warning("No shows found matching criteria!")
                return {
                    'success': False,
                    'error': f'No shows found with ratings: {content_ratings}'
                }
            
            # Get all episodes
            logger.info("Collecting episodes from shows...")
            show_episodes = self.get_all_episodes(all_shows)
            
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
