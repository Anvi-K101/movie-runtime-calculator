#!/usr/bin/env python3
"""
🎬 Ultimate Movie & TV Show Runtime Calculator - Enhanced Streamlit Web App
Comprehensive features: detailed runtime info, cast data, viewing schedules, 
watchlist functionality, trending content, fuzzy search, and detailed descriptions.
Merged from both original versions with all features integrated.
"""

import streamlit as st
import requests
import datetime
from typing import Dict, List, Tuple, Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import json

# TMDb API Configuration
API_KEY = "47aa3b4def8767b97ea958e92b233aec"
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0N2FhM2I0ZGVmODc2N2I5N2VhOTU4ZTkyYjIzM2FlYyIsIm5iZiI6MTc1MzU4NTA3MS4yMjIwMDAxLCJzdWIiOiI2ODg1OTVhZmZiNDE4YjFhYzEzOGY2YTciLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.6dfVkYzjkrLLh7072uq-iMe8D2FoPeFCiZXKtfGVrCI"
BASE_URL = "https://api.themoviedb.org/3"

class RuntimeCalculator:
    """Enhanced API communication class with fuzzy search and comprehensive content fetching"""
    
    def __init__(self, api_key: str, access_token: str):
        self.api_key = api_key
        self.access_token = access_token
        self.headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make a secure API request with error handling"""
        url = f"{BASE_URL}/{endpoint}"
        try:
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            st.error(f"API request failed: {e}")
            return None
    
    def search_suggestions(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for movies and TV shows with suggestions - supports all languages"""
        if len(query) < 2:
            return []
        
        data = self._make_request("search/multi", {
            "query": query,
            "include_adult": False,
            "page": 1
        })
        
        if not data or not data.get('results'):
            return []
        
        # Filter and format results
        results = []
        for item in data.get('results', [])[:limit]:
            if item.get('media_type') in ['movie', 'tv']:
                title = item.get('title') or item.get('name', 'Unknown')
                original_title = item.get('original_title') or item.get('original_name', '')
                
                # Show original title if different
                display_title = title
                if original_title and original_title != title:
                    display_title = f"{title} ({original_title})"
                
                year = ''
                if item.get('release_date'):
                    year = f" [{item['release_date'][:4]}]"
                elif item.get('first_air_date'):
                    year = f" [{item['first_air_date'][:4]}]"
                
                # Add language indicator
                lang = item.get('original_language', '').upper()
                lang_indicator = f" 🌐{lang}" if lang and lang != 'EN' else ""
                
                media_icon = "🎬" if item.get('media_type') == 'movie' else "📺"
                
                results.append({
                    'display': f"{media_icon} {display_title}{year}{lang_indicator}",
                    'title': title,
                    'data': item
                })
        
        return results
    
    def search_title(self, query: str) -> Optional[Dict]:
        """Search for a specific movie or TV show - supports all languages"""
        data = self._make_request("search/multi", {
            "query": query,
            "include_adult": False
        })
        
        if data and data['results']:
            return data['results'][0]
        return None
    
    def get_movie_details(self, movie_id: int) -> Dict:
        """Get detailed movie information including runtime - supports all languages"""
        return self._make_request(f"movie/{movie_id}", {
            "append_to_response": "credits,keywords,reviews,videos,similar,translations"
        }) or {}
    
    def get_tv_details(self, tv_id: int) -> Dict:
        """Get detailed TV show information - supports all languages"""
        return self._make_request(f"tv/{tv_id}", {
            "append_to_response": "credits,keywords,content_ratings,videos,similar,translations"
        }) or {}
    
    def get_season_details(self, tv_id: int, season_number: int) -> Dict:
        """Get detailed season information including episode runtimes"""
        return self._make_request(f"tv/{tv_id}/season/{season_number}", {
            "append_to_response": "credits,videos"
        }) or {}
    
    def get_trending(self, media_type: str = 'all', time_window: str = 'day') -> List[Dict]:
        """Get trending movies and TV shows"""
        data = self._make_request(f"trending/{media_type}/{time_window}")
        return data.get('results', []) if data else []
    
    def get_popular(self, media_type: str = 'movie') -> List[Dict]:
        """Get popular movies or TV shows"""
        data = self._make_request(f"{media_type}/popular")
        return data.get('results', []) if data else []

class WatchlistManager:
    """Enhanced watchlist management with custom items support"""
    
    @staticmethod
    def initialize_watchlist():
        """Initialize watchlist in session state"""
        if 'watchlist_watching' not in st.session_state:
            st.session_state.watchlist_watching = []
        if 'watchlist_want_to_watch' not in st.session_state:
            st.session_state.watchlist_want_to_watch = []
    
    @staticmethod
    def add_to_watchlist(media_data: Dict, list_type: str):
        """Add item to watchlist"""
        WatchlistManager.initialize_watchlist()
        
        item = {
            'id': media_data.get('id'),
            'title': media_data.get('title') or media_data.get('name'),
            'original_title': media_data.get('original_title') or media_data.get('original_name', ''),
            'media_type': media_data.get('media_type'),
            'poster_path': media_data.get('poster_path'),
            'year': media_data.get('release_date', '')[:4] if media_data.get('release_date') else media_data.get('first_air_date', '')[:4],
            'language': media_data.get('original_language', 'en').upper(),
            'added_date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'is_custom': False
        }
        
        target_list_key = 'watchlist_watching' if list_type == 'watching' else 'watchlist_want_to_watch'
        
        # Check if item already exists
        if any(str(existing_item['id']) == str(item['id']) for existing_item in st.session_state[target_list_key]):
            return False
        
        st.session_state[target_list_key].append(item)
        return True
    
    @staticmethod
    def add_custom_item(title: str, media_type: str, list_type: str, year: str = "", notes: str = ""):
        """Add custom item to watchlist"""
        WatchlistManager.initialize_watchlist()
        
        item = {
            'id': f"custom_{len(st.session_state.watchlist_watching) + len(st.session_state.watchlist_want_to_watch)}_{int(datetime.datetime.now().timestamp())}",
            'title': title,
            'original_title': '',
            'media_type': media_type,
            'poster_path': None,
            'year': year,
            'language': 'CUSTOM',
            'added_date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'notes': notes,
            'is_custom': True
        }
        
        target_list_key = 'watchlist_watching' if list_type == 'watching' else 'watchlist_want_to_watch'
        st.session_state[target_list_key].append(item)
        return True
    
    @staticmethod
    def remove_from_watchlist(item_id: str, list_type: str):
        """Remove item from watchlist"""
        target_list_key = 'watchlist_watching' if list_type == 'watching' else 'watchlist_want_to_watch'
        st.session_state[target_list_key] = [
            item for item in st.session_state[target_list_key] 
            if str(item['id']) != str(item_id)
        ]
    
    @staticmethod
    def is_in_watchlist(item_id: int, list_type: str) -> bool:
        """Check if item is in watchlist"""
        WatchlistManager.initialize_watchlist()
        target_list = st.session_state.watchlist_watching if list_type == 'watching' else st.session_state.watchlist_want_to_watch
        return any(str(item['id']) == str(item_id) for item in target_list)

# Utility Functions
def format_time(minutes: int) -> str:
    """Convert minutes to HH:MM format"""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"

def format_detailed_time(total_minutes: int) -> str:
    """Convert minutes to detailed HH:MM:SS format"""
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}:00"

def get_review_summary(rating: float, vote_count: int) -> Tuple[str, str, str]:
    """Generate a review summary based on rating"""
    if rating >= 8.5:
        sentiment = "🌟 Exceptional"; description = "Critically acclaimed masterpiece"; color = "#FFD700"
    elif rating >= 7.5:
        sentiment = "⭐ Excellent"; description = "Highly recommended viewing"; color = "#32CD32"
    elif rating >= 6.5:
        sentiment = "👍 Good"; description = "Solid entertainment value"; color = "#87CEEB"
    elif rating >= 5.5:
        sentiment = "👌 Average"; description = "Mixed but watchable"; color = "#FFA500"
    elif rating >= 4.0:
        sentiment = "👎 Below Average"; description = "Has some issues"; color = "#FF6347"
    else:
        sentiment = "💔 Poor"; description = "Generally not recommended"; color = "#DC143C"
    
    return sentiment, description, color

def get_detailed_description(media_data: Dict, media_type: str) -> str:
    """Create a comprehensive detailed description with extensive information"""
    overview = media_data.get('overview', 'No summary available.')
    additional_sections = []
    
    if media_type == 'movie':
        # Movie specific comprehensive details
        budget = media_data.get('budget', 0)
        revenue = media_data.get('revenue', 0)
        production_companies = media_data.get('production_companies', [])
        production_countries = media_data.get('production_countries', [])
        spoken_languages = media_data.get('spoken_languages', [])
        runtime = media_data.get('runtime', 0)
        
        # Production Information
        prod_info = []
        if budget > 0:
            prod_info.append(f"Budget: ${budget:,}")
        if revenue > 0:
            prod_info.append(f"Box Office: ${revenue:,}")
            if budget > 0:
                profit = revenue - budget
                roi = ((revenue - budget) / budget) * 100 if budget > 0 else 0
                prod_info.append(f"Profit: ${profit:,} (ROI: {roi:.1f}%)")
        
        if prod_info:
            additional_sections.append("💰 **Financial Performance:**\n" + " • ".join(prod_info))
        
        # Production Details
        if production_companies:
            companies = [company['name'] for company in production_companies[:4]]
            additional_sections.append(f"🏢 **Production:** {', '.join(companies)}")
        
        if production_countries:
            countries = [country['name'] for country in production_countries]
            additional_sections.append(f"🌍 **Countries:** {', '.join(countries)}")
        
        if spoken_languages and len(spoken_languages) > 1:
            languages = [lang['english_name'] for lang in spoken_languages]
            additional_sections.append(f"🗣️ **Languages:** {', '.join(languages)}")
        
        if runtime > 0:
            additional_sections.append(f"⏱️ **Runtime:** {format_time(runtime)} ({runtime} minutes)")
    
    else:  # TV show
        # TV show comprehensive details
        networks = media_data.get('networks', [])
        created_by = media_data.get('created_by', [])
        first_air_date = media_data.get('first_air_date', '')
        last_air_date = media_data.get('last_air_date', '')
        status = media_data.get('status', '')
        type_info = media_data.get('type', '')
        origin_country = media_data.get('origin_country', [])
        languages = media_data.get('languages', [])
        number_of_seasons = media_data.get('number_of_seasons', 0)
        number_of_episodes = media_data.get('number_of_episodes', 0)
        
        # Show Status and Dates
        if first_air_date:
            air_info = f"First Aired: {first_air_date}"
            if last_air_date and last_air_date != first_air_date:
                air_info += f" | Last Aired: {last_air_date}"
            if status:
                air_info += f" | Status: {status}"
            additional_sections.append(f"📅 **Air Dates:** {air_info}")
        
        # Show Statistics
        if number_of_seasons > 0 or number_of_episodes > 0:
            stats = []
            if number_of_seasons > 0:
                stats.append(f"{number_of_seasons} Season{'s' if number_of_seasons != 1 else ''}")
            if number_of_episodes > 0:
                stats.append(f"{number_of_episodes} Episode{'s' if number_of_episodes != 1 else ''}")
            if type_info:
                stats.append(f"Type: {type_info}")
            additional_sections.append(f"📊 **Show Info:** {' • '.join(stats)}")
        
        # Network and Creator Info
        if networks:
            network_names = [network['name'] for network in networks]
            additional_sections.append(f"📺 **Network:** {', '.join(network_names)}")
        
        if created_by:
            creators = [creator['name'] for creator in created_by]
            additional_sections.append(f"👨‍💼 **Created by:** {', '.join(creators)}")
        
        if origin_country:
            additional_sections.append(f"🌍 **Origin:** {', '.join(origin_country)}")
        
        if languages and len(languages) > 1:
            additional_sections.append(f"🗣️ **Languages:** {', '.join(languages)}")
    
    # Keywords for context
    keywords = media_data.get('keywords', {})
    if keywords:
        keyword_list = keywords.get('keywords', []) if media_type == 'tv' else keywords.get('keywords', [])
        if keyword_list:
            keyword_names = [kw['name'] for kw in keyword_list[:8]]
            additional_sections.append(f"🏷️ **Themes:** {', '.join(keyword_names)}")
    
    # Reviews snippet
    reviews = media_data.get('reviews', {})
    if reviews and reviews.get('results'):
        review = reviews['results'][0]
        author = review.get('author', 'Anonymous')
        content = review.get('content', '')[:200] + "..." if len(review.get('content', '')) > 200 else review.get('content', '')
        if content:
            additional_sections.append(f"📝 **Review by {author}:** \"{content}\"")
    
    # Combine everything
    detailed_description = f"**📖 Plot Summary:**\n{overview}"
    
    if additional_sections:
        detailed_description += "\n\n" + "\n\n".join(additional_sections)
    
    return detailed_description

def get_star_cast(media_data: Dict, limit: int = 8) -> List[Dict]:
    """Extract star cast information from credits"""
    credits = media_data.get('credits', {})
    cast = credits.get('cast', [])
    
    star_cast = []
    for actor in cast[:limit]:
        star_cast.append({
            'name': actor.get('name', 'Unknown'),
            'character': actor.get('character', 'Unknown Role'),
            'profile_path': actor.get('profile_path'),
            'popularity': actor.get('popularity', 0)
        })
    
    return star_cast

def display_star_cast(star_cast: List[Dict]):
    """Display star cast with expandable view and smaller images"""
    if not star_cast:
        st.info("🎭 Cast information not available")
        return
    
    st.markdown("### 🌟 Star Cast")
    
    # Show first 4 cast members by default
    initial_count = 4
    show_more = len(star_cast) > initial_count
    
    # Display initial cast members
    cols_per_row = 4
    for i in range(0, min(initial_count, len(star_cast)), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, actor in enumerate(star_cast[i:i+cols_per_row]):
            if i + j < initial_count:
                with cols[j]:
                    # Display smaller actor photo
                    if actor['profile_path']:
                        photo_url = f"https://image.tmdb.org/t/p/w185{actor['profile_path']}"
                        st.image(photo_url, width=80)
                    else:
                        st.write("🎭")
                    
                    st.markdown(f"**{actor['name']}**")
                    st.caption(f"as {actor['character']}")
    
    # View More functionality
    if show_more:
        if st.button("👁️ View More Cast", key="view_more_cast"):
            st.session_state.show_full_cast = not st.session_state.get('show_full_cast', False)
        
        if st.session_state.get('show_full_cast', False):
            st.markdown("#### 👥 Full Cast")
            
            # Display remaining cast in smaller format
            remaining_cast = star_cast[initial_count:]
            cols_per_row = 6  # More columns for smaller display
            
            for i in range(0, len(remaining_cast), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, actor in enumerate(remaining_cast[i:i+cols_per_row]):
                    with cols[j]:
                        # Even smaller images for expanded view
                        if actor['profile_path']:
                            photo_url = f"https://image.tmdb.org/t/p/w185{actor['profile_path']}"
                            st.image(photo_url, width=60)
                        else:
                            st.write("🎭")
                        
                        st.markdown(f"**{actor['name']}**", help=f"Character: {actor['character']}")
                        st.caption(actor['character'][:20] + "..." if len(actor['character']) > 20 else actor['character'])
            
            if st.button("👁️ Show Less", key="show_less_cast"):
                st.session_state.show_full_cast = False
                st.rerun()

def create_progress_gauge(current: int, total: int) -> go.Figure:
    """Create a progress gauge chart"""
    if total == 0:
        progress = 0
    else:
        progress = (current / total) * 100
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = progress,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Viewing Progress"},
        delta = {'reference': 100},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "#1f77b4"},
            'steps': [
                {'range': [0, 50], 'color': "lightgray"},
                {'range': [50, 100], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(height=300)
    return fig

def display_media_showcase(media_data: Dict, media_type: str):
    """Display comprehensive media information with adaptive poster sizing and detailed description"""
    if media_type == 'movie':
        title = media_data.get('title', 'Unknown')
        original_title = media_data.get('original_title', '')
        year = media_data.get('release_date', '')[:4] if media_data.get('release_date') else 'Unknown'
        genres = [genre['name'] for genre in media_data.get('genres', [])]
    else:  # TV show
        title = media_data.get('name', 'Unknown')
        original_title = media_data.get('original_name', '')
        year = media_data.get('first_air_date', '')[:4] if media_data.get('first_air_date') else 'Unknown'
        genres = [genre['name'] for genre in media_data.get('genres', [])]
    
    # Display original title if different
    display_title = title
    if original_title and original_title != title:
        display_title = f"{title} ({original_title})"
    
    # Get detailed description
    detailed_description = get_detailed_description(media_data, media_type)
    
    rating = media_data.get('vote_average', 0)
    vote_count = media_data.get('vote_count', 0)
    poster_path = media_data.get('poster_path', '')
    original_language = media_data.get('original_language', 'en').upper()
    
    # Calculate adaptive column sizes based on description length
    description_length = len(detailed_description)
    if description_length > 1200:
        col_ratio = [1, 3.5]  # Much more space for extensive text
    elif description_length > 800:
        col_ratio = [1, 3]  # More space for text
    elif description_length > 400:
        col_ratio = [1, 2]  # Balanced
    else:
        col_ratio = [1, 1.5]  # More space for poster
    
    col1, col2 = st.columns(col_ratio)
    
    # Display poster
    with col1:
        if poster_path:
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            st.image(poster_url, caption=f"{title} Poster", use_container_width=True)
        else:
            st.info("📽️ No poster available")
        
        # Language indicator
        if original_language != 'EN':
            st.info(f"🌐 Language: {original_language}")
        
        # Watchlist buttons
        st.markdown("#### 📝 Add to Watchlist")
        
        watching_button = st.button(
            "📺 Currently Watching" if not WatchlistManager.is_in_watchlist(media_data.get('id'), 'watching') else "✅ Currently Watching",
            key=f"watching_{media_data.get('id')}",
            use_container_width=True
        )
        
        want_to_watch_button = st.button(
            "⭐ Want to Watch" if not WatchlistManager.is_in_watchlist(media_data.get('id'), 'want_to_watch') else "✅ Want to Watch",
            key=f"want_to_watch_{media_data.get('id')}",
            use_container_width=True
        )
        
        if watching_button:
            if WatchlistManager.add_to_watchlist(media_data, 'watching'):
                st.success("Added to Currently Watching!")
            else:
                st.info("Already in Currently Watching list")
        
        if want_to_watch_button:
            if WatchlistManager.add_to_watchlist(media_data, 'want_to_watch'):
                st.success("Added to Want to Watch!")
            else:
                st.info("Already in Want to Watch list")
    
    # Display information
    with col2:
        st.markdown(f"# 🎬 {display_title} ({year})")
        
        if genres:
            genre_badges = " ".join([f"`{genre}`" for genre in genres])
            st.markdown(f"**🎭 Genres:** {genre_badges}")
        
        # Rating display
        sentiment, description, color = get_review_summary(rating, vote_count)
        st.markdown(f"**⭐ Rating:** {sentiment} ({rating:.1f}/10)")
        st.markdown(f"*{description}*")
        st.caption(f"Based on {vote_count:,} user ratings")
        
        # Comprehensive Detailed Summary
        st.markdown("### 📖 Comprehensive Details")
        st.markdown(detailed_description)
    
    # Display star cast below
    star_cast = get_star_cast(media_data)
    display_star_cast(star_cast)

def display_media_card(media: Dict, index: str):
    """Display a media card for homepage trending/popular sections"""
    title = media.get('title') or media.get('name', 'N/A')
    year = (media.get('release_date') or media.get('first_air_date', ''))[:4]
    rating = media.get('vote_average', 0)
    
    if media.get('poster_path'):
        st.image(f"https://image.tmdb.org/t/p/w342{media['poster_path']}", use_container_width=True)
    else:
        st.markdown(
            "<div style='height:300px; display:flex; align-items:center; justify-content:center; background-color:#222; border-radius:10px; color:white;'>No Image</div>", 
            unsafe_allow_html=True
        )
    
    st.markdown(f"**{title}** ({year})")
    if rating > 0:
        st.caption(f"⭐ {rating:.1f}/10")
    
    if st.button("Calculate Runtime", key=f"card_{media.get('id')}_{index}", use_container_width=True):
        media['media_type'] = 'movie' if 'title' in media else 'tv'
        st.session_state.selected_result = media
        st.session_state.search_completed = True
        st.rerun()

def display_homepage():
    """Display the enhanced homepage with trending and popular content"""
    st.markdown("## 🔥 Trending Today")
    trending_media = st.session_state.calculator.get_trending()[:5]
    if trending_media:
        cols = st.columns(5)
        for i, media in enumerate(trending_media):
            with cols[i]:
                display_media_card(media, f"trending_{i}")
    else:
        st.info("Unable to load trending content")
    
    st.markdown("---")
    st.markdown("## 🎬 Popular Movies")
    popular_movies = st.session_state.calculator.get_popular('movie')[:5]
    if popular_movies:
        cols = st.columns(5)
        for i, media in enumerate(popular_movies):
            with cols[i]:
                display_media_card(media, f"pop_movie_{i}")
    else:
        st.info("Unable to load popular movies")
    
    st.markdown("---")
    st.markdown("## 📺 Popular TV Shows")
    popular_tv = st.session_state.calculator.get_popular('tv')[:5]
    if popular_tv:
        cols = st.columns(5)
        for i, media in enumerate(popular_tv):
            with cols[i]:
                display_media_card(media, f"pop_tv_{i}")
    else:
        st.info("Unable to load popular TV shows")

def search_interface():
    """Enhanced search interface with suggestions"""
    st.markdown("---")
    st.markdown("## 🔍 Or Search Directly")
    
    # Search input
    search_query = st.text_input(
        "Enter movie or TV show title:", 
        placeholder="e.g., Breaking Bad, Avengers, Game of Thrones...",
        key="search_input"
    )
    
    # Search suggestions
    if search_query and len(search_query) >= 2:
        with st.spinner("🔍 Finding suggestions..."):
            suggestions = st.session_state.calculator.search_suggestions(search_query)
        
        if suggestions:
            st.markdown("#### 💡 Suggestions:")
            
            for i, suggestion in enumerate(suggestions[:6]):  # Show max 6 suggestions
                col1, col2 = st.columns([1, 4])
                
                with col1:
                    # Display poster if available
                    if suggestion['data'].get('poster_path'):
                        poster_url = f"https://image.tmdb.org/t/p/w185{suggestion['data']['poster_path']}"
                        st.image(poster_url, width=80)
                    else:
                        media_icon = "🎬" if suggestion['data'].get('media_type') == 'movie' else "📺"
                        st.markdown(f"<div style='text-align: center; font-size: 50px;'>{media_icon}</div>", unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"**{suggestion['display']}**")
                    overview = suggestion['data'].get('overview', '')
                    if overview:
                        st.caption(overview[:100] + "..." if len(overview) > 100 else overview)
                    
                    if st.button("Select", key=f"suggestion_{i}", use_container_width=True):
                        st.session_state.selected_result = suggestion['data']
                        st.session_state.search_completed = True
                        st.rerun()
                
                st.markdown("---")
    
    # Direct search button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔍 Search", type="primary", disabled=not search_query):
            with st.spinner(f"🔍 Searching for: {search_query}"):
                result = st.session_state.calculator.search_title(search_query)
            
            if result:
                result['media_type'] = result.get('media_type', 'movie' if 'title' in result else 'tv')
                st.session_state.selected_result = result
                st.session_state.search_completed = True
                st.rerun()
            else:
                st.error("❌ No results found. Please check the title and try again.")

def get_current_progress_movie(total_minutes: int) -> int:
    """Get user's current watching progress for movies"""
    st.markdown("### 🎬 Current Progress Tracker")
    
    time_input_method = st.radio(
        "How would you like to enter your progress?",
        ["Hours and Minutes", "Total Minutes", "Percentage"],
        key="movie_progress_method"
    )
    
    watched_minutes = 0
    
    if time_input_method == "Hours and Minutes":
        col1, col2 = st.columns(2)
        with col1:
            hours = st.number_input("Hours watched", min_value=0, max_value=10, value=0, key="hours_watched")
        with col2:
            minutes = st.number_input("Minutes watched", min_value=0, max_value=59, value=0, key="minutes_watched")
        watched_minutes = int(hours * 60 + minutes)
    
    elif time_input_method == "Total Minutes":
        watched_minutes = st.number_input(
            "Total minutes watched", 
            min_value=0, 
            max_value=total_minutes, 
            value=0,
            key="total_minutes_watched"
        )
    
    else:  # Percentage
        percentage = st.slider("Percentage completed", 0, 100, 0, key="percentage_watched")
        watched_minutes = int((percentage / 100) * total_minutes)
    
    if watched_minutes > total_minutes:
        st.error(f"❌ You can't have watched more than the total runtime ({format_time(total_minutes)})")
        return 0
    
    return watched_minutes

def get_current_progress_tv(tv_details: Dict, season_episodes: List[List[Dict]]) -> int:
    """Get user's current watching progress for TV shows"""
    st.markdown("### 🎬 Current Progress Tracker")
    st.info("Let's track where you are in the show!")
    
    total_seasons = tv_details.get('number_of_seasons', 0)
    
    col1, col2 = st.columns(2)
    
    with col1:
        current_season = st.selectbox(
            "📺 Which season are you currently watching?",
            range(1, total_seasons + 1),
            index=0,
            key="current_season_select"
        )
    
    max_episode = len(season_episodes[current_season - 1]) if current_season <= len(season_episodes) else 1
    
    with col2:
        current_episode = st.selectbox(
            f"📋 Which episode in Season {current_season}?",
            range(1, max_episode + 1),
            index=0,
            key="current_episode_select"
        )
    
    # Calculate watched runtime
    watched_minutes = 0
    
    # Add complete seasons
    for season_idx in range(current_season - 1):
        if season_idx < len(season_episodes):
            for episode in season_episodes[season_idx]:
                watched_minutes += episode.get('runtime', 0)
    
    # Add episodes from current season
    if current_season - 1 < len(season_episodes):
        for ep_idx in range(current_episode - 1):
            if ep_idx < len(season_episodes[current_season - 1]):
                watched_minutes += season_episodes[current_season - 1][ep_idx].get('runtime', 0)
    
    st.success(f"📍 Current Position: Season {current_season}, Episode {current_episode}")
    
    return watched_minutes

def display_progress_summary(watched_minutes: int, total_minutes: int):
    """Display progress summary with gauge chart"""
    remaining_minutes = total_minutes - watched_minutes
    
    st.markdown("### 📊 Progress Summary")
    
    # Progress gauge
    fig = create_progress_gauge(watched_minutes, total_minutes)
    st.plotly_chart(fig, use_container_width=True)
    
    # Progress metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("✅ Watched", format_time(watched_minutes))
    with col2:
        st.metric("⏳ Remaining", format_time(remaining_minutes))
    with col3:
        st.metric("📺 Total", format_time(total_minutes))
    with col4:
        percentage = (watched_minutes / total_minutes) * 100 if total_minutes > 0 else 0
        st.metric("🎯 Progress", f"{percentage:.1f}%")

def calculate_viewing_schedule(total_minutes: int, watched_minutes: int = 0):
    """Calculate and display viewing schedule"""
    remaining_minutes = total_minutes - watched_minutes
    
    st.markdown("### 📅 Viewing Schedule Calculator")
    
    daily_hours = st.slider(
        "⏰ How many hours per day do you plan to watch?",
        min_value=0.5,
        max_value=12.0,
        value=2.0,
        step=0.5,
        format="%.1f hours",
        key="daily_hours_slider"
    )
    
    daily_minutes = daily_hours * 60
    schedule_type = "remaining" if watched_minutes > 0 else "total"
    minutes_to_calculate = remaining_minutes if watched_minutes > 0 else total_minutes
    
    if minutes_to_calculate <= 0:
        st.success("🎉 You've already finished watching!")
        return
    
    days_to_finish = minutes_to_calculate / daily_minutes
    
    st.markdown(f"### 🗓️ Schedule Breakdown ({schedule_type.title()})")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Days", f"{days_to_finish:.1f}")
    
    with col2:
        if days_to_finish >= 7:
            weeks = days_to_finish / 7
            st.metric("📅 Weeks", f"{weeks:.1f}")
        else:
            st.metric("📅 Weeks", "< 1")
    
    with col3:
        if days_to_finish >= 30:
            months = days_to_finish / 30.44
            st.metric("🗓️ Months", f"{months:.1f}")
        else:
            st.metric("🗓️ Months", "< 1")
    
    with col4:
        if days_to_finish >= 365:
            years = days_to_finish / 365.25
            st.metric("📆 Years", f"{years:.1f}")
        else:
            st.metric("📆 Years", "< 1")
    
    # Finish date
    finish_date = datetime.date.today() + datetime.timedelta(days=int(days_to_finish))
    st.info(f"🏁 **Estimated completion date:** {finish_date.strftime('%B %d, %Y')}")
    
    if watched_minutes > 0:
        watch_percentage = (watched_minutes / total_minutes) * 100
        st.success(f"🎊 You're {watch_percentage:.1f}% done!")

def process_movie(calculator: RuntimeCalculator, movie_data: Dict) -> int:
    """Process movie data and return runtime in minutes"""
    with st.spinner("Fetching movie details..."):
        movie_details = calculator.get_movie_details(movie_data['id'])
    
    # Store in session state
    st.session_state.movie_details = movie_details
    
    # Add media_type to details
    movie_details['media_type'] = 'movie'
    
    # Display comprehensive media info
    display_media_showcase(movie_details, 'movie')
    
    runtime = movie_details.get('runtime', 0)
    
    st.markdown("---")
    st.markdown("## ⏱️ Runtime Information")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Runtime", format_time(runtime))
    with col2:
        st.metric("Exact Time", format_detailed_time(runtime))
    with col3:
        st.metric("Minutes", f"{runtime} min")
    
    return runtime

def process_tv_show(calculator: RuntimeCalculator, tv_data: Dict) -> Tuple[int, Dict, List[List[Dict]]]:
    """Process TV show data and return total runtime in minutes, tv_details, and episode data"""
    with st.spinner("Fetching TV show details..."):
        tv_details = calculator.get_tv_details(tv_data['id'])
    
    # Store in session state
    st.session_state.tv_details = tv_details
    
    # Add media_type to details
    tv_details['media_type'] = 'tv'
    
    # Display comprehensive media info
    display_media_showcase(tv_details, 'tv')
    
    seasons = tv_details.get('number_of_seasons', 0)
    total_episodes = tv_details.get('number_of_episodes', 0)
    
    st.markdown("---")
    st.markdown("## 📺 Show Information")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Seasons", seasons)
    with col2:
        st.metric("Total Episodes", total_episodes)
    
    # Check if we already have episode data in session state
    if 'season_episodes' in st.session_state and 'total_runtime' in st.session_state:
        return st.session_state.total_runtime, tv_details, st.session_state.season_episodes
    
    # Fetch episode data
    st.markdown("### 📊 Fetching Episode Runtimes...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_runtime = 0
    episode_count = 0
    season_episodes = []
    season_data_display = []
    
    for season_num in range(1, seasons + 1):
        try:
            progress_bar.progress(season_num / seasons)
            status_text.text(f"Processing Season {season_num}...")
            
            season_data = calculator.get_season_details(tv_data['id'], season_num)
            season_runtime = 0
            episodes = season_data.get('episodes', [])
            season_episodes.append(episodes)
            
            for episode in episodes:
                runtime = episode.get('runtime', 0)
                if runtime:
                    season_runtime += runtime
                    total_runtime += runtime
                episode_count += 1
            
            season_data_display.append({
                'Season': season_num,
                'Episodes': len(episodes),
                'Runtime': format_time(season_runtime),
                'Minutes': season_runtime
            })
            
        except Exception as e:
            season_episodes.append([])
            season_data_display.append({
                'Season': season_num,
                'Episodes': 0,
                'Runtime': "Unable to fetch",
                'Minutes': 0
            })
    
    progress_bar.progress(1.0)
    status_text.text("✅ Complete!")
    
    # Store in session state
    st.session_state.season_episodes = season_episodes
    st.session_state.total_runtime = total_runtime
    st.session_state.season_data_display = season_data_display
    
    # Display season breakdown
    st.markdown("### 📈 Season Breakdown")
    st.dataframe(season_data_display, use_container_width=True)
    
    # Display totals
    st.markdown("### 📊 Total Runtime Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Episodes", episode_count)
    with col2:
        st.metric("Total Runtime", format_time(total_runtime))
    with col3:
        st.metric("Exact Time", format_detailed_time(total_runtime))
    
    return total_runtime, tv_details, season_episodes

def display_watchlist():
    """Display the user's enhanced watchlist with custom addition feature"""
    st.markdown("## 📋 My Watchlist")
    
    WatchlistManager.initialize_watchlist()
    
    # Add custom item section
    with st.expander("➕ Add Custom Movie/Show", expanded=False):
        st.markdown("### Add anything you want to your watchlist!")
        
        col1, col2 = st.columns(2)
        with col1:
            custom_title = st.text_input("Title", placeholder="e.g., The Godfather", key="custom_title")
            custom_year = st.text_input("Year (optional)", placeholder="e.g., 1972", key="custom_year")
        
        with col2:
            custom_type = st.selectbox("Type", ["movie", "tv"], format_func=lambda x: "🎬 Movie" if x == "movie" else "📺 TV Show", key="custom_type")
            custom_list = st.selectbox("Add to", ["want_to_watch", "watching"], format_func=lambda x: "⭐ Want to Watch" if x == "want_to_watch" else "📺 Currently Watching", key="custom_list")
        
        custom_notes = st.text_area("Notes (optional)", placeholder="Any additional notes about this title...", key="custom_notes")
        
        if st.button("➕ Add to Watchlist", type="primary", key="add_custom"):
            if custom_title.strip():
                WatchlistManager.add_custom_item(
                    title=custom_title.strip(),
                    media_type=custom_type,
                    list_type=custom_list,
                    year=custom_year.strip(),
                    notes=custom_notes.strip()
                )
                st.success(f"Added '{custom_title}' to your watchlist!")
                st.rerun()
            else:
                st.error("Please enter a title!")
    
    tab1, tab2 = st.tabs(["📺 Currently Watching", "⭐ Want to Watch"])
    
    def render_watchlist(watchlist: List[Dict], list_type: str):
        """Render a watchlist section"""
        if not watchlist:
            st.info(f"Your '{list_type.replace('_', ' ')}' list is empty.")
            return
        
        st.markdown(f"### {len(watchlist)} items in your list")
        
        for i, item in enumerate(watchlist):
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                if item.get('poster_path'):
                    poster_url = f"https://image.tmdb.org/t/p/w185{item['poster_path']}"
                    st.image(poster_url, width=80)
                else:
                    icon = "🎬" if item['media_type'] == 'movie' else "📺"
                    st.markdown(f"<div style='text-align: center; font-size: 50px;'>{icon}</div>", unsafe_allow_html=True)
            
            with col2:
                # Title with language indicator
                title_display = item['title']
                if item.get('original_title') and item['original_title'] != item['title']:
                    title_display = f"{item['title']} ({item['original_title']})"
                
                media_icon = "🎬" if item['media_type'] == 'movie' else "📺"
                lang_indicator = f" 🌐{item.get('language', '')}" if item.get('language') and item.get('language') not in ['EN', 'CUSTOM'] else ""
                custom_indicator = " 🔧" if item.get('is_custom') else ""
                
                st.markdown(f"**{media_icon} {title_display} ({item.get('year', 'N/A')})**{lang_indicator}{custom_indicator}")
                st.caption(f"Added: {item['added_date']}")
                
                # Show notes for custom items
                if item.get('notes'):
                    st.caption(f"📝 {item['notes']}")
            
            with col3:
                if st.button("❌", key=f"remove_{list_type}_{i}", help="Remove from list"):
                    WatchlistManager.remove_from_watchlist(item['id'], list_type)
                    st.rerun()
            
            st.divider()
    
    with tab1:
        render_watchlist(st.session_state.watchlist_watching, 'watching')
    
    with tab2:
        render_watchlist(st.session_state.watchlist_want_to_watch, 'want_to_watch')

def main():
    """Main Streamlit application with all merged features"""
    # Page configuration
    st.set_page_config(
        page_title="🎬 Ultimate Runtime Calculator",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    if 'calculator' not in st.session_state:
        st.session_state.calculator = RuntimeCalculator(API_KEY, ACCESS_TOKEN)
    if 'search_completed' not in st.session_state:
        st.session_state.search_completed = False
    if 'selected_result' not in st.session_state:
        st.session_state.selected_result = None
    
    # Initialize watchlist
    WatchlistManager.initialize_watchlist()
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("# 🎬 Navigation")
        page = st.radio(
            "Choose a page:",
            ["🏠 Home & Discover", "📋 My Watchlist"],
            key="navigation"
        )
        
        st.markdown("---")
        st.markdown("### 🎯 Features")
        st.info("• Calculate total runtimes\n• Track viewing progress\n• Plan viewing schedules\n• Manage watchlists\n• Discover trending content")
        
        # Watchlist summary
        total_watching = len(st.session_state.watchlist_watching)
        total_want_to_watch = len(st.session_state.watchlist_want_to_watch)
        
        if total_watching > 0 or total_want_to_watch > 0:
            st.markdown("### 📊 Your Lists")
            if total_watching > 0:
                st.metric("📺 Currently Watching", total_watching)
            if total_want_to_watch > 0:
                st.metric("⭐ Want to Watch", total_want_to_watch)
    
    # Header
    st.markdown("""
    <div style='text-align: center;'>
        <h1>🎬 Ultimate Movie & TV Show Runtime Calculator</h1>
        <p style='font-size: 1.2em; color: #666;'>Discover, calculate, and plan your entertainment journey!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Handle page navigation
    if page == "📋 My Watchlist":
        display_watchlist()
        return
    
    # Main content area
    if st.session_state.search_completed and st.session_state.selected_result:
        # Back button
        if st.button("← Back to Home / New Search", key="back_button"):
            # Clear session state
            for key in ['search_completed', 'selected_result', 'movie_details', 'tv_details', 
                       'season_episodes', 'total_runtime', 'season_data_display']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        result = st.session_state.selected_result
        media_type = result.get('media_type')
        found_title = result.get('title') or result.get('name')
        
        st.success(f"✅ Found: **{found_title}** ({media_type})")
        
        # Process based on media type
        if media_type == 'movie':
            total_minutes = process_movie(st.session_state.calculator, result)
            watched_minutes = 0
            
            # Check if started watching
            started = st.checkbox("🎬 I've already started watching this movie", key="started_movie")
            
            if started:
                watched_minutes = get_current_progress_movie(total_minutes)
                if watched_minutes > 0:
                    display_progress_summary(watched_minutes, total_minutes)
        
        elif media_type == 'tv':
            total_minutes, tv_details, season_episodes = process_tv_show(st.session_state.calculator, result)
            watched_minutes = 0
            
            # Check if started watching
            started = st.checkbox("📺 I've already started watching this show", key="started_tv")
            
            if started:
                watched_minutes = get_current_progress_tv(tv_details, season_episodes)
                if watched_minutes > 0:
                    display_progress_summary(watched_minutes, total_minutes)
        
        else:
            st.error("❌ Unsupported media type.")
            return
        
        # Viewing schedule
        st.markdown("---")
        schedule_help = st.checkbox("📅 Help me plan my viewing schedule", value=True, key="schedule_checkbox")
        
        if schedule_help:
            calculate_viewing_schedule(total_minutes, watched_minutes)
    
    else:
        # Homepage with discovery and search
        display_homepage()
        search_interface()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>Made by ✨Anvi Karanjkar✨</p>
        <p><em>Discover • Calculate • Track • Plan</em></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
    # To run: streamlit run runtime_streamlit.py
