import gradio as gr

from user_data.extensions.skdv_comfyui.ui.generation_parameters import (
    generation_parameters_ui,
)
from user_data.extensions.skdv_comfyui.ui.image_descritor_prompt_settings import (
    image_descriptor_prompt_settings_ui,
)
from user_data.extensions.skdv_comfyui.ui.update_checker_tab import update_checker_ui
from user_data.extensions.skdv_comfyui.ui.workflow_importer import workflow_importer_ui
from user_data.extensions.skdv_comfyui.ui.character_parameters import (
    character_parameters_ui,
)
from user_data.extensions.skdv_comfyui.ui.extensions_chat_panel import (
    comfyui_chat_panel_ui,
    comfyui_hover_menu_buttons_ui,
)
from user_data.extensions.skdv_comfyui.ui.workflow_editor import workflow_editor_ui


def mount_ui(mount_for_tab: bool):
    if not mount_for_tab:
        comfyui_chat_panel_ui()
        comfyui_hover_menu_buttons_ui()
        return

    with gr.Tabs(elem_id="skdv_comfyui_tabs"):
        with gr.TabItem("Generation Settings"):
            with gr.Column():
                with gr.Row():
                    with gr.Column():
                        generation_parameters_ui()

                    with gr.Column():
                        workflow_importer_ui()

        with gr.TabItem("Character Settings"):
            with gr.Column():
                with gr.Row():
                    with gr.Column():
                        character_parameters_ui()

        with gr.TabItem("Image Descriptor Settings"):
            image_descriptor_prompt_settings_ui()

        with gr.TabItem("Workflow Editor"):
            workflow_editor_ui()

        with gr.TabItem("Update Checker"):
            update_checker_ui()

