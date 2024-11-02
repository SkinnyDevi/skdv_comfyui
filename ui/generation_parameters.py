import gradio as gr


def generation_parameters_ui():
    gr.Markdown("## Generation Parameters")

    with gr.Row():
        model_dropdown = gr.Dropdown(
            ["a.safetensors", "b.safetensors", "c.safetensors"], label="Model"
        )
        vae_dropdown = gr.Dropdown(["vae1", "vae2", "vae3"], label="VAE")

    with gr.Row():
        resolution_dropdown = gr.Dropdown(["832x1216"], label="Resolution Preset")

    with gr.Row():
        width_slider = gr.Slider(
            128, 4096, value=512, step=1, label="Width", interactive=True
        )
        height_slider = gr.Slider(
            128, 4096, value=512, step=1, label="Height", interactive=True
        )

    with gr.Row():
        sampler_dropdown = gr.Dropdown(["euler", "euler a"], label="Sampler")
        scheduler_dropdown = gr.Dropdown(["normal", "karras"], label="Scheduler")

    with gr.Row():
        sampler_steps_slider = gr.Slider(
            1, 150, value=20, label="Sampling Steps", interactive=True
        )
        cgc_scale_slider = gr.Slider(
            1, 30, value=7.0, step=0.5, label="CFG Scale", interactive=True
        )

    with gr.Row():
        clip_skip_slider = gr.Slider(
            -12,
            12,
            value=2,
            step=1,
            label="CLIP Skip",
            info="Use positive or negative CLIP skip depending on your workflow configuration.",
            interactive=True,
        )

    with gr.Row():
        with gr.Column():
            seed_input = gr.Number(
                value=-1,
                step=1,
                label="Seed",
                interactive=True,
                info="Use -1 for a random seed.",
            )
            previous_seed_display = gr.Number(
                value=-1, interactive=False, label="Last generated seed"
            )

        with gr.Column():
            random_seed_button = gr.Button(
                value="Random",
                size="lg",
                interactive=True,
                elem_classes=["skdv-full-height-btn"],
            )
            reuse_seed_button = gr.Button(
                value="Re-use last seed",
                size="lg",
                interactive=True,
                elem_classes=["skdv-full-height-btn"],
            )