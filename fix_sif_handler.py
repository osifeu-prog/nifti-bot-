path = r"D:\NIFTI\server.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = 'await msg.answer(f"💎 SIF Balance: {bal} SIF\nRate: 1 TON = {rate} SIF")'
new = 'await msg.answer(f"💎 SIF Balance: {bal} SIF\\nRate: 1 TON = {rate} SIF")'
content = content.replace(old, new)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed SIF f‑string")
