from typing import Any
import requests

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from langflow.base.models.anthropic_constants import ANTHROPIC_MODELS
from langflow.base.models.model import LCModelComponent
from langflow.base.models.openai_constants import OPENAI_MODEL_NAMES
from langflow.field_typing import LanguageModel
from langflow.field_typing.range_spec import RangeSpec
from langflow.inputs.inputs import BoolInput
from langflow.io import DropdownInput, MessageTextInput, SecretStrInput, SliderInput
from langflow.schema.dotdict import dotdict

# Fetch OpenRouter models
def get_openrouter_models():
    try:
        response = requests.get("https://openrouter.ai/api/v1/models")
        models_data = response.json()
        return [model["id"] for model in models_data.get("data", [])]
    except:
        # Fallback to some common OpenRouter models if API call fails
        return [
            "anthropic/claude-3-sonnet",
            "anthropic/claude-3-haiku",
            "openai/gpt-4",
            "openai/gpt-3.5-turbo",
            "meta-llama/llama-2-70b-chat"
        ]

OPENROUTER_MODEL_NAMES = get_openrouter_models()


class LanguageModelComponent(LCModelComponent):
    display_name = "Language Model"
    description = "Runs a language model given a specified provider. "
    icon = "brain-circuit"
    category = "models"
    priority = 0  # Set priority to 0 to make it appear first

    inputs = [
        DropdownInput(
            name="provider",
            display_name="Model Provider",
            options=["OpenAI", "Anthropic", "OpenRouter"],
            value="OpenAI",
            info="Select the model provider",
            real_time_refresh=True,
            options_metadata=[{"icon": "OpenAI"}, {"icon": "Anthropic"}, {"icon": "OpenRouter"}],
        ),
        DropdownInput(
            name="model_name",
            display_name="Model Name",
            options=OPENAI_MODEL_NAMES,
            value=OPENAI_MODEL_NAMES[0],
            info="Select the model to use",
        ),
        SecretStrInput(
            name="api_key",
            display_name="OpenAI API Key",
            info="Model Provider API key",
            required=False,
            show=True,
            real_time_refresh=True,
        ),
        MessageTextInput(
            name="input_value",
            display_name="Input",
            info="The input text to send to the model",
        ),
        MessageTextInput(
            name="system_message",
            display_name="System Message",
            info="A system message that helps set the behavior of the assistant",
            advanced=True,
        ),
        BoolInput(
            name="stream",
            display_name="Stream",
            info="Whether to stream the response",
            value=False,
            advanced=True,
        ),
        SliderInput(
            name="temperature",
            display_name="Temperature",
            value=0.1,
            range_spec=RangeSpec(min=0, max=1, step=0.01),
            show=True,
        ),
    ]

    def build_model(self) -> LanguageModel:
        provider = self.provider
        model_name = self.model_name
        temperature = self.temperature
        stream = self.stream

        if provider == "OpenAI":
            if not self.api_key:
                msg = "OpenAI API key is required when using OpenAI provider"
                raise ValueError(msg)
            return ChatOpenAI(
                model_name=model_name,
                temperature=temperature,
                streaming=stream,
                openai_api_key=self.api_key,
            )
        if provider == "Anthropic":
            if not self.api_key:
                msg = "Anthropic API key is required when using Anthropic provider"
                raise ValueError(msg)
            return ChatAnthropic(
                model=model_name,
                temperature=temperature,
                streaming=stream,
                anthropic_api_key=self.api_key,
            )
        if provider == "OpenRouter":
            if not self.api_key:
                msg = "OpenRouter API key is required when using OpenRouter provider"
                raise ValueError(msg)
            return ChatOpenAI(
                model_name=model_name,
                temperature=temperature,
                streaming=stream,
                openai_api_key=self.api_key,
                base_url="https://openrouter.ai/api/v1",
            )
        msg = f"Unknown provider: {provider}"
        raise ValueError(msg)

    def update_build_config(self, build_config: dotdict, field_value: Any, field_name: str | None = None) -> dotdict:
        if field_name == "provider":
            if field_value == "OpenAI":
                build_config["model_name"]["options"] = OPENAI_MODEL_NAMES
                build_config["model_name"]["value"] = OPENAI_MODEL_NAMES[0]
                build_config["api_key"]["display_name"] = "OpenAI API Key"
            elif field_value == "Anthropic":
                build_config["model_name"]["options"] = ANTHROPIC_MODELS
                build_config["model_name"]["value"] = ANTHROPIC_MODELS[0]
                build_config["api_key"]["display_name"] = "Anthropic API Key"
            elif field_value == "OpenRouter":
                build_config["model_name"]["options"] = OPENROUTER_MODEL_NAMES
                build_config["model_name"]["value"] = OPENROUTER_MODEL_NAMES[0]
                build_config["api_key"]["display_name"] = "OpenRouter API Key"
        return build_config
