# curl -X GET "https://data-api.binance.vision/api/v3/depth?symbol=BTCUSDT&limit=3"

import requests
from typing import Dict, Any

from langflow.custom import Component
from langflow.inputs import MessageTextInput, IntInput
from langflow.io import Output
from langflow.schema import Data


class BinanceDepthComponent(Component):
    display_name = "Binance Depth"
    description = "Fetch order book depth data from Binance API for a given trading pair."
    icon = "chart-line"

    inputs = [
        MessageTextInput(
            name="symbol",
            display_name="Symbol",
            info="Trading pair symbol (e.g., 'BTCUSDT', 'ETHUSDT').",
            value="BTCUSDT",
            tool_mode=True,
        ),
        IntInput(
            name="limit",
            display_name="Limit",
            info="Number of orders to return (5, 10, 20, 50, 100, 500, 1000, 5000).",
            value=5,
        ),
    ]

    outputs = [
        Output(display_name="Data", name="result", type_=Data, method="fetch_depth"),
    ]

    def fetch_depth(self) -> Data:
        """Fetch order book depth data from Binance API."""
        try:
            url = "https://data-api.binance.vision/api/v3/depth"
            params = {
                "symbol": self.symbol.upper(),
                "limit": self.limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Format the response for better readability
            formatted_data = {
                "symbol": self.symbol.upper(),
                "bids": data.get("bids", []),
                "asks": data.get("asks", []),
                "lastUpdateId": data.get("lastUpdateId")
            }
            
            self.log(f"Successfully fetched depth data for {self.symbol.upper()}")
            self.status = f"Success: {self.symbol.upper()} depth data retrieved"
            
            return Data(data=formatted_data)
            
        except requests.exceptions.RequestException as e:
            error_message = f"Network error: {str(e)}"
            self.status = error_message
            return Data(data={"error": error_message, "symbol": self.symbol})
            
        except ValueError as e:
            error_message = f"JSON decode error: {str(e)}"
            self.status = error_message
            return Data(data={"error": error_message, "symbol": self.symbol})
            
        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            self.status = error_message
            return Data(data={"error": error_message, "symbol": self.symbol})

    def build(self):
        """Return the main fetch function."""
        return self.fetch_depth
