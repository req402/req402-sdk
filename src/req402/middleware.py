import httpx
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import os

class req402Middleware(BaseHTTPMiddleware):
    """
    Fully automatic req402 middleware for FastAPI + x402.
    
    Detects successful x402 payments from popular libraries and reports to req402 dashboard.
    
    Usage – ONLY ONE LINE:
        app.add_middleware(req402Middleware, api_key="fk_your_key")
    """
    
    def __init__(self, app, api_key: Optional[str] = None, backend_url: Optional[str] = None):
        super().__init__(app)
        self.api_key = api_key or os.getenv("REQ402_API_KEY")
        self.backend_url = backend_url or "https://req402-backend.onrender.com"
        
        if not self.api_key:
            raise ValueError("req402 API key is required. Pass it or set REQ402_API_KEY env var.")

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)
        
        if response.status_code != 200:
            return response

        endpoint = str(request.url.path)
        payer_wallet = None
        amount_usd = None
        tx_hash = None

        if hasattr(request.state, "payment"):
            payment = request.state.payment
            payer_wallet = payment.get("payer") or payment.get("from")
            amount_usd = payment.get("amount_usd") or payment.get("price")
            tx_hash = payment.get("tx_hash")

        elif hasattr(request.state, "x402"):
            x402_data = request.state.x402
            payer_wallet = x402_data.get("payer_wallet") or x402_data.get("from")
            amount_usd = x402_data.get("amount_usd")
            tx_hash = x402_data.get("tx_hash")

        elif "x-payment-proof" in request.headers:
            pass

        if payer_wallet and amount_usd:
            await self._report(
                endpoint=endpoint,
                payer_wallet=str(payer_wallet),
                amount_usd=float(amount_usd),
                tx_hash=tx_hash,
                event_type="revenue"
            )

        return response

    async def _report(
        self,
        endpoint: str,
        payer_wallet: str,
        amount_usd: float,
        tx_hash: Optional[str] = None,
        event_type: str = "revenue"
    ):
        payload = {
            "endpoint": endpoint,
            "payer_wallet": payer_wallet,
            "amount_usd": amount_usd,
            "tx_hash": tx_hash,
            "event_type": event_type
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{self.backend_url}/webhook/event",
                    json=payload,
                    headers={"X-API-Key": self.api_key}
                )
        except Exception:
            pass
