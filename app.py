from flask import Flask, redirect, request, session, url_for, render_template
from dotenv import load_dotenv
import os
import requests
import base64
import json

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Spotify API credentials from .env file
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')

# Spotify API URLs
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_URL = "https://api.spotify.com/v1"
SCOPE = "user-read-private user-read-email user-top-read"

# Function to generate Spotify authorization URL
def get_spotify_auth_url():
    return f"{SPOTIFY_AUTH_URL}?response_type=code&client_id={SPOTIFY_CLIENT_ID}&scope={SCOPE}&redirect_uri={SPOTIFY_REDIRECT_URI}"

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Login route
@app.route('/login')
def login():
    auth_url = get_spotify_auth_url()
    return redirect(auth_url)

# Callback route
@app.route('/callback')
def callback():
    auth_token = request.args.get('code')
    if auth_token is None:
        return "Error: Missing authorization code."
    try:
        auth_header = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode('ascii')
    except requests.exceptions.JSONDecodeError:
        auth_header = None
    auth_payload = {
        "grant_type": "authorization_code",
        "code": auth_token,
        "redirect_uri": SPOTIFY_REDIRECT_URI
    }
    auth_headers = {"Authorization": f"Basic {auth_header}"}

    auth_response = requests.post(SPOTIFY_TOKEN_URL, data=auth_payload, headers=auth_headers)
    auth_response_data = auth_response.json()

    if 'error' in auth_response_data:
        return f"Error: {auth_response_data['error']} - {auth_response_data.get('error_description', 'No description')}"

    session['token'] = auth_response_data['access_token']
    return redirect(url_for('profile'))

# Profile route
# Profile route
@app.route('/profile')
def profile():
    token = session.get('token')
    if token is None:
        return redirect(url_for('login'))

    # Headers for authenticated requests
    profile_headers = {"Authorization": f"Bearer {token}"}
    
    # Fetching user profile
    profile_response = requests.get(f"{SPOTIFY_API_URL}/me", headers=profile_headers)
    if profile_response.status_code != 200:
        return f"Error fetching profile: {profile_response.json().get('error', 'Unknown error')}"
    profile_data = profile_response.json()

    # Fetching user's top tracks
    top_tracks_response = requests.get(f"{SPOTIFY_API_URL}/me/top/tracks?time_range=short_term&limit=50", headers=profile_headers)
    if top_tracks_response.status_code != 200:
        return f"Error fetching top tracks: {top_tracks_response.json().get('error', 'Unknown error')}"
    top_tracks = top_tracks_response.json()

    # Extract artist IDs from the top tracks
    artist_ids = set()
    for track in top_tracks.get('items', []):
        for artist in track.get('artists', []):
            artist_ids.add(artist.get('id'))

    # Fetch artist details for each artist ID
    artist_details = []
    for artist_id in artist_ids:
        artist_response = requests.get(f"{SPOTIFY_API_URL}/artists/{artist_id}", headers=profile_headers)
        if artist_response.status_code == 200:
            artist_details.append(artist_response.json())
        else:
            print(f"Error fetching artist details for ID {artist_id}: {artist_response.json().get('error', 'Unknown error')}")

    # Create a dictionary to map artist ID to their details
    artist_map = {artist['id']: artist for artist in artist_details}

    comments = []
    track_info_with_comments = []

    # Prepare artist info with popularity and genres
    for track in top_tracks.get('items', []):
        track_comments = []
        for artist in track.get('artists', []):
            artist_id = artist.get('id')
            artist_detail = artist_map.get(artist_id, {})
            artist['popularity'] = artist_detail.get('popularity', 'N/A')
            artist['genres'] = artist_detail.get('genres', [])
        
        # Generate a comment based on the artist's popularity and genres
        # Default comments based on popularity
        if artist['popularity'] < 50:
            track_comments.append("Guess you’re not making it big anytime soon.")
        elif artist['popularity'] > 85:
            track_comments.append("Must be hard being the center of attention. Try harder to be interesting.")

        # Genre-specific comments

        elif "grunge" in artist['genres']:
            track_comments.append("Steady on Kurt")
        elif "palm desert scene" in artist['genres']:
            track_comments.append("Desert rock? More like deserted from good taste.")
        elif "stoner metal" in artist['genres']:
            track_comments.append("Heavy and slow? More like lazy and boring.")
        elif "stoner rock" in artist['genres']:
            track_comments.append("Congratulations, you've mastered the art of being forgettable.")
        elif "british invasion" in artist['genres']:
            track_comments.append("A nostalgia trip that's more annoying than charming.")
        elif "classic rock" in artist['genres']:
            track_comments.append("Classic rock? More like classicly overplayed.")
        elif "merseybeat" in artist['genres']:
            track_comments.append("Trying to relive the Beatles' glory days, huh? Give it up already.")
        elif "psychedelic rock" in artist['genres']:
            track_comments.append("Still tripping on the '60s? Your time machine is broken.")
        elif "indie rock" in artist['genres']:
            track_comments.append("Indie rock: because being obscure is cooler than being good.")
        elif "indietronica" in artist['genres']:
            track_comments.append("Electronic indie? Sounds like a desperate attempt to be different.")
        elif "irish rock" in artist['genres']:
            track_comments.append("If this is what you call 'rock,' I'm not impressed.")
        elif "alternative metal" in artist['genres']:
            track_comments.append("Screaming into a mic doesn't make you deep—just obnoxious.")
        elif "alternative rock" in artist['genres']:
            track_comments.append("Another band trying too hard to be different. How original.")
        elif "modern alternative rock" in artist['genres']:
            track_comments.append("Alternative but still painfully mainstream. Nice try.")
        elif "album rock" in artist['genres']:
            track_comments.append("Long-winded tracks for people who have nothing better to do.")
        elif "hard rock" in artist['genres']:
            track_comments.append("Just more noise for people who can't handle subtlety.")
        elif "alternative pop rock" in artist['genres']:
            track_comments.append("Pop rock with a desperate attempt to sound 'alternative.'")
        elif "punk blues" in artist['genres']:
            track_comments.append("Bluesy punk—sounds like a mess, and it probably is.")
        elif "funk metal" in artist['genres']:
            track_comments.append("Funky metal? Sounds like a midlife crisis in musical form.")
        elif "funk rock" in artist['genres']:
            track_comments.append("Rocking out with funk? Your genre identity crisis is showing.")
        elif "permanent wave" in artist['genres']:
            track_comments.append("A genre name that sounds like it’s permanently stuck in the past.")
        elif "post-grunge" in artist['genres'] or artist["name"] == "Wunderhorse":
            track_comments.append("Grunge's failed sequel. Try harder next time.")
        elif "supergroup" in artist['genres']:
            track_comments.append("When big names come together to make something mediocre.")
        elif "birmingham metal" in artist['genres']:
            track_comments.append("Birmingham metal? More like Birmingham's attempt at being metal.")
        elif "uk doom metal" in artist['genres']:
            track_comments.append("Doom metal from the UK? A gloomy reminder of what music could be.")
        elif "australian hip hop" in artist['genres']:
            track_comments.append("Aussie hip hop? Cute, but not nearly as good as you think.")
        elif "australian underground hip hop" in artist['genres']:
            track_comments.append("Underground Aussie hip hop? More like underground for a reason.")
        elif "modern rock" in artist['genres']:
            track_comments.append("Modern rock: because blandness is apparently a genre now.")
        elif "stomp pop" in artist['genres']:
            track_comments.append("Pop with a stomping beat—just what the world didn't need.")
        elif "welsh rock" in artist['genres']:
            track_comments.append("Welsh rock? A quirky experiment gone wrong.")
        elif "candy pop" in artist['genres']:
            track_comments.append("Sugar-coated pop that's too sweet to be taken seriously.")
        elif "pop emo" in artist['genres']:
            track_comments.append("Emo pop? All the angst, none of the substance.")
        elif "pop punk" in artist['genres']:
            track_comments.append("Punk for people who want to look rebellious but aren’t.")
        elif "pov: indie" in artist['genres']:
            track_comments.append("Indie perspective? More like 'please don’t listen to me.'")
        elif "garage punk" in artist['genres']:
            track_comments.append("Garage punk: raw but not in a good way.")
        elif "australian underground hip hop" in artist['genres']:
            track_comments.append("Underground beats from Australia, hiding for a reason.")
        elif "alternative dance" in artist['genres']:
            track_comments.append("Alternative dance: because regular dance is too mainstream.")
        elif "modern rock" in artist['genres']:
            track_comments.append("Rock's not dead, but this is as close as it gets.")
        elif "neo-synthpop" in artist['genres']:
            track_comments.append("Synthpop with pretentious new-age nonsense.")
        elif "oxford indie" in artist['genres']:
            track_comments.append("Indie from Oxford—it's as dull as it sounds.")
        elif "shimmer pop" in artist['genres']:
            track_comments.append("Pop that tries to shine but ends up just being tacky.")
        elif "electropop" in artist['genres']:
            track_comments.append("Electronic pop: because your taste in music is a mystery.")
        elif "chillwave" in artist['genres']:
            track_comments.append("Chillwave? More like 'chill and forgettable.'")
        elif "downtempo" in artist['genres']:
            track_comments.append("Slow beats for people who need a nap.")
        elif "trip hop" in artist['genres']:
            track_comments.append("Trip hop: a fancy way of saying ‘I’m too cool for upbeat music.’")
        elif "swedish electropop" in artist['genres']:
            track_comments.append("Swedish electropop—because your musical tastes are both foreign and boring.")
        elif "swedish synthpop" in artist['genres']:
            track_comments.append("Synthpop from Sweden? That's a global disappointment.")
        elif "indie soul" in artist['genres']:
            track_comments.append("Soulful indie? Just more indie nonsense dressed up.")
        elif "modern alternative pop" in artist['genres']:
            track_comments.append("Modern alternative pop—trying too hard to be different.")
        elif "garage rock" in artist['genres']:
            track_comments.append("Garage rock: raw and unrefined, just like your taste.")
        elif "melbourne punk" in artist['genres']:
            track_comments.append("Punk from Melbourne? It's as loud and annoying as you'd expect.")
        elif "scottish rock" in artist['genres']:
            track_comments.append("Scottish rock: bagpipes and bad decisions.")
        elif "australian garage punk" in artist['genres']:
            track_comments.append("Garage punk with an Aussie flair—still a mess.")
        elif "norwegian hip hop" in artist['genres']:
            track_comments.append("Norwegian hip hop? The world didn't need this.")
        else:
            track_comments.append("Generic and forgettable—no one will remember this.")
        # Combine comments for each track
        combined_comments = ' '.join(track_comments)
        track_info_with_comments.append({
            'track': track,
            'comment': combined_comments
        })

    # Pass profile data and top tracks with comments to the template
    return render_template('profile.html', profile=profile_data, track_info_with_comments=track_info_with_comments)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
