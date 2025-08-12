import html
from modules import shared, chat

from user_data.extensions.skdv_comfyui.config.config_handler import ConfigHandler

CONFIG_HANLDER = ConfigHandler.setup()


def generate(prompt: str, state: dict):
    if shared.model is None or shared.model_name == "None":
        raise ValueError("Model and tokenizer are not loaded.")

    history = list(chat.generate_chat_reply(prompt, state.copy()))[-1]
    output: str = history["visible"][-1][1]
    try:
        return html.unescape(output.replace(history["visible"][-2][1], ""))
    except IndexError:
        return html.unescape(output)


def generate_image_description_from_message(message: str, state: dict):
    if (
        CONFIG_HANLDER.image_descriptor_prompt is None
        or CONFIG_HANLDER.image_descriptor_prompt == ""
    ):
        raise ValueError(
            "Image description cannot be empty for description generation."
        )

    if "%message%" not in CONFIG_HANLDER.image_descriptor_prompt:
        raise ValueError("'%message%' was not found in image descriptor prompt.")

    return generate(
        CONFIG_HANLDER.image_descriptor_prompt.replace("%message%", message), state
    )

