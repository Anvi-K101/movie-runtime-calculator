import requests
import datetime
from typing import Dict, List, Tuple, Optional

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
    
    def search_title(self, query: str) -> Optional[Dict]:
        """Search for a movie or TV show"""
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
                return data['results'][0]  # Return first result
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
    """Convert minutes to HH:MM:SS format"""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}h {mins:02d}m"

def format_detailed_time(total_minutes: int) -> str:
    """Convert minutes to detailed HH:MM:SS format"""
    hours = total_minutes // 60
    minutes = total_minutes % 60
    seconds = 0  # TMDb provides runtime in minutes
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def print_box(text: str, width: int = 60):
    """Print text in a decorative box"""
    print("┌" + "─" * (width - 2) + "┐")
    lines = text.split('\n')
    for line in lines:
        padding = width - len(line) - 4
        print(f"│ {line}{' ' * padding} │")
    print("└" + "─" * (width - 2) + "┘")

def print_header():
    """Print the program header"""
    header = """🎬 MOVIE & TV SHOW RUNTIME CALCULATOR 🎬
Enter any movie or TV show title to get detailed
runtime information and viewing schedule help!"""
    print_box(header, 70)
    print()

def process_movie(calculator: RuntimeCalculator, movie_data: Dict) -> int:
    """Process movie data and return runtime in minutes"""
    movie_details = calculator.get_movie_details(movie_data['id'])
    
    title = movie_details.get('title', 'Unknown')
    year = movie_details.get('release_date', '')[:4] if movie_details.get('release_date') else 'Unknown'
    runtime = movie_details.get('runtime', 0)
    
    print("🎥 MOVIE DETAILS")
    print("=" * 50)
    print(f"📽️  Title: {title} ({year})")
    print(f"⏱️  Runtime: {format_time(runtime)}")
    print(f"🕐 Exact Runtime: {format_detailed_time(runtime)}")
    print()
    
    return runtime

def process_tv_show(calculator: RuntimeCalculator, tv_data: Dict) -> int:
    """Process TV show data and return total runtime in minutes"""
    tv_details = calculator.get_tv_details(tv_data['id'])
    
    title = tv_details.get('name', 'Unknown')
    first_air_date = tv_details.get('first_air_date', '')[:4] if tv_details.get('first_air_date') else 'Unknown'
    seasons = tv_details.get('number_of_seasons', 0)
    total_episodes = tv_details.get('number_of_episodes', 0)
    
    print("📺 TV SHOW DETAILS")
    print("=" * 50)
    print(f"📺 Title: {title} ({first_air_date})")
    print(f"🎭 Seasons: {seasons}")
    print(f"📋 Total Episodes: {total_episodes}")
    print()
    
    print("📊 Fetching episode runtimes...")
    total_runtime = 0
    episode_count = 0
    
    # Get runtime for each season
    for season_num in range(1, seasons + 1):
        try:
            season_data = calculator.get_season_details(tv_data['id'], season_num)
            season_runtime = 0
            season_episodes = len(season_data.get('episodes', []))
            
            for episode in season_data.get('episodes', []):
                runtime = episode.get('runtime', 0)
                if runtime:  # Some episodes might not have runtime data
                    season_runtime += runtime
                    total_runtime += runtime
                episode_count += 1
            
            print(f"   Season {season_num}: {season_episodes} episodes, {format_time(season_runtime)}")
            
        except requests.RequestException:
            print(f"   Season {season_num}: Unable to fetch data")
    
    print()
    print("📈 TOTAL RUNTIME SUMMARY")
    print("=" * 50)
    print(f"🎯 Total Episodes Processed: {episode_count}")
    print(f"⏱️  Total Runtime: {format_time(total_runtime)}")
    print(f"🕐 Exact Total Runtime: {format_detailed_time(total_runtime)}")
    print()
    
    return total_runtime

def calculate_viewing_schedule(total_minutes: int):
    """Calculate and display viewing schedule based on daily hours"""
    print("📅 VIEWING SCHEDULE CALCULATOR")
    print("=" * 50)
    
    while True:
        try:
            daily_hours = float(input("⏰ How many hours per day do you plan to watch? "))
            if daily_hours <= 0:
                print("❌ Please enter a positive number of hours.")
                continue
            break
        except ValueError:
            print("❌ Please enter a valid number.")
    
    daily_minutes = daily_hours * 60
    days_to_finish = total_minutes / daily_minutes
    
    print()
    print("🗓️  SCHEDULE BREAKDOWN")
    print("=" * 30)
    print(f"📊 Days to finish: {days_to_finish:.1f} days")
    
    if days_to_finish >= 7:
        weeks = days_to_finish / 7
        print(f"📅 Approximately: {weeks:.1f} weeks")
    
    if days_to_finish >= 30:
        months = days_to_finish / 30.44  # Average days per month
        print(f"🗓️  Approximately: {months:.1f} months")
    
    if days_to_finish >= 365:
        years = days_to_finish / 365.25  # Account for leap years
        print(f"📆 Approximately: {years:.1f} years")
    
    # Calculate finish date
    finish_date = datetime.date.today() + datetime.timedelta(days=int(days_to_finish))
    print(f"🏁 Estimated completion date: {finish_date.strftime('%B %d, %Y')}")

def main():
    """Main program function"""
    print_header()
    
    # Initialize calculator with your TMDb credentials
    calculator = RuntimeCalculator(API_KEY, ACCESS_TOKEN)
    
    # Get user input
    title = input("🔍 Enter movie/TV show title: ")
    print(f"\n🔍 Searching for: {title}")
    print("=" * 50)
    
    # Search for the title
    result = calculator.search_title(title)
    
    if not result:
        print("❌ No results found. Please check the title and try again.")
        return
    
    media_type = result.get('media_type')
    print(f"✅ Found: {result.get('title') or result.get('name')} ({media_type})")
    print()
    
    # Process based on media type
    if media_type == 'movie':
        total_minutes = process_movie(calculator, result)
    elif media_type == 'tv':
        total_minutes = process_tv_show(calculator, result)
    else:
        print("❌ Unsupported media type.")
        return
    
    # Ask about scheduling
    schedule_help = input("📅 Would you like help scheduling how long it'll take to finish? (y/n): ").lower()
    
    if schedule_help in ['y', 'yes']:
        print()
        calculate_viewing_schedule(total_minutes)
    
    print()
    print_box("Thanks for using the Runtime Calculator! 🎬", 50)

if __name__ == "__main__":
    main()
#Add progress 
#Add how many episodes
#Star cast w character name
#