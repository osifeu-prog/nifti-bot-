import re

with open('frontend/vite.config.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Add base if missing
if "base:" not in content:
    # Insert after the first '{' or after 'export default defineConfig({'
    content = content.replace(
        'export default defineConfig({',
        "export default defineConfig({\n  base: '/mini-app/',"
    )

with open('frontend/vite.config.js', 'w', encoding='utf-8') as f:
    f.write(content)

print('vite.config.js updated with base: /mini-app/')
