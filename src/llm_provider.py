import google.generativeai as genai

from config import get_gemini_api_key, get_gemini_model

_selected_model: str | None = None


def list_models() -> list[str]:
    """
    Lists models available via Gemini SDK.

    Returns:
        models (list[str]): Sorted list of model names.
    """
    genai.configure(api_key=get_gemini_api_key())
    
    models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            models.append(m.name.replace("models/", ""))
    
    return sorted(models)


def select_model(model: str) -> None:
    """
    Sets the model to use for all subsequent generate_text calls.

    Args:
        model (str): A Gemini model name.
    """
    global _selected_model
    _selected_model = model


def get_active_model() -> str | None:
    """
    Returns the currently selected model, or None if none has been selected.
    """
    return _selected_model


def generate_text(
    prompt: str, 
    model_name: str | None = None, 
    system_instruction: str | None = None, 
    temperature: float = 1.0, 
    thinking: bool = False
) -> str:
    """
    Generates text using Google Gemini Mode.

    Args:
        prompt (str): User prompt
        model_name (str): Optional model name override
        system_instruction (str): Optional system instruction
        temperature (float): Optional temperature override (default 1.0)
        thinking (bool): Enable Gemini 3.x thinking feature

    Returns:
        response (str): Generated text
    """
    api_key = get_gemini_api_key()
    genai.configure(api_key=api_key)
    
    # Padrão da skill dinâmico para família 3.x
    model = model_name or _selected_model or get_gemini_model()

    generative_model = genai.GenerativeModel(model, system_instruction=system_instruction)
    
    from typing import Any
    gen_config: dict[str, Any] = {"temperature": temperature}
    if thinking:
        # Configuração para suportar familia Gemini 3.x e flash-thinking-preview
        gen_config["thinking"] = True

    response = generative_model.generate_content(
        prompt,
        generation_config=gen_config
    )
    
    return response.text.strip()

