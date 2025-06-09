import urllib.request
import urllib.parse
import json
from urllib.parse import urlparse

from langflow.custom import Component
from langflow.io import DropdownInput, IntInput, MessageTextInput, Output, BoolInput
from langflow.schema import Data, DataFrame


class SearchRetrievalComponent(Component):
    display_name = "Search Retrieval"
    description = "Search and retrieve data from custom knowledge base API"
    icon = "Search"

    inputs = [
        MessageTextInput(
            name="ip_address",
            display_name="IP Address",
            info="The IP address of your API server (e.g., '192.168.1.100')",
            value="IP_PLACEHOLD",
        ),
        MessageTextInput(
            name="kb_name",
            display_name="Knowledge Base Name",
            info="The name of the knowledge base",
            tool_mode=True,
        ),
        MessageTextInput(
            name="search_query",
            display_name="Search Query",
            info="The text query to search for",
            tool_mode=True,
        ),
        MessageTextInput(
            name="selected_tables",
            display_name="Selected Tables",
            info="JSON string of selected tables in format: [['texts_table_name', 'images_table_name', 'tables_table_name'], ...]",
            tool_mode=True,
        ),
        DropdownInput(
            name="return_format",
            display_name="Return Format",
            info="The format to return results in",
            options=["pd", "pl", "arrow", "raw"],
            value="pd",
        ),
        IntInput(
            name="limit",
            display_name="Max Results",
            info="Maximum number of results to return",
            value=10,
        ),
        IntInput(
            name="top_k",
            display_name="Top K",
            info="Top K results for text search (used in conditions.text.topn)",
            value=5,
        ),
        BoolInput(
            name="do_image_search",
            display_name="Image Search",
            info="Enable image search",
            value=False,
        ),
        BoolInput(
            name="do_coord_search",
            display_name="Coordinate Search",
            info="Enable coordinate search",
            value=False,
        ),
    ]

    outputs = [
        Output(display_name="Data", name="data", method="search_knowledge_base"),
        Output(display_name="DataFrame", name="dataframe", method="as_dataframe"),
    ]

    def build_search_url(self) -> str:
        """Build the API URL for search endpoint."""
        port = 14514
        return f"http://{self.ip_address}:{port}/search"

    def search_knowledge_base(self) -> list[Data]:
        """Search the knowledge base."""
        try:
            url = self.build_search_url()
            
            # Parse selected tables from input (expecting JSON string)
            try:
                if isinstance(self.selected_tables, str):
                    selected_tables = json.loads(self.selected_tables)
                else:
                    selected_tables = self.selected_tables
            except (json.JSONDecodeError, TypeError):
                # If parsing fails, use default empty list
                selected_tables = []
            
            # Prepare search payload based on your API spec (matching kb.py structure)
            search_payload = {
                "kb_name": self.kb_name,
                "tables": selected_tables,  # Use the selected tables structure
                "select_cols": ["*"],
                "conditions": {
                    "text": [
                        {
                            "field": "text", 
                            "query": self.search_query, 
                            "topn": self.top_k
                        }
                    ]
                },
                "do_image_search": self.do_image_search,
                "do_coord_search": self.do_coord_search,
                "limit": self.top_k,
                "return_format": self.return_format
            }
            
            # Validate URL
            parsed_url = urlparse(url)
            if parsed_url.scheme not in {"http", "https"}:
                raise ValueError(f"Invalid URL scheme: {parsed_url.scheme}")
            
            # Make POST request
            data = json.dumps(search_payload).encode('utf-8')
            request = urllib.request.Request(url, data=data, method='POST')
            request.add_header('Content-Type', 'application/json')
            
            with urllib.request.urlopen(request) as response:
                response_text = response.read().decode("utf-8")
                result = json.loads(response_text)
                
            if result.get("status") == "success":
                search_results = result.get("tables", {})
                results = [Data(data={"search_results": search_results, "operation": "search"})]
                self.status = results
                return results
            else:
                error_msg = f"API error: {result.get('message', 'Unknown error')}"
                error_data = Data(data={"error": error_msg})
                self.status = error_data
                return [error_data]
                
        except Exception as e:
            error_data = Data(data={"error": f"Request error: {str(e)}"})
            self.status = error_data
            return [error_data]

    def as_dataframe(self) -> DataFrame:
        """Convert the search results to a DataFrame.

        Returns:
            DataFrame: A DataFrame containing the search results.
        """
        data = self.search_knowledge_base()
        if isinstance(data, list):
            return DataFrame(data=[d.data for d in data])
        return DataFrame(data=[data.data])
