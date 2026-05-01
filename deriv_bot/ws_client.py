import json
import logging
import asyncio
import websockets
from typing import Dict, Any, Callable, Awaitable

logger = logging.getLogger(__name__)

class DerivWSClient:
    def __init__(self, app_id: str, api_token: str):
        self.app_id = app_id
        self.api_token = api_token
        self.ws_url = f"wss://ws.binaryws.com/websockets/v3?app_id={self.app_id}"
        self.ws = None
        self.req_id = 1
        self.callbacks = {}
        self._listener_task = None

    async def connect(self):
        logger.info(f"Connecting to Deriv WebSocket...")
        self.ws = await websockets.connect(self.ws_url)
        self._listener_task = asyncio.create_task(self._listen())
        logger.info("Connected.")

        # Authenticate
        auth_response = await self.send_request({"authorize": self.api_token})
        if "error" in auth_response:
            logger.error(f"Authentication failed: {auth_response['error']['message']}")
            raise Exception("Authentication Failed")
        logger.info("Successfully authenticated.")

    async def disconnect(self):
        if self.ws:
            await self.ws.close()
        if self._listener_task:
            self._listener_task.cancel()
        logger.info("Disconnected from WebSocket.")

    async def _listen(self):
        try:
            async for message in self.ws:
                data = json.loads(message)

                # Check if it's a response to a specific request
                req_id = data.get("req_id")
                if req_id and req_id in self.callbacks:
                    future = self.callbacks.pop(req_id)
                    if not future.done():
                        future.set_result(data)

                # Handle tick stream updates
                if "tick" in data:
                    # If someone subscribed to ticks, we need a way to pass them back.
                    # We will handle streaming in the main logic, but let's allow a callback
                    pass

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"WebSocket listener error: {e}")

    async def send_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request and wait for the specific response using req_id."""
        req_id = self.req_id
        self.req_id += 1

        payload["req_id"] = req_id
        future = asyncio.Future()
        self.callbacks[req_id] = future

        await self.ws.send(json.dumps(payload))

        # Wait for the listener to resolve the future
        return await future

    async def get_ticks_history(self, symbol: str, count: int) -> list:
        """Fetch historical ticks."""
        request = {
            "ticks_history": symbol,
            "end": "latest",
            "count": count,
            "style": "ticks"
        }
        response = await self.send_request(request)
        if "error" in response:
            logger.error(f"Error fetching history: {response['error']['message']}")
            return []

        history = response.get("history", {})
        prices = history.get("prices", [])
        return prices

    async def get_active_symbols(self) -> Dict[str, Any]:
        """Fetch all active symbols to determine correct pip sizes."""
        request = {
            "active_symbols": "brief",
            "product_type": "basic"
        }
        return await self.send_request(request)

    async def get_contract_status(self, contract_id: int) -> Dict[str, Any]:
        """Check the status of an open or recently closed contract."""
        request = {
            "proposal_open_contract": 1,
            "contract_id": contract_id
        }
        return await self.send_request(request)

    async def buy_contract(self, symbol: str, amount: float, contract_type: str, barrier: str, duration: int) -> Dict[str, Any]:
        """
        Execute a digit over/under contract.
        contract_type: "DIGITOVER" or "DIGITUNDER"
        barrier: "2" or "7" depending on over/under strategy
        """
        request = {
            "buy": 1,
            "price": amount,
            "parameters": {
                "amount": amount,
                "basis": "stake",
                "contract_type": contract_type,
                "currency": "USD",
                "duration": duration,
                "duration_unit": "t",
                "symbol": symbol,
                "barrier": barrier
            }
        }

        logger.info(f"Executing {contract_type} trade with barrier {barrier}")
        response = await self.send_request(request)
        return response
