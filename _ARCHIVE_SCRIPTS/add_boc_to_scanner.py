# add_boc_to_scanner.py
scanner_path = r"D:\NIFTI\ton_scanner.py"
with open(scanner_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add import if not present
if "from nifti_core import verify_boc" not in content:
    content = content.replace(
        "import asyncio, aiohttp, os, asyncpg, logging",
        "import asyncio, aiohttp, os, asyncpg, logging\nfrom nifti_core import verify_boc"
    )

# Replace process_tx
start_marker = "async def process_tx(tx, pool):"
end_marker = "async def main():"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    new_func = '''async def process_tx(tx, pool):
    tx_hash = tx.get("transaction_id", {}).get("hash", "")
    if not tx_hash:
        return

    # Verify BOC
    boc = await verify_boc(tx_hash)
    if not boc.get("ok"):
        logging.warning(f"BOC verification failed for {tx_hash}: {boc.get('error')}")
        return

    memo = boc.get("comment", "")
    value = boc["amount"]
    user_id = None

    if memo.startswith("NIFTI_PAY:"):
        try:
            user_id = int(memo.split(":")[1])
        except:
            pass

    if not user_id:
        return

    async with pool.acquire() as conn:
        exists = await conn.fetchval("SELECT tx_hash FROM premium_users WHERE tx_hash=$1", tx_hash)
        if exists:
            return
        await conn.execute("UPDATE users SET is_premium = TRUE WHERE user_id = $1", user_id)
        await conn.execute(
            "INSERT INTO premium_users (user_id, bot_name, amount, tx_hash) VALUES ($1, 'nifti', $2, $3)",
            user_id, value, tx_hash
        )
        logging.info(f"✅ Premium activated for user {user_id} ({value} TON)")
        await send_telegram(user_id, f"🎉 Payment of {value} TON received! Your Premium status is now active.")
        await send_telegram(224223270, f"💰 Payment received: {value} TON from user {user_id}")
'''
    content = content[:start_idx] + new_func + "\n\n" + content[end_idx:]
    with open(scanner_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("ton_scanner.py updated with BOC verification")
else:
    print("Could not find process_tx boundaries")
