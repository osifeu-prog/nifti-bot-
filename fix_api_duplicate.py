import os
server_path = r"D:\NIFTI\server.py"
with open(server_path, "r", encoding="utf-8") as f:
    lines = f.readlines()
# Find first occurrence of "async def api_card_json"
idx_to_remove = None
for i, line in enumerate(lines):
    if line.strip().startswith("async def api_card_json"):
        idx_to_remove = i
        break
if idx_to_remove is None:
    print("First api_card_json not found")
else:
    # Remove the function and its decorator
    del lines[idx_to_remove-1:idx_to_remove+9]  # decorator + def + body (approx 8 lines)
    with open(server_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Removed duplicate api_card_json")
