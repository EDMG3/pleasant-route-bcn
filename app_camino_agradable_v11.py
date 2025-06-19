import osmnx as ox
import networkx as nx
import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import pandas as pd
from folium.plugins import HeatMap
from AEMETAPI import AemetAPI
import requests
import matplotlib.pyplot as plt
import plotly.express as px

st.set_page_config(layout="wide", page_title="Pleasant Route Barcelona", page_icon="🌿")

# --- DATA LOADING ---
@st.cache_resource
def load_graph():
    return ox.load_graphml("grafo_barcelona_verde_muestreado.graphml")

@st.cache_resource
def load_green_zones():
    zones = gpd.read_file("zonas_verdes.geojson")
    return [[geom.y, geom.x] for geom in zones.geometry if geom is not None]

@st.cache_resource
def load_fountains():
    return pd.read_csv("2025_fonts_beure.csv", sep=",")

@st.cache_resource
def load_trees():
    return (
        pd.read_csv("OD_Arbrat_Viari_BCN.csv"),
        pd.read_csv("OD_Arbrat_Zona_BCN.csv"),
        pd.read_csv("OD_Arbrat_Parcs_BCN.csv")
    )

@st.cache_data
def get_aemet_data(api_key):
    aemet = AemetAPI(api_key)
    try:
        prediction = aemet.get_prediction_city()
    except requests.exceptions.RequestException as e:
        prediction = f"error::{e}"
    try:
        warnings = aemet.get_warnings()
    except requests.exceptions.RequestException as e:
        warnings = f"error::{e}"
    return prediction, warnings

# --- LOAD DATA ---
G = load_graph()
heat_data = load_green_zones()
fountains = load_fountains()
trees_viari, trees_zona, trees_parcs = load_trees()

# --- APP SECTIONS ---
section = st.sidebar.radio("Choose section:", ["Map & Weather", "Neighborhood Statistics", "About the Project"])

def set_backgrounds(section_bg_url, header_bg_url):
    st.markdown(f"""
        <style>
        /* Fondo sobre el contenedor principal */
        [data-testid="stAppViewContainer"] {{
            background-image: url('{section_bg_url}');
            background-attachment: fixed;
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center;
        }}

        /* Quitamos padding y márgenes de Streamlit */
        .stApp {{
            padding: 0;
            margin: 0;
        }}

        [data-testid="stHeader"] {{
            padding: 0;
            height: 3rem;
        }}

        /* Ajuste de ancho completo sin limitar a 960px */
        .block-container {{
            padding: 0;
            margin: 0 auto;
            max-width: 90%; /* margen lateral del 5% a cada lado */
            width: 90%;
            background-color: transparent; /* eliminamos el fondo blanco */
        }}

        /* Header personalizado (con más espacio superior) */
        .title-container {{
            background-image: url('{header_bg_url}');
            background-size: cover;
            background-position: center;
            padding: 5rem 3rem 3rem 3rem;
            width: 100%;
            border-radius: 0px;
            box-shadow: 0px 4px 8px rgba(0,0,0,0.4);
            margin-bottom: 2rem; /* <-- AQUÍ AÑADIMOS EL ESPACIO ABAJO */
        }}

        .title-container h1 {{
            color: white;
            text-align: center;
            font-size: 3rem;
            margin: 0;
            text-shadow: 3px 3px 6px #000000;
        }}

        /* Subtítulo: más margen superior */
        .subtitle {{
            margin-top: 2rem;
            text-align: center;
            font-size: 1.2rem;
        }}
        </style>
    """, unsafe_allow_html=True)

def render_title(title_text, header_bg_url):
    st.markdown(f"""
        <div class='title-container' style="background-image: url('{header_bg_url}');">
            <h1>{title_text}</h1>
        </div>
    """, unsafe_allow_html=True)


# --- SECTION 1: MAP & WEATHER ---
if section == "Map & Weather":
    section_bg = "https://i.imgur.com/OoCfFSD.jpeg"
    header_bg = "https://i.imgur.com/MfYYYqA.jpeg"
    set_backgrounds(section_bg, header_bg)

    render_title("🌿 Pleasant Walking Route in Barcelona", header_bg)

    st.markdown("""
    <p style='text-align: center;'>This app calculates pedestrian routes in Barcelona prioritizing shade, green zones, and drinking fountains.</p>
    """, unsafe_allow_html=True)

    for k in ["origin", "destination", "coords_origin", "coords_destination", "route", "stage"]:
        if k not in st.session_state:
            st.session_state[k] = None
    if st.session_state.stage is None:
        st.session_state.stage = "origin"

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("Click the map to select your *starting point.*" if st.session_state.stage == "origin" else "Click to select your *destination*.")

        m = folium.Map(location=[41.387, 2.17], zoom_start=13, control_scale=True)
        m.options['doubleClickZoom'] = False

        HeatMap(heat_data, radius=10, blur=15, min_opacity=0.3,
                gradient={0.4: 'green', 0.7: 'lime', 1: 'yellow'}).add_to(m)

        for _, row in fountains.iterrows():
            folium.Marker(
                location=(row['LATITUD'], row['LONGITUD']),
                icon=folium.DivIcon(html="""<div style='font-size:8px; color:#3399FF;'>💧</div>""")
            ).add_to(m)

        if st.session_state.coords_origin:
            folium.Marker(st.session_state.coords_origin, tooltip="Start", icon=folium.Icon(color="green")).add_to(m)
        if st.session_state.coords_destination:
            folium.Marker(st.session_state.coords_destination, tooltip="Destination", icon=folium.Icon(color="red")).add_to(m)

        if st.session_state.route:
            coords = []
            for u, v in zip(st.session_state.route[:-1], st.session_state.route[1:]):
                data = G.get_edge_data(u, v)[0]
                if "geometry" in data:
                    coords += list(data["geometry"].coords)
                else:
                    coords += [(G.nodes[u]["x"], G.nodes[u]["y"]), (G.nodes[v]["x"], G.nodes[v]["y"])]
            folium.PolyLine(locations=[(y, x) for x, y in coords], color="blue", weight=5).add_to(m)

        map_data = st_folium(m, width=None, height=600)

        if map_data and map_data["last_clicked"]:
            lat, lon = map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]
            node = ox.distance.nearest_nodes(G, X=lon, Y=lat)
            point = (lat, lon)

            if st.session_state.stage == "origin":
                st.session_state.origin = node
                st.session_state.coords_origin = point
                st.session_state.stage = "destination"
                st.rerun()
            elif st.session_state.stage == "destination" and node != st.session_state.origin:
                st.session_state.destination = node
                st.session_state.coords_destination = point
                st.session_state.stage = "done"
                st.rerun()

        if st.session_state.stage == "done" and not st.session_state.route:
            if st.button("📍 Calculate pleasant route"):
                def pleasant_weight(u, v, d):
                    length = d.get("length", 0)
                    shade = float(d.get("distancia_sombra_muestreada", 50))
                    return length + 20 * min(shade / 50, 1.0) * length

                try:
                    path = nx.shortest_path(G, st.session_state.origin, st.session_state.destination, weight=pleasant_weight)
                    st.session_state.route = path
                    st.rerun()
                except nx.NetworkXNoPath:
                    st.error("❌ No path found between selected points.")

        if st.session_state.route:
            dist = sum(G.get_edge_data(u, v)[0].get("length", 0) for u, v in zip(st.session_state.route[:-1], st.session_state.route[1:]))
            st.success(f"🚶‍♀ Total route distance: {dist:.1f} meters")

        if st.button("🔁 New route"):
            for k in ["origin", "destination", "coords_origin", "coords_destination", "route"]:
                st.session_state[k] = None
            st.session_state.stage = "origin"
            st.rerun()

    with col2:
        st.header("🌡 Weather info & warnings (AEMET)")
        API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJqb3NlcHRvbmlzaEBnbWFpbC5jb20iLCJqdGkiOiI0ODRmOWNlZi04MWNjLTQ2YmEtYjE5Ny1mYjEzN2E3NDBjODciLCJpc3MiOiJBRU1FVCIsImlhdCI6MTc1MDAwMzE4MSwidXNlcklkIjoiNDg0ZjljZWYtODFjYy00NmJhLWIxOTctZmIxMzdhNzQwYzg3Iiwicm9sZSI6IiJ9.xloAjXBps25YTzzPr6rUFGLrRTW9nvPmIDDKC4yjki0"
        prediction, warnings = get_aemet_data(API_KEY)

        if isinstance(prediction, str) and prediction.startswith("error::"):
            st.error(f"🌐 Error connecting to AEMET: {prediction[7:]}")
        elif prediction:
            try:
                today = prediction[0]['prediccion']['dia'][0]
                temp_max = int(today['temperatura']['maxima'])
                temp_min = int(today['temperatura']['minima'])
                st.info(f"🌡 Max: {temp_max} ºC · Min: {temp_min} ºC")

                if temp_max >= 40:
                    st.error("🔥 Extreme heat! Avoid going out.")
                elif temp_max >= 35:
                    st.warning("⚠ Very hot. Stay in shade.")
                elif temp_max >= 30:
                    st.info("☀ Warm. Take water.")
                elif temp_max >= 20:
                    st.success("🌤 Ideal walking weather.")
                else:
                    st.warning("❄ Cold weather, dress warm.")
            except Exception as e:
                st.error(f"⚠ Error processing AEMET data: {e}")
        else:
            st.warning("⚠ Forecast data unavailable.")

        if isinstance(warnings, str) and warnings.startswith("error::"):
            st.error(f"Error retrieving AEMET alerts: {warnings[7:]}")
        elif warnings:
            st.subheader("⚠ Active Warnings")
            for warning in warnings:
                st.write(warning)
        else:
            st.success("✅ No active alerts.")

# --- SECTION 2: STATISTICS ---
elif section == "Neighborhood Statistics":
    section_bg = "https://i.imgur.com/uHceXE8.jpeg"
    header_bg = "https://i.imgur.com/QOph7V9.jpeg"
    set_backgrounds(section_bg, header_bg)

    render_title("🌱 Urban Tree Statistics by Neighborhood", header_bg)
    
    neighborhoods = sorted(trees_viari['nom_barri'].dropna().unique())
    selected = st.selectbox("Select neighborhood:", neighborhoods)

    df_viari = trees_viari[trees_viari['nom_barri'] == selected]
    df_zona = trees_zona[trees_zona['nom_barri'] == selected]
    df_parcs = trees_parcs[trees_parcs['nom_barri'] == selected]

    st.subheader("Number of trees by type")
    df_types = pd.DataFrame({
        'Type': ['Street', 'Green areas', 'Parks'],
        'Count': [len(df_viari), len(df_zona), len(df_parcs)]
    })
    fig1 = px.bar(df_types, x='Type', y='Count', color_discrete_sequence=['green'])
    fig1.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=14, color='black', family="Arial", weight='bold'),
        xaxis=dict(title_font=dict(size=16, color='black', family="Arial", weight='bold'),
                   tickfont=dict(size=14, color='black', weight='bold'),
                   linecolor='black', linewidth=2),
        yaxis=dict(title_font=dict(size=16, color='black', family="Arial", weight='bold'),
                   tickfont=dict(size=14, color='black', weight='bold'),
                   linecolor='black', linewidth=2,
                   gridcolor='rgb(150,150,150)')
    )
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("Top 5 tree species (scientific name)")
    top_species = pd.concat([df_viari, df_zona, df_parcs])['cat_nom_cientific'].value_counts().nlargest(5).reset_index()
    top_species.columns = ['Species', 'Count']
    fig2 = px.bar(top_species, x='Species', y='Count', color_discrete_sequence=['green'])
    fig2.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=14, color='black', family="Arial", weight='bold'),
        xaxis=dict(title_font=dict(size=16, color='black', family="Arial", weight='bold'),
            tickfont=dict(size=14, color='black', weight='bold'),
            linecolor='black', linewidth=2),
        yaxis=dict(title_font=dict(size=16, color='black', family="Arial", weight='bold'),
            tickfont=dict(size=14, color='black', weight='bold'),
            linecolor='black', linewidth=2,
            gridcolor='rgb(150,150,150)')
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Annual tree planting evolution")
    mode = st.radio("Chart type:", ["By year", "Cumulative"], horizontal=True)
    df_dates = pd.concat([df_viari, df_zona, df_parcs])
    df_dates['year'] = pd.to_datetime(df_dates['data_plantacio'], errors='coerce').dt.year
    df_years = df_dates['year'].dropna().value_counts().sort_index().reset_index()
    df_years.columns = ['Year', 'Count']
    if mode == "Cumulative":
        df_years['Count'] = df_years['Count'].cumsum()
    fig3 = px.line(df_years, x='Year', y='Count', markers=True, color_discrete_sequence=['green'])
    fig3.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=14, color='black', family="Arial", weight='bold'),
        xaxis=dict(title_font=dict(size=16, color='black', family="Arial", weight='bold'),
                   tickfont=dict(size=14, color='black', weight='bold'),
                   linecolor='black', linewidth=2),
        yaxis=dict(title_font=dict(size=16, color='black', family="Arial", weight='bold'),
                   tickfont=dict(size=14, color='black', weight='bold'),
                   linecolor='black', linewidth=2,
                   gridcolor='rgb(150,150,150)')
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Neighborhood tree map")

    df_map = pd.concat([df_viari, df_zona, df_parcs])
    df_map = df_map[df_map['latitud'].notna() & df_map['longitud'].notna()]

    map_barri = folium.Map(
        location=[df_map['latitud'].mean(), df_map['longitud'].mean()],
        zoom_start=15
    )

    for _, row in df_map.iterrows():
        folium.CircleMarker(
            location=[row['latitud'], row['longitud']],
            radius=2,
            color='green',
            fill=True,
            fill_opacity=0.6
        ).add_to(map_barri)

    with st.container():
        st_folium(map_barri, width=None, height=600)


# --- SECTION 3: ABOUT ---
elif section == "About the Project":
    section_bg = "https://i.imgur.com/KlR7cQ1.png"
    header_bg = "https://i.imgur.com/r1R4zQI.jpeg"
    set_backgrounds(section_bg, header_bg)

    render_title("About the Project", header_bg)

    st.markdown("""
<div style='background-color: white; padding: 2rem; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);'>

### Project Objective

This project is part of a university initiative to apply **Data Science and Urban Analytics** to real-world environmental and mobility challenges. Our main goal is to help pedestrians in Barcelona choose routes that minimize sun exposure, maximize shade availability, and provide access to public water sources — improving comfort, health, and safety during increasingly frequent heat waves.

---

### Scientific Approach

The project integrates multiple open datasets from Barcelona's public data platform, including:

- Detailed tree inventories for parks, streets and green zones.
- Public water fountains dataset.
- Urban street network from OpenStreetMap.
- Real-time weather and alerts from AEMET official API.

We enrich the street network graph by adding an attribute to each street segment: **"proximity to green elements"**, based on spatial distance to nearby trees. This allows us to model shade as a proxy for heat exposure risk.

---

### Methodology

- **Spatial Data Processing:**
     - Trees converted into spatial points (GeoDataFrames).
     - Green proximity estimated using spatial KDTree nearest-neighbor search.
     - Zones projected into the same Coordinate Reference System (CRS) for accurate distance calculations.
     - Distances stored as edge attributes in the pedestrian graph.

- **Routing Algorithm:**
     - NetworkX shortest path algorithm.
     - Custom edge weight combining route length and shade score: **cost = length + λ * shade_bonus**, where λ reflects the importance given to the shadow.

- **Heatmap Visualization:**
    - Kernel-like shadow visualization over tree concentrations.
    - Dynamic route recalculation upon user input.
    
- **Water Source Integration:**
    - Public fountains mapped as points of interest to support hydration planning.

- **Real-Time Weather (AEMET):**
    - Official forecasts and extreme heat alerts automatically retrieved.
    - Context-aware warnings issued to users based on temperature thresholds.

---

### Urban Wellbeing Perspective

Barcelona, like many global cities, is increasingly exposed to climate change effects: **heat stress, sunstroke, and urban overheating**.

This tool demonstrates how **data-driven urban routing** can:

- Improve pedestrian thermal comfort.
- Support public health on extreme heat days.
- Encourage green infrastructure awareness.

---

> *Data Science for Urban Health & Climate Adaptation.*

</div>
""", unsafe_allow_html=True)
