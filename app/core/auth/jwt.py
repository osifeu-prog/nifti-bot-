import jwt
import datetime

SECRET = "NIFTI_SUPER_SECRET_CHANGE_ME"

def create_token(user_id: int):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


def verify_token(token: str):
    try:
        return jwt.decode(token, SECRET, algorithms=["HS256"])
    except Exception:
        return None

