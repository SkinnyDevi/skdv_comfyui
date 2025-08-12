import gradio as gr

import modules.ui as oobabooga_ui

from user_data.extensions.skdv_comfyui.comfyui.api import ComfyAPI
from user_data.extensions.skdv_comfyui.config.config_handler import ConfigHandler
from user_data.extensions.skdv_comfyui.config.dir_manager import DirManager
from user_data.extensions.skdv_comfyui.ui.shared import shared_ui

dir_manager = DirManager()
config_handler = ConfigHandler.setup()

CONNECTED_COLOR = "#1eab10"
DISCONNECTED_COLOR = "#b71717"
CONNECTING_COLOR = "#dfdb0c"

RESOLUTION_PRESETS = [
    "512x512",
    "512x768",
    "512x912",
    "576x768",
    "768x512",
    "768x576",
    "768x768",
    "912x512",
    "640x1536 (SDXL)",
    "768x1344 (SDXL)",
    "832x1216 (SDXL)",
    "896x1152 (SDXL)",
    "1152x896 (SDXL)",
    "1216x832 (SDXL)",
    "1344x768 (SDXL)",
    "1536x640 (SDXL)",
]


def load_local_workflows() -> list:
    return [file.name for file in dir_manager.get_local_workflows()]


def update_workflow_file(file_name: str):
    config_handler.set_current_workflow_file(file_name)
    gr.Info("Workflow Loaded")


def switch_to_random_seed():
    config_handler.set_seed(-1)
    return gr.update(value=-1)


def switch_to_fixed_seed(previous_seed: int):
    config_handler.set_seed(previous_seed)
    return gr.update(value=previous_seed)


def apply_resolution_preset(preset: str):
    if preset.count(" ") >= 1:
        preset = preset.split(" ")[0]

    resolution = preset.split("x")
    config_handler.set_width(int(resolution[0]))
    config_handler.set_height(int(resolution[1]))

    return gr.update(value=config_handler.width), gr.update(value=config_handler.height)


def ping_comfy_api():
    if not ComfyAPI.ping():
        gr.Error("Could not connect to ComfyUI")
        return (
            gr.update(color=DISCONNECTED_COLOR, value="Disconnected"),
            gr.update(choices=[]),
            gr.update(choices=[]),
            gr.update(choices=[]),
            gr.update(choices=[]),
        )

    parameters = ComfyAPI.get_generation_info()
    models = ComfyAPI.get_models(parameters)
    vaes = ComfyAPI.get_vaes(parameters)
    samplers = ComfyAPI.get_samplers(parameters)
    schedulers = ComfyAPI.get_schedulers(parameters)

    if config_handler.model == "":
        config_handler.set_model(models[0])

    if config_handler.vae == "":
        config_handler.set_vae(vaes[0])

    if config_handler.sampler == "":
        config_handler.set_sampler(samplers[0])

    if config_handler.scheduler == "":
        config_handler.set_scheduler(schedulers[0])

    gr.Info("Connected to ComfyUI")
    return (
        gr.update(color=CONNECTED_COLOR, value="Connected"),
        gr.update(
            choices=models,
            value=config_handler.model,
        ),
        gr.update(choices=vaes, value=config_handler.vae),
        gr.update(
            choices=samplers,
            value=config_handler.sampler,
        ),
        gr.update(
            choices=schedulers,
            value=config_handler.scheduler,
        ),
    )


def force_disconnect_api(new_url: str):
    config_handler.set_api_url(new_url)
    return gr.update(color=DISCONNECTED_COLOR, value="Disconnected")


def generation_parameters_ui():
    gr.Markdown("## Generation Parameters")

    with gr.Row():
        api_url_input = gr.Textbox(
            value=config_handler.api_url,
            max_lines=1,
            interactive=True,
            label="ComfyUI Endpoint",
            elem_classes=["slim-dropdown"],
            scale=3,
        )

        connect_button = gr.Button(
            "Connect",
            elem_id="skdv-connect-comfyapi",
            elem_classes=["skdv-button-height", "skdv-align-button-bottom"],
        )
        connection_status_label = gr.Label(
            "Disconnected",
            color=DISCONNECTED_COLOR,
            show_label=False,
            elem_classes=["skdv-connection-status", "skdv-align-button-bottom"],
        )

        api_url_input.change(
            fn=force_disconnect_api,
            inputs=api_url_input,
            outputs=connection_status_label,
        )

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

        workflow_dropdown.input(
            fn=lambda file: update_workflow_file(file), inputs=workflow_dropdown
        )

    with gr.Row():
        model_dropdown = gr.Dropdown(
            [],
            label="Model",
            interactive=True,
        )
        vae_dropdown = gr.Dropdown([], label="VAE", interactive=True)

        model_dropdown.input(
            fn=lambda model: config_handler.set_model(model), inputs=model_dropdown
        )
        vae_dropdown.input(
            fn=lambda vae: config_handler.set_vae(vae), inputs=vae_dropdown
        )

    with gr.Row():
        resolution_dropdown = gr.Dropdown(
            list(RESOLUTION_PRESETS),
            value=RESOLUTION_PRESETS[10],
            label="Resolution Preset",
            interactive=True,
        )

    with gr.Row():
        width_slider = gr.Slider(
            128,
            4096,
            value=config_handler.width,
            step=1,
            label="Width",
            interactive=True,
        )
        height_slider = gr.Slider(
            128,
            4096,
            value=config_handler.height,
            step=1,
            label="Height",
            interactive=True,
        )

        width_slider.release(
            fn=lambda width: config_handler.set_width(width), inputs=width_slider
        )
        height_slider.release(
            fn=lambda height: config_handler.set_height(height), inputs=height_slider
        )

    resolution_dropdown.input(
        fn=apply_resolution_preset,
        inputs=resolution_dropdown,
        outputs=[width_slider, height_slider],
    )

    with gr.Row():
        sampler_dropdown = gr.Dropdown([], label="Sampler", interactive=True)
        scheduler_dropdown = gr.Dropdown([], label="Scheduler", interactive=True)

        sampler_dropdown.input(
            fn=lambda sampler: config_handler.set_sampler(sampler),
            inputs=sampler_dropdown,
        )
        scheduler_dropdown.input(
            fn=lambda scheduler: config_handler.set_scheduler(scheduler),
            inputs=scheduler_dropdown,
        )

    with gr.Row():
        sampler_steps_slider = gr.Slider(
            1, 150, value=config_handler.steps, label="Sampling Steps", interactive=True
        )
        cfg_scale_slider = gr.Slider(
            1,
            30,
            value=config_handler.cfg_scale,
            step=0.5,
            label="CFG Scale",
            interactive=True,
        )

        sampler_steps_slider.release(
            fn=lambda steps: config_handler.set_steps(steps),
            inputs=sampler_steps_slider,
        )
        cfg_scale_slider.release(
            fn=lambda cfg: config_handler.set_cfg_scale(cfg), inputs=cfg_scale_slider
        )

    with gr.Row():
        clip_skip_slider = gr.Slider(
            -12,
            12,
            value=config_handler.clip_skip,
            step=1,
            label="CLIP Skip",
            info="Use positive or negative CLIP skip depending on your workflow configuration.",
            interactive=True,
        )

        clip_skip_slider.release(
            fn=lambda clip_skip: config_handler.set_clip_skip(clip_skip),
            inputs=clip_skip_slider,
        )

    with gr.Row():
        with gr.Column():
            seed_input = gr.Number(
                value=config_handler.seed,
                step=1,
                label="Seed",
                interactive=True,
                info="Use -1 for a random seed.",
            )
            shared_ui["previous-seed-display"] = gr.Number(
                value=config_handler.seed,
                interactive=False,
                label="Last generated seed",
            )

        with gr.Column(elem_id="skdv_seed_control_buttons"):
            random_seed_button = gr.Button(
                value="Random",
                size="lg",
                elem_classes=["skdv-full-height-btn"],
            )
            reuse_seed_button = gr.Button(
                value="Re-use last seed",
                size="lg",
                elem_classes=["skdv-full-height-btn"],
            )

            random_seed_button.click(fn=switch_to_random_seed, outputs=seed_input)
            reuse_seed_button.click(
                fn=switch_to_fixed_seed,
                inputs=shared_ui["previous-seed-display"],
                outputs=seed_input,
            )

    connect_button.click(
        fn=ping_comfy_api,
        outputs=[
            connection_status_label,
            model_dropdown,
            vae_dropdown,
            sampler_dropdown,
            scheduler_dropdown,
        ],
    )
