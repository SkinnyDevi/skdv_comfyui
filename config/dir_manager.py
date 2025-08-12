from pathlib import Path
import json

EXTENSION_PATH = Path("extensions")
USER_DATA_EXTENSION_PATH = Path("user_data/extensions")


def base_ext_path() -> Path:
    if USER_DATA_EXTENSION_PATH.joinpath("skdv_comfyui").exists():
        return USER_DATA_EXTENSION_PATH.joinpath("skdv_comfyui")

    return EXTENSION_PATH.joinpath("skdv_comfyui")


class DirManager:
    __instance = None

    __EXT_DIR = base_ext_path()
    __WEB_DIR = __EXT_DIR.joinpath("web")
    __WORKFLOW_DIR = __EXT_DIR.joinpath("workflows")
    __GENERATED_IMAGES_DIR = Path("user_data/cache/comfyui/")
    __CONFIG_DIR = __EXT_DIR.joinpath("config")

    __VERSION_FILE = __CONFIG_DIR.joinpath("version.json")

    def __new__(cls) -> "DirManager":
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)

        return cls.__instance

    def __ensure_dir_exists(self, dir: Path):
        if dir.exists():
            return

        dir.mkdir()

    def __init__(self) -> None:
        self.__ensure_dir_exists(DirManager.__WORKFLOW_DIR)
        self.__ensure_dir_exists(DirManager.__GENERATED_IMAGES_DIR)

    def get_web_dir(self):
        return DirManager.__WEB_DIR

    def get_workflows_dir(self):
        return DirManager.__WORKFLOW_DIR

    def get_images_dir(self):
        return DirManager.__GENERATED_IMAGES_DIR

    def get_config_dir(self):
        return DirManager.__CONFIG_DIR

    def __check_source_exists(self, source: Path, skip_check=False):
        if not source.exists() and not skip_check:
            raise FileNotFoundError(f"Path to {source} not found in extension.")

        return source.exists()

    def __get_from_module(self, module: Path, resource: str):
        self.__check_source_exists(module.joinpath(resource))
        return module.joinpath(resource)

    def __write_to_file(
        self, file_path: Path, content: str | bytes, write_binary=False
    ):
        with open(file_path, "wb" if write_binary else "w") as file:
            file.write(content)

    def get_or_create(self, file_path: Path):
        if file_path.suffix == "":
            raise Exception(f"Path '{file_path}' is a directory")

        if not file_path.exists():
            file_path.touch()

        return file_path

    def test_path_from_web(self, file_name: str):
        return self.__check_source_exists(
            DirManager.__WEB_DIR.joinpath(file_name), skip_check=True
        )

    def get_from_web(self, file_name: str):
        return self.__get_from_module(DirManager.__WEB_DIR, file_name)

    def test_path_from_config(self, file_name: str):
        return self.__check_source_exists(
            DirManager.__CONFIG_DIR.joinpath(file_name), skip_check=True
        )

    def get_from_config(self, file_name: str):
        return self.__get_from_module(DirManager.__CONFIG_DIR, file_name)

    def create_path_from_config(self, path: str):
        return DirManager.__CONFIG_DIR.joinpath(path)

    def save_to_config(self, file_path: Path, content: str):
        self.__write_to_file(file_path, content)
        return file_path

    def get_from_workflows(self, workflow_file: str):
        return self.__get_from_module(DirManager.__WORKFLOW_DIR, workflow_file)

    def test_path_to_character(self, character: str):
        return self.__check_source_exists(
            DirManager.__GENERATED_IMAGES_DIR.joinpath(character), skip_check=True
        )

    def get_images_from_character(self, character: str):
        self.__ensure_dir_exists(DirManager.__GENERATED_IMAGES_DIR.joinpath(character))
        image_dir = self.__get_from_module(DirManager.__GENERATED_IMAGES_DIR, character)
        return list(image_dir.iterdir())

    def get_image_from_character(self, character: str, image_name: str):
        images = self.get_images_from_character(character)
        for image in images:
            if image.name == image_name:
                return image

        return None

    def save_image_to_character(self, character: str, image_name: str, content: bytes):
        self.__ensure_dir_exists(DirManager.__GENERATED_IMAGES_DIR.joinpath(character))
        image_dir = self.__get_from_module(DirManager.__GENERATED_IMAGES_DIR, character)
        self.__write_to_file(image_dir.joinpath(image_name), content, write_binary=True)
        return image_dir.joinpath(image_name)

    def get_local_workflows(self):
        return list(self.get_workflows_dir().iterdir())

    def save_to_workflows(self, workflow_file_name: str, content: str):
        self.__write_to_file(
            DirManager.__WORKFLOW_DIR.joinpath(workflow_file_name), content
        )
        return DirManager.__WORKFLOW_DIR.joinpath(workflow_file_name)

    def save_to_extension_version(self, version: str):
        self.__write_to_file(self.__VERSION_FILE, json.dumps({"version": version}))
        return self.__VERSION_FILE

    def get_extension_version(self):
        self.__check_source_exists(self.__VERSION_FILE)
        return self.__VERSION_FILE
