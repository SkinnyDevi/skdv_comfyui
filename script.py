import user_data.extensions.skdv_comfyui.ui.main as comfyui
from user_data.extensions.skdv_comfyui.config.dir_manager import DirManager

params = {
    "display_name": "ComfyUI",
    "is_tab": True,
}

dir_manager = DirManager()


def load_skdv_comfyui_resource(file: str):
    with dir_manager.get_from_web(file).open("r", encoding="utf-8") as f:
        f = f.read()

    return f


def custom_css():
    return load_skdv_comfyui_resource("skdv_comfyui_styles.css")


def custom_js():
    return load_skdv_comfyui_resource("skdv_comfyui.js")


mount_for_tab = True


def ui():
    global mount_for_tab

    comfyui.mount_ui(mount_for_tab)

    if mount_for_tab:  # Made to mount both as Tab and in Extension Block
        mount_for_tab = False
        params["is_tab"] = False

