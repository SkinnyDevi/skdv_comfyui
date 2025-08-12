import gradio as gr
import json

from pathlib import Path
from gradio.utils import NamedString

from user_data.extensions.skdv_comfyui.config.config_handler import ConfigHandler
from user_data.extensions.skdv_comfyui.config.dir_manager import DirManager

config_handler = ConfigHandler.setup()
dir_manager = DirManager()


def parse_json_file(file_path: NamedString) -> dict:
    try:
        with open(file_path, "r") as file:
            return json.loads(file.read())
    except json.JSONDecodeError or UnicodeDecodeError:
        return {"error": f"Invalid JSON file: '{file_path}'"}


def on_workflow_upload(file_paths: list[NamedString] | None):
    if file_paths is None:
        return gr.update(interactive=False, variant="stop")

    for file in file_paths:
        parsed = parse_json_file(file)
        if "error" in parsed.keys():
            return gr.update(interactive=False, variant="stop")

    return gr.update(interactive=True, variant="primary")


def on_workflow_import(file_paths: list[NamedString] | None):
    if file_paths is None:
        return gr.update(variant="stop", interactive=False)

    for file in file_paths:
        parsed = parse_json_file(file)
        if "error" in parsed.keys():
            return gr.update(interactive=False, variant="stop")

        dir_manager.save_to_workflows(Path(file.name).name, json.dumps(parsed))

    gr.Info("Workflow(s) saved.")
    return gr.update(interactive=False, variant="stop"), gr.update(value=[])


def workflow_importer_ui():
    gr.Markdown("## Import Workflow")

    workflow_upload = gr.File(
        type="filepath", file_types=[".json"], file_count="multiple", label="JSON File"
    )
    import_button = gr.Button("Import Workflow", interactive=False, variant="stop")

    workflow_upload.upload(
        fn=on_workflow_upload,
        inputs=workflow_upload,
        outputs=[import_button],
    )

    import_button.click(
        fn=on_workflow_import,
        inputs=workflow_upload,
        outputs=[import_button, workflow_upload],
    )
