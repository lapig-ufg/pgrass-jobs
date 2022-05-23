from hashlib import shake_256
from app.db import PyObjectId

def get_id(string: str) -> PyObjectId:
    return PyObjectId(
        shake_256(string.encode()).hexdigest(12)
    )