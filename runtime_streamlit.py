import streamlit as st
import requests
from datetime import date, timedelta

# --- TMDB Config ---
API_KEY = "47aa3b4def8767b97ea958e92b233aec"
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0N2FhM2I0ZGVmODc2N2I5N2VhOTU4ZTkyYjIzM2FlYyIsIm5iZiI6MTc1MzU4NTA3MS4yMjIwMDAxLCJzdWIiOiI2ODg1OTVhZmZiNDE4YjFhYzEzOGY2YTciLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.6dfVkYzjkrLLh7072uq-iMe8D2FoPeFCiZXKtfGVrCI"
BASE_URL = "https://api.themoviedb.org/3"
HEADERS = {
    "accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

def search_title(query):
    url = f"{BASE_URL}/search/multi"
    params = {"query": query, "language": "en-US"}
    try:
        res = requests.get(url, headers=HEADERS, params=params)
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        st.error(f"API request failed: {e}")
        return None

    if data.get("results") and len(data["results"]) > 0:
        return data["results"][0]
    else:
        return None

def get_movie_runtime(movie_id):
    url = f"{BASE_URL}/movie/{movie_id}"
    try:
        res = requests.get(url, headers=HEADERS)
        res.raise_for_status()
        data = res.json()
        return data.get("runtime", 0), data.get("title", "Unknown")
    except Exception as e:
        st.error(f"Failed to get movie details: {e}")
        return 0, "Unknown"

def get_tv_details(tv_id):
    # Get show details
    try:
        details_res = requests.get(f"{BASE_URL}/tv/{tv_id}", headers=HEADERS)
        details_res.raise_for_status()
        details = details_res.json()
    except Exception as e:
        st.error(f"Failed to get TV show details: {e}")
        return None

    # Fetch season and episode runtimes
    seasons = details.get("seasons", [])
    all_seasons_data = []
    total_runtime = 0

    for season in seasons:
        season_num = season.get("season_number")
        if season_num is None:
            continue
        try:
            season_res = requests.get(f"{BASE_URL}/tv/{tv_id}/season/{season_num}", headers=HEADERS)
            season_res.raise_for_status()
            season_data = season_res.json()
            episodes = season_data.get("episodes", [])
            for ep in episodes:
                ep_runtime = ep.get("runtime") or 0
                total_runtime += ep_runtime
            all_seasons_data.append({
                "season_number": season_num,
                "episodes": episodes,
            })
        except Exception as e:
            st.warning(f"Could not fetch season {season_num} details: {e}")

    return details, all_seasons_data, total_runtime

def format_time(minutes):
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"

def calculate_remaining_runtime(seasons_data, current_season, current_episode):
    """Calculate total remaining runtime from current position."""
    remaining = 0
    for season in seasons_data:
        season_num = season["season_number"]
        episodes = season["episodes"]

        if season_num < current_season:
            continue
        for ep in episodes:
            ep_num = ep.get("episode_number")
            ep_runtime = ep.get("runtime") or 0

            if season_num == current_season and ep_num < current_episode:
                continue  # Already watched
            remaining += ep_runtime
    return remaining

st.title("🎬 Movie & TV Show Runtime Calculator")

query = st.text_input("Enter a movie or TV show title:")

if query:
    with st.spinner("Searching..."):
        result = search_title(query)

    if not result:
        st.error("No results found for that title.")
        st.stop()

    media_type = result.get("media_type")
    if media_type == "movie":
        runtime, title = get_movie_runtime(result["id"])
        st.subheader(f"Title: {title}")
        st.write(f"Total Runtime: **{format_time(runtime)}** ({runtime} minutes)")

        daily_hours = st.number_input("How many hours per day do you plan to watch?", min_value=0.1, step=0.1, format="%.1f")

        if daily_hours:
            days_to_finish = runtime / (daily_hours * 60)
            finish_date = date.today() + timedelta(days=int(days_to_finish))

            st.markdown("### 📅 Viewing Schedule")
            st.write(f"Days to finish: **{days_to_finish:.1f}** days")
            st.write(f"Weeks: ~{days_to_finish/7:.1f}")
            st.write(f"Months: ~{days_to_finish/30.44:.1f}")
            st.write(f"Estimated finish date: **{finish_date.strftime('%B %d, %Y')}**")

    elif media_type == "tv":
        details, seasons_data, total_runtime = get_tv_details(result["id"])
        if details is None:
            st.error("Could not retrieve TV show details.")
            st.stop()

        title = details.get("name", "Unknown")
        num_seasons = details.get("number_of_seasons", 0)
        num_episodes = details.get("number_of_episodes", 0)

        st.subheader(f"Title: {title}")
        st.write(f"Seasons: {num_seasons}")
        st.write(f"Total Episodes: {num_episodes}")
        st.write(f"Total Runtime: **{format_time(total_runtime)}** ({total_runtime} minutes)")

        st.markdown("---")
        st.write("### Where are you up to?")
        current_season = st.number_input("Current Season", min_value=1, max_value=num_seasons, step=1, value=1)
        # Find max episodes in current season to limit episode input
        max_episodes_current_season = 0
        for season in seasons_data:
            if season["season_number"] == current_season:
                max_episodes_current_season = len(season["episodes"])
                break
        current_episode = st.number_input("Current Episode", min_value=1, max_value=max_episodes_current_season or 1, step=1, value=1)

        daily_hours = st.number_input("How many hours per day do you plan to watch?", min_value=0.1, step=0.1, format="%.1f")

        if daily_hours:
            remaining_runtime = calculate_remaining_runtime(seasons_data, current_season, current_episode)
            days_to_finish = remaining_runtime / (daily_hours * 60) if daily_hours > 0 else 0
            finish_date = date.today() + timedelta(days=int(days_to_finish))

            st.markdown("### 📅 Viewing Schedule")
            st.write(f"Remaining Runtime: **{format_time(remaining_runtime)}** ({remaining_runtime} minutes)")
            st.write(f"Days to finish: **{days_to_finish:.1f}** days")
            st.write(f"Weeks: ~{days_to_finish/7:.1f}")
            st.write(f"Months: ~{days_to_finish/30.44:.1f}")
            st.write(f"Estimated finish date: **{finish_date.strftime('%B %d, %Y')}**")

    else:
        st.error(f"Unsupported media type: {media_type}")
