import json
import requests

from user_data.extensions.skdv_comfyui.config.config_handler import ConfigHandler


class ExtUpdateManager:
    __JSON_CHECKER_URL = "https://raw.githubusercontent.com/SkinnyDevi/skdv_comfyui/master/config/version.json"

    @staticmethod
    def check_for_updates(config: ConfigHandler):
        try:
            online_config: dict = requests.get(
                ExtUpdateManager.__JSON_CHECKER_URL
            ).json()
        except json.JSONDecodeError:
            online_config = {}

        online_version = online_config.get("version")
        local_version = config.version

        return False if online_version is None else local_version != online_version
