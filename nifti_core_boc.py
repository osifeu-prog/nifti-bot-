import aiohttp
import os

TONCENTER_API = "https://toncenter.com/api/v2"

async def verify_boc(tx_hash: str) -> dict:
    """Check transaction on TON. Returns dict with ok, amount, sender, comment or error."""
    url = f"{TONCENTER_API}/getTransactions?hash={tx_hash}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("ok"):
                    tx = data.get("result", [{}])[0]
                    value = int(tx.get("in_msg", {}).get("value", 0)) / 1e9
                    comment = tx.get("comment", "")
                    sender = tx.get("in_msg", {}).get("source", "")
                    return {"ok": True, "amount": value, "sender": sender, "comment": comment}
                return {"ok": False, "error": "Transaction not found or invalid"}
            return {"ok": False, "error": f"API error {resp.status}"}

