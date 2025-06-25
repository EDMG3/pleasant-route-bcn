import requests

class AemetAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://opendata.aemet.es/opendata/api/"

    def _get_data_url(self, endpoint):
    headers = {"Accept": "application/json", "api_key": self.api_key}
    response = requests.get(self.base_url + endpoint, headers=headers)
    if response.status_code == 200:
        json_data = response.json()
        if "datos" in json_data:
            datos_url = json_data["datos"]
            datos_resp = requests.get(datos_url, headers=headers)
            if datos_resp.status_code == 200:
                return datos_resp.json()
    return None


    def get_prediction_city(self, city_code="08019"):
        endpoint = f"prediccion/especifica/municipio/diaria/{city_code}/"
        return self._get_data_url(endpoint)

    def get_warnings(self, area_code="08"):
        endpoint = f"avisos_cap/provincia/{area_code}/"
        return self._get_data_url(endpoint)
