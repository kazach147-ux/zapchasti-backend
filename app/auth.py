import os
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

def check_auth(credentials: HTTPBasicCredentials = Depends(security)):
    admin_user = os.getenv("ADMIN_USER", "admin_zap")
    admin_pass = os.getenv("ADMIN_PASS", "PartMaster_2026!")

    is_user = secrets.compare_digest(credentials.username, admin_user)
    is_pass = secrets.compare_digest(credentials.password, admin_pass)
    
    if not (is_user and is_pass):
        print(f"RENDER_LOG: AUTH_FAILED | User: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )
        
    print(f"RENDER_LOG: AUTH_SUCCESS | User: {credentials.username}")
    return credentials.username