# remove_mount.py
server_path = r"D:\NIFTI\server.py"
with open(server_path, "r", encoding="utf-8") as f:
    content = f.read()

# Remove the app.mount line
content = content.replace(
    'app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")',
    '# app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")  # disabled  dist not in Railway'
)
# Also remove the import if we don't use it
content = content.replace(
    'from fastapi.staticfiles import StaticFiles',
    '# from fastapi.staticfiles import StaticFiles'
)

with open(server_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Mount removed")
