"""RustChain API client wrapper for the MCP server."""

import httpx
import os
from typing import Any, Dict, List, Optional


class RustChainClient:
    """Sync HTTP client for RustChain node RPC API."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
    ):
        self._base_url = (base_url or os.environ.get("RUSTCHAIN_NODE_URL", "https://50.28.86.131")).rstrip("/")
        self._timeout = timeout
        self._client: Optional[httpx.Client] = None
        # Skip SSL verification for IP-based URLs with self-signed certs
        self._verify: bool | str = os.environ.get("RUSTCHAIN_SKIP_SSL_VERIFY", "").lower() not in ("1", "true", "yes")
        if not self._verify:
            self._verify = True  # will be set per-client below

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            import ssl
            # If URL is an IP address, default to skipping SSL verification
            verify: bool | str = True
            if os.environ.get("RUSTCHAIN_SKIP_SSL_VERIFY", "").lower() in ("1", "true", "yes"):
                verify = False
            elif self._base_url.startswith("https://50.") or self._base_url.startswith("https://76.") or self._base_url.startswith("https://192."):
                # Heuristic: self-signed certs on IP-based RustChain nodes
                verify = False
            self._client = httpx.Client(
                base_url=self._base_url,
                timeout=self._timeout,
                verify=verify,
            )
        return self._client

    def _get(self, path: str, params: Dict[str, Any] | None = None) -> Any:
        try:
            resp = self._get_client().get(path, params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
        except Exception as e:
            return {"error": str(e)}

    def _post(self, path: str, json_data: Dict[str, Any] | None = None) -> Any:
        try:
            resp = self._get_client().post(path, json=json_data)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
        except Exception as e:
            return {"error": str(e)}

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    # ── Tools ────────────────────────────────────────────────────────

    def health(self) -> Dict[str, Any]:
        """Check node health."""
        return self._get("/health")

    def balance(self, address: str) -> Dict[str, Any]:
        """Get wallet balance by address."""
        return self._get("/wallet/balance", params={"address": address})

    def balance_by_miner_id(self, miner_id: str) -> Dict[str, Any]:
        """Get wallet balance by miner ID."""
        return self._get("/wallet/balance", params={"miner_id": miner_id})

    def miners(self) -> List[Dict[str, Any]]:
        """List active miners."""
        result = self._get("/miners")
        if isinstance(result, list):
            return result
        return result.get("miners", [])

    def epoch(self) -> Dict[str, Any]:
        """Get current epoch info."""
        return self._get("/epoch")

    def wallet_history(self, address: str, limit: int = 50) -> Dict[str, Any]:
        """Get transaction history for a wallet."""
        return self._get("/wallet/history", params={"address": address, "limit": limit})

    def attestation_status(self, miner_public_key: str) -> Dict[str, Any]:
        """Get attestation status for a miner."""
        return self._get("/attestation/status", params={"miner_public_key": miner_public_key})

    def bounty_multiplier(self) -> Dict[str, Any]:
        """Get current bounty multiplier."""
        return self._get("/attestation/bounty_multiplier")

    def explorer_blocks(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent blocks."""
        result = self._get("/explorer/blocks", params={"limit": limit})
        if isinstance(result, list):
            return result
        return result.get("blocks", [])

    def explorer_transactions(self, address: str | None = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get transactions, optionally filtered by address."""
        params: Dict[str, Any] = {"limit": limit}
        if address:
            params["address"] = address
        result = self._get("/explorer/transactions", params=params)
        if isinstance(result, list):
            return result
        return result.get("transactions", [])

    def governance_proposals(self, status: str | None = None) -> List[Dict[str, Any]]:
        """List governance proposals."""
        params = {"status": status} if status else {}
        result = self._get("/governance/proposals", params=params)
        if isinstance(result, list):
            return result
        return result.get("proposals", [])


# Global singleton client (lazily created per server instance)
_client: Optional[RustChainClient] = None


def get_client(node_url: str | None = None) -> RustChainClient:
    global _client
    if _client is None:
        _client = RustChainClient(base_url=node_url)
    return _client
