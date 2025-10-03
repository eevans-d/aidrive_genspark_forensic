

"""
Autenticación y autorización para agentes multiagente.
Provee dependencias para validación de roles y JWT, gestión de tokens y hashing seguro de contraseñas.

R2 Mitigation: Soporte para secretos JWT separados por agente con backward compatibility.
"""

import os
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

# Configuración global de seguridad (R2 mitigation: per-agent secrets with fallback)
# Priority: specific agent secret > JWT_SECRET_KEY > default
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE-ME-IN-PRODUCTION")
JWT_SECRET_DEPOSITO = os.getenv("JWT_SECRET_DEPOSITO", JWT_SECRET_KEY)
JWT_SECRET_NEGOCIO = os.getenv("JWT_SECRET_NEGOCIO", JWT_SECRET_KEY)
JWT_SECRET_ML = os.getenv("JWT_SECRET_ML", JWT_SECRET_KEY)
JWT_SECRET_DASHBOARD = os.getenv("JWT_SECRET_DASHBOARD", JWT_SECRET_KEY)

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 8

# Hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class AuthManager:
    """
    Gestor de autenticación y autorización JWT.
    Métodos para crear/verificar tokens y contraseñas.
    
    R2 Mitigation: Soporta secreto específico por agente para mejor aislamiento.
    """
    def __init__(self, secret_key: Optional[str] = None, issuer: Optional[str] = None):
        """
        Inicializa AuthManager con secreto opcional específico del agente.
        
        Args:
            secret_key: Secreto JWT específico. Si None, usa JWT_SECRET_KEY global.
            issuer: Identificador del agente emisor (e.g., 'deposito', 'negocio').
        """
        self.secret_key = secret_key or JWT_SECRET_KEY
        self.algorithm = JWT_ALGORITHM
        self.issuer = issuer

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """
        Crea un token JWT con expiración y claim de issuer.
        Args:
            data (dict): Datos a codificar en el token.
        Returns:
            str: Token JWT generado.
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        to_encode.update({"exp": expire})
        
        # R2 Mitigation: Añadir claim de issuer si está configurado
        if self.issuer:
            to_encode.update({"iss": self.issuer})
        
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



# Instancia global del gestor de autenticación (backward compatible)
auth_manager = AuthManager()

# R2 Mitigation: Instancias específicas por agente con secretos aislados
auth_manager_deposito = AuthManager(secret_key=JWT_SECRET_DEPOSITO, issuer="deposito")
auth_manager_negocio = AuthManager(secret_key=JWT_SECRET_NEGOCIO, issuer="negocio")
auth_manager_ml = AuthManager(secret_key=JWT_SECRET_ML, issuer="ml")
auth_manager_dashboard = AuthManager(secret_key=JWT_SECRET_DASHBOARD, issuer="dashboard")

def get_auth_manager_for_agent(agent_name: str) -> AuthManager:
    """
    Obtiene la instancia de AuthManager específica para un agente.
    
    Args:
        agent_name: Nombre del agente ('deposito', 'negocio', 'ml', 'dashboard')
    
    Returns:
        AuthManager configurado para el agente especificado.
    
    R2 Mitigation: Permite aislamiento de secretos por agente.
    """
    managers = {
        "deposito": auth_manager_deposito,
        "negocio": auth_manager_negocio,
        "ml": auth_manager_ml,
        "dashboard": auth_manager_dashboard,
    }
    return managers.get(agent_name, auth_manager)

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