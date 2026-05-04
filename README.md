# 🚦 Traffic Route App

A Streamlit-based web application that helps users find driving routes between two locations, view real-time traffic estimates, and save their search history. No API keys are required — it uses free, open-source services (OpenStreetMap / Nominatim and OSRM).

---

## ✨ Features

- **Route Search** — Enter any two addresses (or raw coordinates) to get the driving route.
- **Interactive Map** — Visualize the route with start/end markers and a path line powered by Folium.
- **Traffic Estimates** — Displays distance, normal duration, and duration with traffic heuristic.
- **Search History** — Automatically saves every searched route to a local SQLite database.
- **Frequent Routes** — Tracks and highlights your most-used routes.
- **No API Keys Needed** — Uses free public APIs (Nominatim + OSRM).

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────┐
│              User Browser                │
│  ┌──────────────┐  ┌──────────────┐    │
│  │  Home Page   │  │ Saved Routes │    │
│  │  (home.py)   │  │(saved_routes)│    │
│  └──────┬───────┘  └──────┬───────┘    │
└─────────┼─────────────────┼────────────┘
          │                 │
          └─────────────────┼──────────────┘
                            │
                    ┌───────▼────────┐
                    │    app.py      │
                    │  (Streamlit    │
                    │   entry point) │
                    └───────┬────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
 ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
 │  backend/   │    │  frontend/  │    │   utils/    │
 │  maps.py    │    │  map_view.py│    │  helpers.py │
 │  database.py│    │             │    │             │
 │  auth.py    │    │             │    │             │
 └─────────────┘    └─────────────┘    └─────────────┘
```

---

## 📁 Project Structure

| File / Folder | Purpose |
|---------------|---------|
| `app.py` | Streamlit entry point. Sets up page config, sidebar navigation, and routes to pages. |
| `frontend/home.py` | Main search page. Handles user input, geocoding, routing, and displays results. |
| `frontend/saved_routes.py` | Shows frequent routes and full search history in tabs. |
| `frontend/map_view.py` | Renders an interactive Folium map with the route path and markers. |
| `frontend/gps_component/` | (Unused) Custom Streamlit bi-directional component for browser GPS. |
| `backend/maps.py` | `MapHandler` class — geocoding, reverse geocoding, OSRM routing, traffic estimates. |
| `backend/database.py` | SQLite database layer — creates tables, saves routes, retrieves history / frequent routes. |
| `backend/auth.py` | User registration and login with bcrypt password hashing. |
| `utils/helpers.py` | Coordinate parsing, validation, address cleaning, and formatting utilities. |
| `requirements.txt` | Python dependencies. |
| `test_imports.py` | Sanity-check script that validates imports and basic functionality. |

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the App

```bash
streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`.

---

## 🔧 How It Works

1. **User enters origin & destination** in `home.py`.
2. **Geocoding** — `MapHandler.get_coordinates()` uses Nominatim (OpenStreetMap) to convert addresses into `(lat, lon)` tuples. Also supports raw coordinate strings like `"22.71, 75.85"`.
3. **Routing** — `MapHandler.get_route()` queries OSRM (OpenStreetMap Routing Machine) for the actual driving path. If OSRM is down, it falls back to a straight-line interpolation.
4. **Traffic Data** — `MapHandler.get_traffic_data()` uses OSRM distance/duration and applies a realistic traffic multiplier (10–25 % depending on trip length).
5. **Map Rendering** — `map_view.render_map()` draws the route on a Folium map with green (start) and red (end) markers.
6. **Persistence** — Every search is saved to `data/traffic_routes.db` via `database.py`.

---

## 🗃️ Database Schema

SQLite file: `data/traffic_routes.db`

### `users`
| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | |
| `username` | TEXT UNIQUE NOT NULL | |
| `password_hash` | TEXT NOT NULL | bcrypt hashed |

### `routes` (search history)
| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | |
| `user_id` | INTEGER NOT NULL | FK → users(id) |
| `origin` | TEXT NOT NULL | |
| `destination` | TEXT NOT NULL | |
| `distance` | TEXT | e.g. "12.5 km" |
| `duration` | TEXT | e.g. "25 mins" |
| `timestamp` | TEXT | ISO format |

### `frequent_routes`
| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | |
| `user_id` | INTEGER NOT NULL | FK → users(id) |
| `origin` | TEXT NOT NULL | |
| `destination` | TEXT NOT NULL | |
| `trip_count` | INTEGER DEFAULT 1 | |

---

## 🛠️ Tech Stack

- **Frontend UI**: [Streamlit](https://streamlit.io/)
- **Maps**: [Folium](https://python-visualization.github.io/folium/) + [streamlit-folium](https://github.com/randyzwitch/streamlit-folium)
- **Geocoding**: [geopy](https://geopy.readthedocs.io/) (Nominatim)
- **Routing**: [OSRM](http://project-osrm.org/) public demo server
- **Database**: SQLite (built into Python)
- **Authentication**: bcrypt
- **Data Processing**: pandas

---

## 📝 Notes

- The app defaults to `user_id = 1` (no login required) so it works out-of-the-box.
- OSRM is a free public service — for heavy production use, consider hosting your own OSRM instance.

