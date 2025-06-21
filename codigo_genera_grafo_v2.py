import pandas as pd
import geopandas as gpd
import osmnx as ox
from shapely.geometry import Point
from tqdm import tqdm
import numpy as np
from scipy.spatial import cKDTree

ox.settings.use_cache = True
ox.settings.log_console = True

# Cargar árboles
arbrat_parcs = pd.read_csv("OD_Arbrat_Parcs_BCN.csv", sep=",", encoding="ISO-8859-1", on_bad_lines="skip")
arbrat_viari = pd.read_csv("OD_Arbrat_Viari_BCN.csv", sep=",", encoding="ISO-8859-1", on_bad_lines="skip")
arbrat_zona = pd.read_csv("OD_Arbrat_Zona_BCN.csv", sep=",", encoding="ISO-8859-1", on_bad_lines="skip")

def extraer_puntos(df):
    df = df[df["espai_verd"].notna()]
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["longitud"], df["latitud"]), crs="EPSG:4326")

gdf_parcs = extraer_puntos(arbrat_parcs)
gdf_viari = extraer_puntos(arbrat_viari)
gdf_zona = extraer_puntos(arbrat_zona)

zonas_verdes = pd.concat([gdf_parcs, gdf_viari, gdf_zona])
zonas_verdes.to_file("zonas_verdes.geojson", driver="GeoJSON")
print(f"Total árboles: {len(zonas_verdes)}")

# Cargar grafo
G = ox.graph_from_place("Barcelona, Spain", network_type="walk", simplify=True)
nodes, edges = ox.graph_to_gdfs(G, nodes=True, edges=True)
edges = edges.reset_index()

# CRS igual
zonas_verdes_proj = zonas_verdes.to_crs(edges.crs)

# KDTree con árboles
arbol_coords = np.array([(p.x, p.y) for p in zonas_verdes_proj.geometry])
tree = cKDTree(arbol_coords)

# Función para muestrear geometría
def sample_geometry(geom, num=5):
    return [geom.interpolate(i/num, normalized=True) for i in range(num+1)]

# Calculamos distancia media de cada tramo a los árboles
dists_medias = []
for geom in tqdm(edges.geometry, desc="Calculando distancias a sombra (rápido)"):
    muestras = sample_geometry(geom, num=5)
    puntos = np.array([(p.x, p.y) for p in muestras])
    distancias, _ = tree.query(puntos, k=1)
    dists_medias.append(np.mean(distancias))

edges["distancia_sombra_muestreada"] = dists_medias

# Asignamos al grafo
for u, v, k, data in G.edges(keys=True, data=True):
    geom = edges.loc[(edges["u"] == u) & (edges["v"] == v) & (edges["key"] == k)]
    if not geom.empty:
        data["distancia_sombra_muestreada"] = geom["distancia_sombra_muestreada"].values[0]


ox.save_graphml(G, filepath="grafo_barcelona_verde_muestreado.graphml")
print("✅ Grafo generado con muestreo rápido de sombra.")
