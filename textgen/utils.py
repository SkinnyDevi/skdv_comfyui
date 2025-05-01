#
# Implements the model unloader from the sd_api_pictures extension
#
import torch

from typing import Literal
from modules import shared

from modules.models import load_model
from modules.torch_utils import clear_torch_cache

from extensions.skdv_comfyui.comfyui.api import ComfyAPI

torch._C._jit_set_profiling_mode(False)


def unload_model():
    shared.model = shared.tokenizer = None
    shared.model_dirty_from_training = False
    clear_torch_cache()


def reload_model():
    if shared.model_name is None:
        print("[skdv_comfyui] No model loaded previously, skipping model re-load.")
        return

    shared.model, shared.tokenizer = load_model(shared.model_name)


def textgen_model_is_loaded():
    return shared.model is not None


def give_VRAM_priority_to(actor: Literal["textgen", "imagegen"]):
    global shared

    match actor:
        case "textgen":
            print("[skdv_comfyui] Unloading ComfyUI...")
            if ComfyAPI.unload():
                print("[skdv_comfyui] Unloaded ComfyUI.")
            else:
                print(
                    "[skdv_comfyui] Could not unload ComfyUI. Please check your ComfyUI instance."
                )

            print("[skdv_comfyui] Reloading text model...")
            if not textgen_model_is_loaded():
                reload_model()

            print("[skdv_comfyui] Reloading complete.")
        case "imagegen":
            print("[skdv_comfyui] Unloading text model...")
            if textgen_model_is_loaded():
                unload_model()

            print("[skdv_comfyui] Unloading complete.")
