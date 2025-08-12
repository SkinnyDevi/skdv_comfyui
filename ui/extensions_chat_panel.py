from pathlib import Path
from typing import Literal
import gradio as gr
import html

import modules.chat as m_chat
import modules.utils as m_utils
from modules import text_generation
from modules import shared


from user_data.extensions.skdv_comfyui.textgen.generate import (
    generate_image_description_from_message,
)
from user_data.extensions.skdv_comfyui.textgen.utils import give_VRAM_priority_to
from user_data.extensions.skdv_comfyui.comfyui.api import ComfyAPI
from user_data.extensions.skdv_comfyui.comfyui.workflow import ComfyWorkflow
from user_data.extensions.skdv_comfyui.config.config_handler import (
    CharacterPrompt,
    ConfigHandler,
)
from user_data.extensions.skdv_comfyui.ui.shared import shared_ui

CONFIG_HANDLER = ConfigHandler.setup()

latest_image_tag = None
alt_image_text = None
prompt_editor_with_raw = False
main_prompt_to_generate = ""
generated_prompt_has_error = False


def history_is_blank(history: dict):
    return len(history["visible"]) == 0 or len(history["internal"]) == 0


def ping_comfyui():
    if not ComfyAPI.ping():
        gr.Warning("Disconnected from ComfyUI")


def remove_image_from_text(text: str):
    return text[: text.index("<img")] + text[text.index("skdv_comfyui/&gt;'/>") + 20 :]


def remove_alt_text_from_internal(text: str):
    return (
        text[: text.index("<skdv_comfyui")] + text[text.index("skdv_comfyui/>") + 14 :]
    )


def visible_text_contains_comfyui_image(text: str):
    try:
        return text.index("skdv_comfyui/&gt;'/>") >= 0
    except ValueError:
        return False


def internal_text_contains_comfyui_image(text: str):
    try:
        return text.index("<skdv_comfyui") >= 0
    except ValueError:
        return False


def create_image_tag(image_path: Path, alt_text: str):
    return f"<img src='file/{image_path.as_posix()}' class='skdv-generated-image' onclick='skdvExpandImage(this)' alt='{html.escape(alt_text)}'/>\n"


def set_prompt_raw(send: bool, allow_change: bool):
    if allow_change:
        return

    global prompt_editor_with_raw
    prompt_editor_with_raw = send


def get_character_prompt(
    prompt_type: Literal["positive", "negative"],
    character_name: str | None = None,
):
    if (character_name or shared.gradio["name2"]) == "Example":
        character_name = "Chiharu Yamada"

    character = CONFIG_HANDLER.get_character_prompts(
        character_name or shared.gradio["name2"].value
    )
    if character is None:
        return None

    return character.positive if prompt_type == "positive" else character.negative


def save_character_prompt(prompt: str, is_positive: bool, state: dict):
    previous = CONFIG_HANDLER.get_character_prompts(state["name2"])
    if previous is None:
        inverse_prompt = ""
    else:
        inverse_prompt = previous.negative if is_positive else previous.positive

    if is_positive:
        character = CharacterPrompt(state["name2"], prompt, inverse_prompt)
    else:
        character = CharacterPrompt(state["name2"], inverse_prompt, prompt)

    CONFIG_HANDLER.save_character_prompt(character)


def generate_image(
    character: str, positive: str, negative: str, prompt_confirmed=False
):
    if CONFIG_HANDLER.edit_prompt_before_generating and not prompt_confirmed:
        return gr.update()

    global latest_image_tag, alt_image_text, main_prompt_to_generate
    ping_comfyui()
    if not ComfyAPI.ping():
        return gr.update()

    if CONFIG_HANDLER.current_workflow_file is None:
        gr.Error("No workflow selected")
        raise ValueError("No workflow selected")

    if CONFIG_HANDLER.unload_text_model_before_generating:
        give_VRAM_priority_to("imagegen")

    latest_image_tag = None
    alt_image_text = None

    if positive == "":
        alt_prompt = main_prompt_to_generate
    else:
        alt_prompt = positive + ", " + main_prompt_to_generate

    workflow = ComfyWorkflow(CONFIG_HANDLER.current_workflow_file)
    workflow.set_positive_prompt(alt_prompt)
    workflow.set_negative_prompt(negative)
    workflow.set_character(character)

    required_gen_fields = [
        CONFIG_HANDLER.model,
        CONFIG_HANDLER.sampler,
        CONFIG_HANDLER.scheduler,
    ]
    if any(v is None for v in required_gen_fields):
        gr.Warning(
            "Model, Sampler and Scheduler need to be selected before generation."
        )
        return gr.update()

    try:
        image_path, seed = ComfyAPI.generate(workflow)
    except ValueError as e:
        print(e)
        gr.Warning("The workflow is not valid. Please check the editor for more info.")
        return gr.update()

    alt_image_text = f"<skdv_comfyui seed: {seed}, prompt: {alt_prompt} skdv_comfyui/>"
    latest_image_tag = create_image_tag(image_path, alt_image_text)
    return gr.update(value=seed)


def send_image_message(
    image_tag: str | None, history: dict[str, list[list[str]]], state: dict
):
    new_history = history

    if image_tag is None:
        return history

    if latest_image_tag is None or alt_image_text is None:
        return history

    if history_is_blank(history):
        new_history = m_chat.load_latest_history(state)

    new_history["visible"][-1][1] += image_tag
    # new_history["internal"][-1][1] += alt_image_text
    return new_history


def remove_image_from_last_message(history: dict[str, list[list[str]]]):
    new_history = history

    if history_is_blank(new_history):
        return new_history

    if internal_text_contains_comfyui_image(new_history["internal"][-1][1]):
        new_history["internal"][-1][1] = remove_alt_text_from_internal(
            new_history["internal"][-1][1]
        )

    if visible_text_contains_comfyui_image(new_history["visible"][-1][1]):
        new_history["visible"][-1][1] = remove_image_from_text(
            new_history["visible"][-1][1]
        )

    return new_history


def handle_remove_latest_image(
    chat_id: str, chat_html: str, history: dict[str, list[list[str]]], state: dict
):
    new_history = history
    html = chat_html

    if chat_id is not None:
        new_history = remove_image_from_last_message(new_history)
        m_chat.save_history(
            new_history, chat_id, state["character_menu"], state["mode"]
        )

        html = m_chat.redraw_html(
            history,
            state["name1"],
            state["name2"],
            state["mode"],
            state["chat_style"],
            state["character_menu"],
        )

    return [new_history, html]


def handle_send_image_message_click(
    text: str,
    chat_id: str,
    chat_html: str,
    history: dict[str, list[list[str]]],
    state: dict,
    prompt_confirmed=False,
):
    if CONFIG_HANDLER.edit_prompt_before_generating and not prompt_confirmed:
        return gr.update(), gr.update(), gr.update()

    new_history = history
    html = chat_html

    if latest_image_tag is not None and alt_image_text is not None:
        new_history = send_image_message(text, new_history, state)
        m_chat.save_history(
            new_history, chat_id, state["character_menu"], state["mode"]
        )

        html = m_chat.redraw_html(
            history,
            state["name1"],
            state["name2"],
            state["mode"],
            state["chat_style"],
            state["character_menu"],
        )

    if CONFIG_HANDLER.unload_text_model_before_generating:
        try:
            give_VRAM_priority_to("textgen")
        except ValueError:
            print(
                "Failed to give VRAM priority to textgen. Did you have a model loaded before generating an image?"
            )

    return [new_history, html, ""]


def change_main_prompt(new_prompt: str):
    global main_prompt_to_generate

    main_prompt_to_generate = new_prompt


def generate_positive_prompt_from_message(
    history: dict,
    state: dict,
    return_raw=False,
    confirms_prompt=False,
    regenerate=False,
):
    global main_prompt_to_generate, generated_prompt_has_error

    generated_prompt_has_error = False

    if regenerate:
        return main_prompt_to_generate

    if confirms_prompt:
        return gr.update()

    global prompt_editor_with_raw

    if return_raw or prompt_editor_with_raw:
        return history["internal"][-1][1]

    try:
        generated_prompt = generate_image_description_from_message(
            history["internal"][-1][1], state
        )
        change_main_prompt(generated_prompt)
    except ValueError as e:
        gr.Warning(e)
        generated_prompt_has_error = True
        generated_prompt = ""

    return generated_prompt


def show_prompt_editor_box(confirms_prompt=False):
    global generated_prompt_has_error
    return (
        not confirms_prompt
        and CONFIG_HANDLER.edit_prompt_before_generating
        and not generated_prompt_has_error
    )


def mount_generate_events(
    btn_component: gr.Button,
    regenerate_event=False,
    raw_prompt=False,
    confirms_prompt=False,
):
    event_dependencies = (
        btn_component.click(
            lambda: gr.update(visible=True),
            outputs=shared_ui["generation_dots"],
            show_progress="hidden",
        )
        .then(
            fn=lambda: set_prompt_raw(raw_prompt, regenerate_event or confirms_prompt)
        )
        .then(
            fn=lambda prompt, state: generate_positive_prompt_from_message(
                prompt,
                state,
                return_raw=raw_prompt,
                confirms_prompt=confirms_prompt,
                regenerate=regenerate_event,
            ),
            inputs=m_utils.gradio("history", "interface_state"),
            outputs=[shared_ui["prompts_textarea"]],
        )
    )

    if regenerate_event:
        event_dependencies = event_dependencies.then(
            fn=handle_remove_latest_image,
            inputs=m_utils.gradio("unique_id", "display", "history", "interface_state"),
            outputs=m_utils.gradio("history", "display"),
            show_progress="hidden",
        )

    event_dependencies.then(
        fn=lambda chara, pos, neg: generate_image(
            chara, pos, neg, prompt_confirmed=confirms_prompt
        ),
        inputs=[
            shared.gradio["character_menu"],
            shared_ui["character_positive_prompt_input"],
            shared_ui["character_negative_prompt_input"],
        ],
        outputs=shared_ui["previous-seed-display"],
        show_progress="hidden",
    ).then(
        fn=lambda: (latest_image_tag),
        outputs=m_utils.gradio("Chat input"),
        show_progress="hidden",
    ).then(
        fn=lambda chat_in, uid, dis, his, state: handle_send_image_message_click(
            chat_in,
            uid,
            dis,
            his,
            state,
            prompt_confirmed=confirms_prompt,
        ),
        inputs=m_utils.gradio(
            "Chat input", "unique_id", "display", "history", "interface_state"
        ),
        outputs=m_utils.gradio("history", "display", "Chat input"),
        show_progress="hidden",
    ).then(
        fn=lambda: gr.update(visible=False),
        outputs=shared_ui["generation_dots"],
        show_progress="hidden",
    ).then(
        fn=lambda: gr.update(visible=show_prompt_editor_box(confirms_prompt)),
        outputs=shared_ui["confirm_prompts_box"],
    )


def confirm_prompts_for_generation_dialog():
    with gr.Box(
        visible=False, elem_classes="file-saver", elem_id="skdv_prompt_editor"
    ) as shared_ui["confirm_prompts_box"]:
        shared_ui["prompts_textarea"] = gr.TextArea(
            label="Edit the prompt before generating:",
            placeholder="Prompt to generate...",
        )

        shared_ui["prompts_textarea"].change(
            fn=lambda prompt: change_main_prompt(prompt),
            inputs=[shared_ui["prompts_textarea"]],
        )

        with gr.Row(elem_id="skdv_confirm_prompts_buttons"):
            cancel_generation = gr.Button("Cancel", elem_classes="small-button")
            confirm_prompt_generate = gr.Button(
                "Generate",
                elem_classes="small-button",
                variant="primary",
            )

            confirm_prompt_generate.click(
                lambda: gr.update(visible=False),
                None,
                shared_ui["confirm_prompts_box"],
            )

            cancel_generation.click(
                lambda: gr.update(visible=False),
                None,
                shared_ui["confirm_prompts_box"],
            )

    return confirm_prompt_generate


def comfyui_hover_menu_buttons_ui():
    hover_menu_generate_button = gr.Button(
        "Gen. image: last message", elem_id="skdv_comfyui_button_generate"
    )

    hover_menu_generate_raw_button = gr.Button(
        "Gen. image: raw last message", elem_id="skdv_comfyui_button_generate_raw"
    )

    hover_menu_regenerate_button = gr.Button(
        "Re-gen. last image", elem_id="skdv_comfyui_button_regenerate"
    )

    hover_menu_remove_image_button = gr.Button(
        "Remove last image", elem_id="skdv_comfyui_button_remove_image"
    )

    hover_menu_stop_prompt_generation = gr.Button(
        "Stop image prompt generation",
        elem_id="skdv_comfyui_button_stop_prompt_generation",
    )

    mount_generate_events(hover_menu_generate_button)
    mount_generate_events(hover_menu_generate_raw_button, raw_prompt=True)
    mount_generate_events(hover_menu_regenerate_button, regenerate_event=True)

    hover_menu_remove_image_button.click(
        fn=handle_remove_latest_image,
        inputs=m_utils.gradio("unique_id", "display", "history", "interface_state"),
        outputs=m_utils.gradio("history", "display"),
        show_progress="hidden",
    )

    hover_menu_stop_prompt_generation.click(fn=text_generation.stop_everything_event)


def comfyui_chat_panel_ui():
    shared_ui["generation_dots"] = gr.HTML(
        value='<div class="typing skdv-typing-dots"><span></span><span class="dot1"></span><span class="dot2"></span></div>',
        label="typing",
        elem_id="skdv_comfyui_generating_dots",
        visible=False,
    )

    confirm_generation_dialog_button = confirm_prompts_for_generation_dialog()

    with gr.Accordion(
        "ComfyUI Generation Parameters",
        open=False,
        elem_id="skdv_comfyui_generation_panel",
    ):
        unload_text_model_checkbox = gr.Checkbox(
            value=CONFIG_HANDLER.unload_text_model_before_generating,
            label="Unload text model before generating image",
            interactive=True,
        )

        edit_prompt_before_generation_checkbox = gr.Checkbox(
            value=CONFIG_HANDLER.edit_prompt_before_generating,
            label="Edit prompt before generating image",
            interactive=True,
        )

        character_selected = gr.Markdown(
            value="### Editing prompts for: *None*",
        )
        shared_ui["character_positive_prompt_input"] = gr.TextArea(
            value=get_character_prompt("positive"),
            placeholder="glasses, uniform, ...",
            interactive=True,
            label="Positive Prompt",
            lines=3,
        )
        shared_ui["character_negative_prompt_input"] = gr.TextArea(
            value=get_character_prompt("negative"),
            placeholder="black hair, jeans, ...",
            interactive=True,
            label="Negative Prompt",
            lines=3,
        )

        unload_text_model_checkbox.input(
            fn=lambda checked: CONFIG_HANDLER.set_unload_text_model_before_generating(
                checked
            ),
            inputs=unload_text_model_checkbox,
        )

        edit_prompt_before_generation_checkbox.input(
            fn=lambda checked: CONFIG_HANDLER.set_edit_prompt_before_generating(
                checked
            ),
            inputs=edit_prompt_before_generation_checkbox,
        )

        shared.gradio["name2"].change(
            fn=lambda name: gr.update(value=f"### Editing prompts for: *{name}*"),
            inputs=shared.gradio["character_menu"],
            outputs=character_selected,
        ).then(
            fn=lambda chara: (
                get_character_prompt("positive", chara),
                get_character_prompt("negative", chara),
            ),
            inputs=shared.gradio["character_menu"],
            outputs=[
                shared_ui["character_positive_prompt_input"],
                shared_ui["character_negative_prompt_input"],
            ],
        )

        shared_ui["character_positive_prompt_input"].change(
            fn=lambda prompt, state: save_character_prompt(prompt, True, state),
            inputs=[shared_ui["character_positive_prompt_input"]]
            + m_utils.gradio("interface_state"),
        )
        shared_ui["character_negative_prompt_input"].change(
            fn=lambda prompt, state: save_character_prompt(prompt, False, state),
            inputs=[shared_ui["character_negative_prompt_input"]]
            + m_utils.gradio("interface_state"),
        )

    mount_generate_events(confirm_generation_dialog_button, confirms_prompt=True)
