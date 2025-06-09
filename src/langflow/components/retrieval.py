# This file has been deprecated. Please use:
# - search_retrieval.py for /search API functionality
# - list_tables.py for /list_tables/{kb_owner}/{kb_name} API functionality

import urllib.request
import urllib.parse
import json
from urllib.parse import urlparse

from langflow.custom import Component
from langflow.io import MessageTextInput, Output
from langflow.schema import Data, DataFrame


class DeprecatedRetrievalComponent(Component):
    display_name = "Deprecated Retrieval"
    description = "This component is deprecated. Use search_retrieval.py or list_tables.py instead."
    icon = "Warning"

    inputs = [
        MessageTextInput(
            name="message",
            display_name="Deprecation Notice",
            info="This component is deprecated. Use search_retrieval.py or list_tables.py instead.",
            value="Component deprecated - use separate components",
        ),
    ]

    outputs = [
        Output(display_name="Data", name="data", method="deprecated_warning"),
    ]

    def deprecated_warning(self) -> list[Data]:
        """Return deprecation warning."""
        warning_data = Data(data={
            "warning": "This component is deprecated.",
            "message": "Please use search_retrieval.py for /search API or list_tables.py for /list_tables API",
            "new_components": [
                "search_retrieval.py - for /search endpoint",
                "list_tables.py - for /list_tables/{kb_owner}/{kb_name} endpoint"
            ]
        })
        self.status = warning_data
        return [warning_data]
