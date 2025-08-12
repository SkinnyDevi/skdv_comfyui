import gradio as gr

from user_data.extensions.skdv_comfyui.config.config_handler import ConfigHandler

CONFIG_HANDLER = ConfigHandler.setup()


def image_descriptor_prompt_settings_ui():
    prompt_editor_textarea = gr.TextArea(
        value=CONFIG_HANDLER.image_descriptor_prompt,
        label="Edit the prompt used to generate image prompts for a chat message using your currently loaded text model.",
        placeholder="Use comma separated values...",
        lines=40,
    )

    prompt_editor_textarea.change(
        fn=lambda new: CONFIG_HANDLER.set_image_descriptor_prompt(new),
        inputs=prompt_editor_textarea,
    )

