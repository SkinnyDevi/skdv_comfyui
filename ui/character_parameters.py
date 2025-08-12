import gradio as gr

from user_data.extensions.skdv_comfyui.config.config_handler import ConfigHandler

config_handler = ConfigHandler.setup()


def character_parameters_ui():
    gr.Markdown("""
    ## Shared character prompts

    Use this section to establish quality tokens that can be shared for all character image generations.
    """)

    shared_positive_prompt_input = gr.TextArea(
        value=config_handler.shared_positive_prompt,
        placeholder="best quality, masterpiece, ...",
        interactive=True,
        label="Shared Positive Prompt",
        lines=3,
    )
    shared_negative_prompt_input = gr.TextArea(
        value=config_handler.shared_negative_prompt,
        placeholder="lowres, bad hands, text, ...",
        interactive=True,
        label="Shared Negative Prompt",
        lines=3,
    )

    shared_positive_prompt_input.change(
        fn=lambda prompt: config_handler.set_shared_positive_prompt(prompt),
        inputs=shared_positive_prompt_input,
    )
    shared_negative_prompt_input.change(
        fn=lambda prompt: config_handler.set_shared_negative_prompt(prompt),
        inputs=shared_negative_prompt_input,
    )
