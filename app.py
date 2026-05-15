import streamlit as st
import pickle
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------------- PAGE CONFIG ---------------- #
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

# ---------------- CUSTOM CSS ---------------- #
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --bg-deep:     #08090c;
    --bg-card:     #0f1116;
    --border:      rgba(255,255,255,0.06);
    --gold:        #c9a84c;
    --gold-glow:   rgba(201,168,76,0.18);
    --gold-subtle: rgba(201,168,76,0.07);
    --text-primary:#eeeae0;
    --text-muted:  #5a6070;
}

/* ── Base ── */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"],
[data-testid="stMain"],
section.main { background-color: var(--bg-deep) !important; }

/* Film-grain overlay */
[data-testid="stApp"]::after {
    content: '';
    position: fixed; inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.035'/%3E%3C/svg%3E");
    pointer-events: none; z-index: 9999; opacity: 0.5;
}

/* Ambient top glow */
[data-testid="stMain"]::before {
    content: '';
    position: fixed; top: -180px; left: 50%; transform: translateX(-50%);
    width: 800px; height: 380px;
    background: radial-gradient(ellipse, rgba(201,168,76,0.08) 0%, transparent 70%);
    pointer-events: none; z-index: 0;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

/* ── Typography ── */
* { font-family: 'DM Sans', sans-serif; box-sizing: border-box; }

/* ── Title ── */
.title {
    text-align: center;
    font-family: 'Playfair Display', serif;
    font-size: clamp(32px, 5vw, 60px);
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.5px;
    margin: 52px 0 8px;
    line-height: 1.1;
    animation: fadeDown 0.8s cubic-bezier(0.16,1,0.3,1) both;
}

.title em {
    color: var(--gold);
    font-style: italic;
}

/* ── Subtitle ── */
.subtitle {
    text-align: center;
    color: var(--text-muted);
    font-size: 11px;
    font-weight: 400;
    letter-spacing: 0.30em;
    text-transform: uppercase;
    margin-bottom: 8px;
    animation: fadeDown 0.8s 0.08s cubic-bezier(0.16,1,0.3,1) both;
}

/* ── Gold rule ── */
.gold-rule {
    width: 48px; height: 1px;
    background: linear-gradient(to right, transparent, var(--gold), transparent);
    margin: 0 auto 48px;
    animation: fadeDown 0.8s 0.16s cubic-bezier(0.16,1,0.3,1) both;
}

/* ── Movie card ── */
.movie-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 10px 10px 14px;
    text-align: center;
    height: 100%;
    position: relative;
    overflow: hidden;
    transition:
        transform 0.38s cubic-bezier(0.34,1.56,0.64,1),
        box-shadow 0.38s ease,
        border-color 0.38s ease;
    animation: fadeUp 0.55s cubic-bezier(0.16,1,0.3,1) both;
}

.movie-card::before {
    content: '';
    position: absolute; inset: 0;
    background: linear-gradient(140deg, var(--gold-subtle) 0%, transparent 55%);
    opacity: 0;
    transition: opacity 0.38s ease;
    border-radius: 12px;
    pointer-events: none;
}

.movie-card:hover {
    transform: translateY(-8px) scale(1.015);
    border-color: rgba(201,168,76,0.28);
    box-shadow:
        0 0 0 1px rgba(201,168,76,0.10),
        0 24px 48px rgba(0,0,0,0.65),
        0 0 70px var(--gold-glow);
}

.movie-card:hover::before { opacity: 1; }

/* ── Movie title text ── */
.movie-title {
    color: var(--text-primary);
    font-size: 12px;
    font-weight: 500;
    margin-top: 11px;
    line-height: 1.45;
    letter-spacing: 0.01em;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
    background-color: var(--bg-card) !important;
    border: 1px solid rgba(201,168,76,0.22) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-size: 14px !important;
    transition: border-color 0.2s, box-shadow 0.2s;
}
[data-testid="stSelectbox"] > div > div:focus-within {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 3px var(--gold-glow) !important;
}
[data-testid="stSelectbox"] label {
    color: var(--text-muted) !important;
    font-size: 11px !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
}

/* ── Recommend button ── */
.stButton > button {
    width: 100%;
    background: transparent !important;
    border: 1px solid var(--gold) !important;
    color: var(--gold) !important;
    border-radius: 8px;
    padding: 13px 32px;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    letter-spacing: 0.22em !important;
    text-transform: uppercase !important;
    transition: all 0.28s ease;
    position: relative;
    overflow: hidden;
}
.stButton > button::after {
    content: '';
    position: absolute; inset: 0;
    background: var(--gold-subtle);
    opacity: 0;
    transition: opacity 0.28s ease;
}
.stButton > button:hover {
    box-shadow: 0 0 28px var(--gold-glow), 0 4px 20px rgba(0,0,0,0.4) !important;
    transform: translateY(-2px);
    color: #e0ba62 !important;
    border-color: #e0ba62 !important;
}
.stButton > button:hover::after { opacity: 1; }

/* ── Spinner ── */
[data-testid="stSpinner"] p { color: var(--gold) !important; }

/* ── Warning / info ── */
[data-testid="stAlert"] {
    background: rgba(201,168,76,0.06) !important;
    border: 1px solid rgba(201,168,76,0.2) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: rgba(201,168,76,0.25); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--gold); }

/* ── Animations ── */
@keyframes fadeDown {
    from { opacity: 0; transform: translateY(-16px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(22px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* Stagger cards per row */
.movie-card:nth-child(1) { animation-delay: 0.04s; }
.movie-card:nth-child(2) { animation-delay: 0.09s; }
.movie-card:nth-child(3) { animation-delay: 0.14s; }
.movie-card:nth-child(4) { animation-delay: 0.19s; }
.movie-card:nth-child(5) { animation-delay: 0.24s; }

</style>
""", unsafe_allow_html=True)

# ---------------- CACHE DATA FOR FAST PERFORMANCE ---------------- #
@st.cache_data(show_spinner="Loading movie data...")
def load_data():
    movies = pickle.load(open('movies.pkl', 'rb'))
    similarity = pickle.load(open('similarity.pkl', 'rb'))
    return movies, similarity

movies, similarity = load_data()

# ---------------- TMDB API ---------------- #
try:
    API_KEY = st.secrets["TMDB_API_KEY"]
except Exception:
    API_KEY = "c08b4bde8c46e50b95d9a6ada71d62d9"

# ---------------- FETCH POSTER (cached, with error handling) ---------------- #
@st.cache_data(ttl=3600)
def fetch_poster(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get('poster_path')
        if poster_path:
            return "https://image.tmdb.org/t/p/w500/" + poster_path
    except Exception:
        pass
    return "https://via.placeholder.com/500x750?text=No+Image"

# ---------------- PARALLEL POSTER FETCHING ---------------- #
def fetch_posters_parallel(movie_ids):
    """Fetch all posters concurrently instead of one-by-one."""
    posters = [None] * len(movie_ids)
    with ThreadPoolExecutor(max_workers=15) as executor:
        future_to_index = {
            executor.submit(fetch_poster, movie_id): idx
            for idx, movie_id in enumerate(movie_ids)
        }
        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            try:
                posters[idx] = future.result()
            except Exception:
                posters[idx] = "https://via.placeholder.com/500x750?text=No+Image"
    return posters

# ---------------- RECOMMEND FUNCTION ---------------- #
def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]

    recommended_movies = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )[1:16]

    movie_names = [movies.iloc[i[0]].title for i in recommended_movies]
    movie_ids   = [movies.iloc[i[0]].movie_id for i in recommended_movies]

    # Fetch all posters in parallel — ~5-10x faster than sequential
    movie_posters = fetch_posters_parallel(movie_ids)

    return movie_names, movie_posters

# ---------------- HEADER ---------------- #
st.markdown('<div class="title">🎬 Movie <em>Recommender</em></div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Discover films tailored to your taste</div>', unsafe_allow_html=True)
st.markdown('<div class="gold-rule"></div>', unsafe_allow_html=True)

# ---------------- SEARCH DROPDOWN ---------------- #
selected_movie = st.selectbox(
    '🔍 Search or choose a movie',
    movies['title'].values,
    index=None,
    placeholder='⚡ Start typing movie name for instant search...'
)

# ---------------- BUTTON ---------------- #
if st.button('Recommend Movies'):
    if not selected_movie:
        st.warning("Please select a movie first.")
    else:
        with st.spinner("Finding recommendations..."):
            names, posters = recommend(selected_movie)

        for i in range(0, len(names), 5):
            cols = st.columns(5)
            for idx, col in enumerate(cols):
                if i + idx < len(names):
                    with col:
                        st.markdown('<div class="movie-card">', unsafe_allow_html=True)
                        st.image(posters[i + idx], use_container_width=True)
                        st.markdown(
                            f'<div class="movie-title">{names[i + idx]}</div>',
                            unsafe_allow_html=True
                        )
                        st.markdown('</div>', unsafe_allow_html=True)