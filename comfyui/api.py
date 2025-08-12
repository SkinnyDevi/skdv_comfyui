import requests

from user_data.extensions.skdv_comfyui.config.config_handler import ConfigHandler
from user_data.extensions.skdv_comfyui.config.dir_manager import DirManager
from user_data.extensions.skdv_comfyui.comfyui.workflow import ComfyWorkflow

CONFIG_HANDLER = ConfigHandler.setup()
DIR_MANAGER = DirManager()


class ComfyAPI:
    @staticmethod
    def ping():
        try:
            requests.get(CONFIG_HANDLER.api_url + "/system_stats")
            return True
        except Exception as e:
            print(f"Could not connect to ComfyUI:\n{e}")
            return False

    @staticmethod
    def unload():
        response = requests.post(CONFIG_HANDLER.api_url + "/free", json={"mode": 1})
        response.raise_for_status()

        return response.status_code == 200

    @staticmethod
    def get_generation_info() -> dict:
        try:
            return requests.get(CONFIG_HANDLER.api_url + "/object_info").json()
        except Exception as e:
            print(f"Could not fetch generation parameters:\n{e}")
            return {}

    @staticmethod
    def get_samplers(generation_info: dict | None = None) -> list[str]:
        response = generation_info or ComfyAPI.get_generation_info()
        return response["KSampler"]["input"]["required"]["sampler_name"][0]

    @staticmethod
    def get_models(generation_info: dict | None = None) -> list[str]:
        response = generation_info or ComfyAPI.get_generation_info()
        return response["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]

    @staticmethod
    def get_schedulers(generation_info: dict | None = None) -> list[str]:
        response = generation_info or ComfyAPI.get_generation_info()
        return response["KSampler"]["input"]["required"]["scheduler"][0]

    @staticmethod
    def get_vaes(generation_info: dict | None = None) -> list[str]:
        response = generation_info or ComfyAPI.get_generation_info()
        return response["VAELoader"]["input"]["required"]["vae_name"][0]

    @staticmethod
    def __get_output_image(generation_result: dict) -> tuple[bytes, str]:
        output = generation_result[list(generation_result.keys())[0]]["images"][0]
        response = requests.get(
            CONFIG_HANDLER.api_url
            + f"/view?filename={output['filename']}&subfolder={output['subfolder']}&type={output['type']}",
            stream=True,
        )
        response.raise_for_status()
        return response.content, output["filename"]

    @staticmethod
    def __save_image(image_result: bytes, image_name: str, character: str):
        if character == "" or character is None:
            raise ValueError("No character selected")

        return DIR_MANAGER.save_image_to_character(character, image_name, image_result)

    @staticmethod
    def generate(workflow: ComfyWorkflow):
        import json

        raw_workflow, seed = workflow.inject_parameters()

        try:
            loaded_workflow = json.loads(raw_workflow)
        except json.JSONDecodeError as e:
            raise ValueError(
                "[skdv_comfyui] The workflow loaded is not valid for generation. Please check the JSON File. JSON Error: "
                + e.msg
            )

        response = requests.post(
            CONFIG_HANDLER.api_url + "/prompt",
            json={"prompt": loaded_workflow},
        )
        response.raise_for_status()
        response = response.json()

        generation_id = response["prompt_id"]
        generation_result = None
        while generation_result is None:
            import time

            history_response = requests.get(CONFIG_HANDLER.api_url + "/history")
            history_response.raise_for_status()
            history_response = history_response.json()
            if generation_id in history_response:
                generation_result = history_response[generation_id]
                continue

            time.sleep(0.2)
        if generation_result["status"]["status_str"] != "success":
            raise Exception(
                f"Generation failed: ComfyUI generation status - {generation_result['status']['status_str']}"
            )
        image_output, file_name = ComfyAPI.__get_output_image(
            generation_result["outputs"]
        )
        return ComfyAPI.__save_image(image_output, file_name, workflow.character), seed
