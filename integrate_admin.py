path = r"D:\NIFTI\saas_core\api_gateway.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# הוספת הייבוא של הראוטר
if "from saas_core.admin.admin_routes import router as admin_router" not in content:
    content = content.replace(
        "from fastapi import FastAPI", 
        "from fastapi import FastAPI\nfrom saas_core.admin.admin_routes import router as admin_router"
    )

# הוספת ה-Include לראוטר
if "app.include_router(admin_router)" not in content:
    content = content.replace(
        "app = FastAPI()", 
        "app = FastAPI()\napp.include_router(admin_router)"
    )

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("Admin Dashboard integrated successfully!")
