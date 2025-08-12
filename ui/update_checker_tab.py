import gradio as gr

from user_data.extensions.skdv_comfyui.config.config_handler import ConfigHandler
from user_data.extensions.skdv_comfyui.config.update_manager import ExtUpdateManager

from user_data.extensions.skdv_comfyui.config.legacy_github import (
    clone_or_pull_repository,
)

CONFIG_HANLDER = ConfigHandler.setup()


def create_ext_updater():
    update_btn = gr.Button(
        "There is an update available. Click here to download",
        variant="primary",
        elem_classes=["skdv-download-update-btn"],
    )
    status = gr.Markdown()
    repo = gr.Textbox(
        visible=False,
        value="https://github.com/SkinnyDevi/skdv_comfyui",
    )
    restart_webui = gr.Markdown(
        "Please restart your WebUI using the restart button in the Sessions tab.",
        elem_classes=["skdv-ext-update"],
        visible=False,
    )

    update_btn.click(
        clone_or_pull_repository,
        repo,
        status,
        show_progress=True,
    ).then(
        lambda: (gr.update(visible=False), gr.update(visible=True)),
        None,
        [status, restart_webui],
    )


def update_checker_ui():
    if ExtUpdateManager.check_for_updates(CONFIG_HANLDER):
        create_ext_updater()
    else:
        gr.Button(
            "Extension is up to date.",
            elem_classes=["skdv-download-update-btn"],
            interactive=False,
        )

    gr.Markdown(
        f"SKDV ComfyUI Image Generation - Version {CONFIG_HANLDER.version}",
        elem_classes=["skdv-ext-version"],
    )
    gr.Markdown(
        "Have any issues or feature request? Report them [here](https://github.com/SkinnyDevi/skdv_comfyui/issues/new/choose).",
        elem_classes=["skdv-ext-version"],
    )
    gr.Markdown(
        "Want to support my development? [Donate](https://paypal.me/skinnydevi) to me here! Thank you! :)",
        elem_classes=["skdv-ext-version"],
    )
