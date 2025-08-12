import gradio as gr
import json

import modules.ui as oobabooga_ui

from user_data.extensions.skdv_comfyui.config.config_handler import ConfigHandler
from user_data.extensions.skdv_comfyui.config.dir_manager import DirManager
from user_data.extensions.skdv_comfyui.ui.generation_parameters import (
    load_local_workflows,
    update_workflow_file,
)

config_handler = ConfigHandler.setup()
dir_manager = DirManager()

loaded_workflow: str | None = None


def load_workflow(workflow_file: str | None):
    if workflow_file is None:
        return "{}"

    file_path = dir_manager.get_from_workflows(workflow_file)

    with open(file_path, "r") as workflow:
        read_file = workflow.read()
        try:
            return json.dumps(json.loads(read_file), indent=4)
        except json.JSONDecodeError:
            return read_file


def save_workflow(workflow_file: str, content: str):
    dir_manager.save_to_workflows(workflow_file, content)


def update_editor_with_new_file(workflow_file: str):
    update_workflow_file(workflow_file)
    return gr.update(value=load_workflow(workflow_file), label=workflow_file)


def wrap_variable(name: str):
    return f"%{name}%"


def workflow_has_variable(variable: str):
    global loaded_workflow

    if config_handler.current_workflow_file is None:
        return False

    if loaded_workflow is None:
        loaded_workflow = load_workflow(config_handler.current_workflow_file)

    return wrap_variable(variable) in loaded_workflow


def update_checks_with_file_content(file_content: str):
    global loaded_workflow

    variables = {
        "prompt": False,
        "negative_prompt": False,
        "model": False,
        "vae": False,
        "sampler": False,
        "scheduler": False,
        "steps": False,
        "scale": False,
        "clip_skip": False,
        "width": False,
        "height": False,
        "user_avatar": False,
        "char_avatar": False,
        "seed": False,
    }
    loaded_workflow = file_content

    for var in variables.keys():
        variables[var] = workflow_has_variable(var)

    return [value for value in variables.values()]


def validate_json_editor(content: str):
    validity_msg = "JSON is valid."
    try:
        json.loads(content)
    except json.JSONDecodeError as err:
        validity_msg = "JSON is not valid:\n"
        validity_msg += f"- Error: {err.msg} - line {err.lineno}, column {err.colno}\n"

    return validity_msg


def workflow_editor_ui():
    with gr.Row():
        workflow_dropdown = gr.Dropdown(
            load_local_workflows(),
            value=config_handler.current_workflow_file,
            label="Select a ComfyUI workflow",
            interactive=True,
            elem_classes=["slim-dropdown"],
            scale=2,
        )

        oobabooga_ui.create_refresh_button(
            workflow_dropdown,
            lambda: None,
            lambda: {
                "choices": load_local_workflows(),
                "value": config_handler.current_workflow_file,
            },
            ["refresh-button"],
        )

    with gr.Row():
        with gr.Column(scale=0):
            gr.Markdown(
                "## Available variables \nDisplays what variables are currently being used in the workflow"
            )

            valid_json_textbox = gr.TextArea(
                value=validate_json_editor(
                    load_workflow(config_handler.current_workflow_file)
                ),
                label="Workflow is Valid?",
                interactive=False,
                lines=4,
                info='Please use this as a guide. Some errors may be misleading. Tips: Make sure all curly braces open and close, Make sure there are no random characters out of place, Always close quotes ""',
            )

            prompt_check = gr.Checkbox(
                value=workflow_has_variable("prompt"), label=wrap_variable("prompt")
            )
            negative_prompt_check = gr.Checkbox(
                value=workflow_has_variable("negative_prompt"),
                label=wrap_variable("negative_prompt"),
            )
            model_check = gr.Checkbox(
                value=workflow_has_variable("model"), label=wrap_variable("model")
            )
            vae_check = gr.Checkbox(
                value=workflow_has_variable("vae"), label=wrap_variable("vae")
            )
            sampler_check = gr.Checkbox(
                value=workflow_has_variable("sampler"), label=wrap_variable("sampler")
            )
            scheduler_check = gr.Checkbox(
                value=workflow_has_variable("scheduler"),
                label=wrap_variable("scheduler"),
            )
            steps_check = gr.Checkbox(
                value=workflow_has_variable("steps"), label=wrap_variable("steps")
            )
            scale_check = gr.Checkbox(
                value=workflow_has_variable("scale"), label=wrap_variable("scale")
            )
            clip_skip_check = gr.Checkbox(
                value=workflow_has_variable("clip_skip"),
                label=wrap_variable("clip_skip"),
            )
            width_check = gr.Checkbox(
                value=workflow_has_variable("width"), label=wrap_variable("width")
            )
            height_check = gr.Checkbox(
                value=workflow_has_variable("height"), label=wrap_variable("height")
            )
            user_avatar_check = gr.Checkbox(
                value=workflow_has_variable("user_avatar"),
                label=wrap_variable("user_avatar"),
            )
            char_avatar_check = gr.Checkbox(
                value=workflow_has_variable("char_avatar"),
                label=wrap_variable("chat_avatar"),
            )
            seed_check = gr.Checkbox(
                value=workflow_has_variable("seed"), label=wrap_variable("seed")
            )

        with gr.Column(scale=3):
            with gr.Row():
                code_editor = gr.Code(
                    value=load_workflow(config_handler.current_workflow_file),
                    language="json",
                    interactive=True,
                    lines=5,
                    label=config_handler.current_workflow_file,
                )

                code_editor.change(
                    fn=save_workflow, inputs=[workflow_dropdown, code_editor]
                )

    workflow_dropdown.input(
        fn=update_editor_with_new_file,
        inputs=workflow_dropdown,
        outputs=code_editor,
    ).then(
        fn=update_checks_with_file_content,
        inputs=code_editor,
        outputs=[
            prompt_check,
            negative_prompt_check,
            model_check,
            vae_check,
            sampler_check,
            scheduler_check,
            steps_check,
            scale_check,
            clip_skip_check,
            width_check,
            height_check,
            user_avatar_check,
            char_avatar_check,
            seed_check,
        ],
    ).then(
        fn=lambda wkflw: validate_json_editor(wkflw),
        inputs=code_editor,
        outputs=valid_json_textbox,
    )

    code_editor.change(
        fn=update_checks_with_file_content,
        inputs=code_editor,
        outputs=[
            prompt_check,
            negative_prompt_check,
            model_check,
            vae_check,
            sampler_check,
            scheduler_check,
            steps_check,
            scale_check,
            clip_skip_check,
            width_check,
            height_check,
            user_avatar_check,
            char_avatar_check,
            seed_check,
        ],
    ).then(
        fn=lambda wkflw: validate_json_editor(wkflw),
        inputs=code_editor,
        outputs=valid_json_textbox,
    )
