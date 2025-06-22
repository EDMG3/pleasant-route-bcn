<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
  </head>
  </head>
  <body>
    <p><strong>Pleasant Pathways in Barcelona</strong></p>
    <p>This project provides a Streamlit web application that helps users find the most pleasant walking routes across Barcelona. It uses environmental and urban data—such as trees, fountains, green areas, and real-time weather—to build a weighted graph that prioritizes comfortable walking experiences.</p>
    <p><strong>Project Files</strong></p>
    <ul>
      <li><i>2025_fonts_beure.csv</i>: Contains data on the locations of public drinking fountains in Barcelona.</li>
      <li><i>OD_Arbrat_Parcs_BCN.csv</i>: Tree data from public parks.</li>
      <li><i>OD_Arbrat_Viari_BCN.csv</i>: Tree data from road and street environments.</li>
      <li><i>OD_Arbrat_Zona_BCN.csv</i>: The area tree of the city of Barcelona that is located in the squares, parterres, gazebos or small garden spaces.</li>
      <li><i>zonas_verdes.geojson</i>: GeoJSON file representing the green zones (parks, gardens, etc.) in Barcelona.</li>
      <li><i>grafo_barcelona_verde_muestreado.graphml</i>: A pre-generated graph representing the green paths and urban spaces in Barcelona.</li>
      <li><i>codigo_genera_grafo_v2.py</i>: Python script used to generate the graph structure used for route optimization in the application.</li>
      <li><i>AEMETAPI.py</i>: Script that connects to the AEMET API to retrieve real-time weather information.</li>
      <li><i>app_camino_agradable_v11.py</i>: The main Streamlit app that: 
        <ul>
          <li>Displays an interactive map</li>
          <li>Calculates pleasant walking routes</li>
          <li>Shows statistics and project context</li>
        </ul>
      </li>
      <li><i>requirements.txt</i>: List of Python packages required to run the application (e.g., folium, networkx, streamlit).</li>
      <li><i>.gitattributes</i>: Used to manage large files (like .geojson) with Git LFS.</li>
    </ul>
  </body>
</html>
