

"""
Autenticación y autorización para agentes multiagente.
Provee dependencias para validación de roles y JWT, gestión de tokens y hashing seguro de contraseñas.
"""

import os
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

# Configuración global de seguridad
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE-ME-IN-PRODUCTION")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 8

# Hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class AuthManager:
    """
    Gestor de autenticación y autorización JWT.
    Métodos para crear/verificar tokens y contraseñas.
    """
    def __init__(self):
        self.secret_key = JWT_SECRET_KEY
        self.algorithm = JWT_ALGORITHM

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """
        Crea un token JWT con expiración.
        Args:
            data (dict): Datos a codificar en el token.
        Returns:
            str: Token JWT generado.
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verifica y decodifica un token JWT.
        Args:
            token (str): Token JWT a verificar.
        Returns:
            dict: Payload decodificado.
        Raises:
            HTTPException: Si el token está expirado o es inválido.
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )

    def hash_password(self, password: str) -> str:
        """
        Genera el hash seguro de una contraseña.
        """
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifica una contraseña contra su hash.
        """
        return pwd_context.verify(plain_password, hashed_password)



# Instancia global del gestor de autenticación
auth_manager = AuthManager()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dependencia FastAPI para obtener el usuario actual a partir del token JWT.
    """
    token = credentials.credentials
    payload = auth_manager.verify_token(token)
    return payload

def require_role(required_role: str):
    """
    Decorador/Dependencia para requerir un rol específico en el endpoint.
    """
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_role = current_user.get("role")
        if user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere rol: {required_role}"
            )
        return current_user
    return role_checker

# Roles del sistema
ADMIN_ROLE = "admin"
DEPOSITO_ROLE = "deposito"
NEGOCIO_ROLE = "negocio"
ML_ROLE = "ml_service"