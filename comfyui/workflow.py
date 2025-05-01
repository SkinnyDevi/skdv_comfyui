import base64
import mimetypes
from pathlib import Path
from random import randint

from extensions.skdv_comfyui.config.config_handler import ConfigHandler
from extensions.skdv_comfyui.config.dir_manager import DirManager


DIR_MANAGER = DirManager()
CONFIG_HANDLER = ConfigHandler.setup()


class ComfyWorkflow:
    def __load_workflow(self, file: str) -> str:
        with open(DIR_MANAGER.get_from_workflows(file), "r") as workflow:
            return workflow.read()

    def __init__(self, workflow_file: str):
        self._raw_workflow = self.__load_workflow(workflow_file)
        self._positive_prompt = ""
        self._negative_prompt = ""
        self._character = ""

    @staticmethod
    def copy_from(workflow_file: str, workflow: "ComfyWorkflow") -> "ComfyWorkflow":
        new_workflow = ComfyWorkflow(workflow_file)
        new_workflow.set_positive_prompt(workflow._positive_prompt)
        new_workflow.set_negative_prompt(workflow._negative_prompt)
        new_workflow.set_character(workflow._character)
        return new_workflow

    @property
    def character(self):
        return self._character

    def set_positive_prompt(self, prompt: str):
        self._positive_prompt = prompt

    def set_negative_prompt(self, prompt: str):
        self._negative_prompt = prompt

    def set_character(self, character: str):
        self._character = character

    def __get_current_character_avatar(self):
        character = self._character
        if character == "" or character is None:
            raise ValueError("No character selected")

        image_path = Path("characters")
        for image_format in ["png", "jpg", "jpeg", "webp"]:
            if image_path.joinpath(f"{character}.{image_format}").exists():
                return image_path.joinpath(f"{character}.{image_format}")

        return None

    def __get_user_avatar(self):
        if not Path("cache/pfp_me.png").exists():
            return None

        return Path("cache/pfp_me.png")

    def __avatar_to_base64(self, image_path: Path | None):
        try:
            if not image_path:
                return ""

            mime_type = mimetypes.guess_type(image_path)[0]
            if not mime_type:
                mime_type = f"image/{image_path.suffix[1:]}"

            with open(image_path, "rb") as image:
                encoded = base64.b64encode(image.read()).decode("utf-8")
                return f"data:{mime_type};base64,{encoded}"
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Avatar image file not found: {e}")
        except Exception as e:
            raise Exception(f"Failed to convert avatar to base64: {e}")

    def __parse_seed(self, seed: int):
        if seed >= 0:
            return seed

        return randint(0, 2**31)

    def inject_parameters(self) -> tuple[str, int]:
        injected = f"{self._raw_workflow}"
        injected = injected.replace(
            "%prompt%", CONFIG_HANDLER.shared_positive_prompt + self._positive_prompt
        )
        injected = injected.replace(
            "%negative_prompt%",
            CONFIG_HANDLER.shared_negative_prompt + self._negative_prompt,
        )
        injected = injected.replace("%model%", CONFIG_HANDLER.model)
        injected = injected.replace("%vae%", CONFIG_HANDLER.vae or "")
        injected = injected.replace("%sampler%", CONFIG_HANDLER.sampler)
        injected = injected.replace("%scheduler%", CONFIG_HANDLER.scheduler)
        injected = injected.replace("%steps%", str(CONFIG_HANDLER.steps))
        injected = injected.replace("%scale%", str(CONFIG_HANDLER.cfg_scale))
        injected = injected.replace("%clip_skip%", str(CONFIG_HANDLER.clip_skip))
        injected = injected.replace("%width%", str(CONFIG_HANDLER.width))
        injected = injected.replace("%height%", str(CONFIG_HANDLER.height))

        if self.__get_current_character_avatar() is not None:
            injected = injected.replace(
                "%char_avatar%",
                self.__avatar_to_base64(self.__get_current_character_avatar()),
            )
        elif (
            self.__get_current_character_avatar() is None
            and injected.count("%char_avatar%") > 0
        ):
            raise FileNotFoundError(
                "Character avatar not found in characters directory"
            )

        if self.__get_user_avatar() is not None:
            injected = injected.replace(
                "%user_avatar%", self.__avatar_to_base64(self.__get_user_avatar())
            )
        elif self.__get_user_avatar() is None and injected.count("%user_avatar%") > 0:
            raise FileNotFoundError("User avatar not found")

        seed = self.__parse_seed(CONFIG_HANDLER.seed)
        injected = injected.replace("%seed%", str(seed))

        return injected, seed
