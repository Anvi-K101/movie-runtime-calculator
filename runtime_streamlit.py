#!/usr/bin/env python3
"""
🎬 Movie & TV Show Runtime Calculator - Streamlit Web App
Fetches detailed runtime information and helps with viewing schedules
"""

import streamlit as st
import requests
import datetime
from typing import Dict, List, Tuple, Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# TMDb API Configuration
API_KEY = "47aa3b4def8767b97ea958e92b233aec"
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0N2FhM2I0ZGVmODc2N2I5N2VhOTU4ZTkyYjIzM2FlYyIsIm5iZiI6MTc1MzU4NTA3MS4yMjIwMDAxLCJzdWIiOiI2ODg1OTVhZmZiNDE4YjFhYzEzOGY2YTciLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.6dfVkYzjkrLLh7072uq-iMe8D2FoPeFCiZXKtfGVrCI"
BASE_URL = "https://api.themoviedb.org/3"

class RuntimeCalculator:
    def __init__(self, api_key: str, access_token: str):
        self.api_key = api_key
        self.access_token = access_token
        self.headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
    
    def search_suggestions(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for movies and TV shows with suggestions"""
        if len(query) < 2:
            return []
        
        url = f"{BASE_URL}/search/multi"
        params = {
            "query": query,
            "language": "en-US",
            "page": 1
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            # Filter and format results
            results = []
            for item in data.get('results', [])[:limit]:
                if item.get('media_type') in ['movie', 'tv']:
                    title = item.get('title') or item.get('name', 'Unknown')
                    year = ''
                    if item.get('release_date'):
                        year = f" ({item['release_date'][:4]})"
                    elif item.get('first_air_date'):
                        year = f" ({item['first_air_date'][:4]})"
                    
                    media_icon = "🎬" if item.get('media_type') == 'movie' else "📺"
                    
                    results.append({
                        'display': f"{media_icon} {title}{year}",
                        'title': title,
                        'data': item
                    })
            
            return results
        except requests.RequestException:
            return []
    
    def search_title(self, query: str) -> Optional[Dict]:
        """Search for a specific movie or TV show"""
        url = f"{BASE_URL}/search/multi"
        params = {
            "query": query,
            "language": "en-US"
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            if data['results']:
                return data['results'][0]
            return None
        except requests.RequestException:
            return None
    
    def get_movie_details(self, movie_id: int) -> Dict:
        """Get detailed movie information including runtime"""
        url = f"{BASE_URL}/movie/{movie_id}"
        params = {"language": "en-US"}
        
        response = requests.get(url, params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_tv_details(self, tv_id: int) -> Dict:
        """Get detailed TV show information"""
        url = f"{BASE_URL}/tv/{tv_id}"
        params = {"language": "en-US"}
        
        response = requests.get(url, params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_season_details(self, tv_id: int, season_number: int) -> Dict:
        """Get detailed season information including episode runtimes"""
        url = f"{BASE_URL}/tv/{tv_id}/season/{season_number}"
        params = {"language": "en-US"}
        
        response = requests.get(url, params=params, headers=self.headers)
        response.raise_for_status()
        return response.json()

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
        sentiment = "🌟 Exceptional"
        description = "Critically acclaimed masterpiece"
        color = "#FFD700"
    elif rating >= 7.5:
        sentiment = "⭐ Excellent"
        description = "Highly recommended viewing"
        color = "#32CD32"
    elif rating >= 6.5:
        sentiment = "👍 Good"
        description = "Solid entertainment value"
        color = "#87CEEB"
    elif rating >= 5.5:
        sentiment = "👌 Average"
        description = "Mixed but watchable"
        color = "#FFA500"
    elif rating >= 4.0:
        sentiment = "👎 Below Average"
        description = "Has some issues"
        color = "#FF6347"
    else:
        sentiment = "💔 Poor"
        description = "Generally not recommended"
        color = "#DC143C"
    
    return sentiment, description, color

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
    """Display comprehensive media information with poster and summary"""
    col1, col2 = st.columns([1, 2])
    
    if media_type == 'movie':
        title = media_data.get('title', 'Unknown')
        year = media_data.get('release_date', '')[:4] if media_data.get('release_date') else 'Unknown'
        genres = [genre['name'] for genre in media_data.get('genres', [])]
    else:  # TV show
        title = media_data.get('name', 'Unknown')
        year = media_data.get('first_air_date', '')[:4] if media_data.get('first_air_date') else 'Unknown'
        genres = [genre['name'] for genre in media_data.get('genres', [])]
    
    overview = media_data.get('overview', 'No summary available.')
    rating = media_data.get('vote_average', 0)
    vote_count = media_data.get('vote_count', 0)
    poster_path = media_data.get('poster_path', '')
    
    # Display poster
    with col1:
        if poster_path:
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            st.image(poster_url, caption=f"{title} Poster", use_column_width=True)
        else:
            st.info("📽️ No poster available")
    
    # Display information
    with col2:
        st.markdown(f"# 🎬 {title} ({year})")
        
        if genres:
            genre_badges = " ".join([f"`{genre}`" for genre in genres])
            st.markdown(f"**🎭 Genres:** {genre_badges}")
        
        # Rating display
        sentiment, description, color = get_review_summary(rating, vote_count)
        st.markdown(f"**⭐ Rating:** {sentiment} ({rating:.1f}/10)")
        st.markdown(f"*{description}*")
        st.caption(f"Based on {vote_count:,} user ratings")
        
        # Summary
        st.markdown("### 📝 Summary")
        st.write(overview)

def process_movie(calculator: RuntimeCalculator, movie_data: Dict) -> int:
    """Process movie data and return runtime in minutes"""
    with st.spinner("Fetching movie details..."):
        movie_details = calculator.get_movie_details(movie_data['id'])
    
    # Store in session state
    st.session_state.movie_details = movie_details
    
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
            
        except requests.RequestException:
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

def search_interface():
    """Handle the search interface with suggestions"""
    st.markdown("## 🔍 Search for a Movie or TV Show")
    
    # Initialize calculator
    if 'calculator' not in st.session_state:
        st.session_state.calculator = RuntimeCalculator(API_KEY, ACCESS_TOKEN)
    
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
            
            # Create columns for suggestions
            cols = st.columns(min(3, len(suggestions)))
            
            for i, suggestion in enumerate(suggestions[:6]):  # Show max 6 suggestions
                col_idx = i % 3
                with cols[col_idx]:
                    if st.button(
                        suggestion['display'], 
                        key=f"suggestion_{i}",
                        use_container_width=True
                    ):
                        st.session_state.selected_result = suggestion['data']
                        st.session_state.search_completed = True
                        st.rerun()
    
    # Direct search button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔍 Search", type="primary", disabled=not search_query):
            with st.spinner(f"🔍 Searching for: {search_query}"):
                result = st.session_state.calculator.search_title(search_query)
            
            if result:
                st.session_state.selected_result = result
                st.session_state.search_completed = True
                st.rerun()
            else:
                st.error("❌ No results found. Please check the title and try again.")

def main():
    """Main Streamlit application"""
    # Page configuration
    st.set_page_config(
        page_title="🎬 Runtime Calculator",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize session state
    if 'search_completed' not in st.session_state:
        st.session_state.search_completed = False
    if 'selected_result' not in st.session_state:
        st.session_state.selected_result = None
    
    # Header
    st.markdown("""
    # 🎬 Movie & TV Show Runtime Calculator
    
    ### Get detailed runtime information and plan your viewing schedule!
    """)
    
    # Search interface
    if not st.session_state.search_completed:
        search_interface()
        return
    
    # Process selected result
    result = st.session_state.selected_result
    if not result:
        st.error("❌ No result to process.")
        return
    
    media_type = result.get('media_type')
    found_title = result.get('title') or result.get('name')
    
    # Back button
    if st.button("← Search Again", key="back_button"):
        # Clear session state
        for key in ['search_completed', 'selected_result', 'movie_details', 'tv_details', 
                   'season_episodes', 'total_runtime', 'season_data_display']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
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
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        Made with ❤️ using Streamlit and TMDb API
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
    #streamlit run runtimeradar.py 
