import urllib.request
import urllib.parse
import json
from urllib.parse import urlparse

from langflow.custom import Component
from langflow.io import MessageTextInput, Output
from langflow.schema import Data, DataFrame


class ListTablesComponent(Component):
    display_name = "List Tables"
    description = "List all tables from custom knowledge base API"
    icon = "List"

    inputs = [
        MessageTextInput(
            name="ip_address",
            display_name="IP Address",
            info="The IP address of your API server (e.g., '192.168.1.100')",
            value="IP_PLACEHOLD",
        ),
        MessageTextInput(
            name="kb_owner",
            display_name="Knowledge Base Owner",
            info="The owner of the knowledge base",
            tool_mode=True,
        ),
        MessageTextInput(
            name="kb_name",
            display_name="Knowledge Base Name",
            info="The name of the knowledge base",
            tool_mode=True,
        ),
    ]

    outputs = [
        Output(display_name="Data", name="data", method="list_tables"),
        Output(display_name="DataFrame", name="dataframe", method="as_dataframe"),
    ]

    def build_list_tables_url(self) -> str:
        """Build the API URL for list_tables endpoint."""
        port = 14514
        return f"http://{self.ip_address}:{port}/list_tables/{self.kb_owner}/{self.kb_name}"

    def list_tables(self) -> list[Data]:
        """List all tables for the given knowledge base."""
        try:
            url = self.build_list_tables_url()
            
            # Validate URL
            parsed_url = urlparse(url)
            if parsed_url.scheme not in {"http", "https"}:
                raise ValueError(f"Invalid URL scheme: {parsed_url.scheme}")
            
            # Make GET request
            request = urllib.request.Request(url, method='GET')
            request.add_header('Content-Type', 'application/json')
            
            with urllib.request.urlopen(request) as response:
                response_text = response.read().decode("utf-8")
                result = json.loads(response_text)
                
            if result.get("status") == "success":
                tables = result.get("tables", [])
                results = [Data(data={"tables": tables, "operation": "list_tables"})]
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
        """Convert the list tables results to a DataFrame.

        Returns:
            DataFrame: A DataFrame containing the tables information.
        """
        data = self.list_tables()
        if isinstance(data, list):
            return DataFrame(data=[d.data for d in data])
        return DataFrame(data=[data.data])
