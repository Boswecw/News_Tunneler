"""Secrets management and validation."""
import os
import secrets
import string
from typing import Optional
from app.core.logging import logger


class SecretsValidator:
    """Validate and manage application secrets."""
    
    REQUIRED_SECRETS_PRODUCTION = [
        "JWT_SECRET_KEY",
        "POSTGRES_PASSWORD",
    ]
    
    RECOMMENDED_SECRETS = [
        "OPENAI_API_KEY",
        "NEWSAPI_KEY",
        "SLACK_WEBHOOK_URL",
        "SMTP_PASSWORD",
    ]
    
    WEAK_SECRETS = [
        "your-secret-key-change-in-production",
        "your_key_here",
        "changeme",
        "password",
        "secret",
        "admin",
        "test",
    ]
    
    @staticmethod
    def generate_secret_key(length: int = 32) -> str:
        """Generate a cryptographically secure secret key."""
        alphabet = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def is_weak_secret(value: str) -> bool:
        """Check if a secret value is weak or default."""
        if not value or len(value) < 16:
            return True
        
        value_lower = value.lower()
        for weak in SecretsValidator.WEAK_SECRETS:
            if weak in value_lower:
                return True
        
        return False
    
    @staticmethod
    def validate_jwt_secret(secret: str) -> tuple[bool, Optional[str]]:
        """Validate JWT secret key."""
        if not secret:
            return False, "JWT_SECRET_KEY is not set"
        
        if len(secret) < 32:
            return False, "JWT_SECRET_KEY must be at least 32 characters"
        
        if SecretsValidator.is_weak_secret(secret):
            return False, "JWT_SECRET_KEY appears to be a weak or default value"
        
        return True, None
    
    @staticmethod
    def validate_postgres_password(password: str, env: str) -> tuple[bool, Optional[str]]:
        """Validate PostgreSQL password."""
        if env == "production":
            if not password:
                return False, "POSTGRES_PASSWORD is not set in production"
            
            if len(password) < 16:
                return False, "POSTGRES_PASSWORD must be at least 16 characters in production"
            
            if SecretsValidator.is_weak_secret(password):
                return False, "POSTGRES_PASSWORD appears to be a weak or default value"
        
        return True, None
    
    @staticmethod
    def validate_all_secrets(env: str = "dev") -> dict:
        """
        Validate all application secrets.
        
        Returns a dict with validation results.
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Check JWT secret
        jwt_secret = os.getenv("JWT_SECRET_KEY", "")
        is_valid, error = SecretsValidator.validate_jwt_secret(jwt_secret)
        if not is_valid:
            if env == "production":
                results["valid"] = False
                results["errors"].append(error)
            else:
                results["warnings"].append(error)
        
        # Check PostgreSQL password
        use_postgresql = os.getenv("USE_POSTGRESQL", "false").lower() == "true"
        if use_postgresql:
            postgres_password = os.getenv("POSTGRES_PASSWORD", "")
            is_valid, error = SecretsValidator.validate_postgres_password(postgres_password, env)
            if not is_valid:
                if env == "production":
                    results["valid"] = False
                    results["errors"].append(error)
                else:
                    results["warnings"].append(error)
        
        # Check recommended secrets
        for secret_name in SecretsValidator.RECOMMENDED_SECRETS:
            value = os.getenv(secret_name, "")
            if not value or SecretsValidator.is_weak_secret(value):
                results["recommendations"].append(
                    f"{secret_name} is not set or appears weak. "
                    f"Some features may not work."
                )
        
        return results
    
    @staticmethod
    def log_validation_results(results: dict) -> None:
        """Log secrets validation results."""
        if results["errors"]:
            logger.error("❌ Secrets validation failed:")
            for error in results["errors"]:
                logger.error(f"  - {error}")
        
        if results["warnings"]:
            logger.warning("⚠️  Secrets validation warnings:")
            for warning in results["warnings"]:
                logger.warning(f"  - {warning}")
        
        if results["recommendations"]:
            logger.info("💡 Secrets recommendations:")
            for rec in results["recommendations"]:
                logger.info(f"  - {rec}")
        
        if results["valid"] and not results["warnings"]:
            logger.info("✅ All secrets validated successfully")


def validate_secrets_on_startup(env: str = "dev") -> None:
    """
    Validate secrets on application startup.
    
    Raises an exception in production if validation fails.
    """
    logger.info("Validating application secrets...")
    results = SecretsValidator.validate_all_secrets(env)
    SecretsValidator.log_validation_results(results)
    
    if not results["valid"] and env == "production":
        raise ValueError(
            "Secrets validation failed in production environment. "
            "Please fix the errors before starting the application."
        )


def generate_env_template() -> str:
    """Generate a .env template with secure defaults."""
    jwt_secret = SecretsValidator.generate_secret_key(64)
    postgres_password = SecretsValidator.generate_secret_key(32)
    admin_token = SecretsValidator.generate_secret_key(32)
    
    template = f"""# Generated .env template with secure secrets
# Generated on: {os.popen('date').read().strip()}

# IMPORTANT: These are randomly generated secrets. 
# Store them securely and never commit to version control!

# Authentication & Security
JWT_SECRET_KEY={jwt_secret}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
REQUIRE_AUTH=false
ALLOW_REGISTRATION=true

# Database
USE_POSTGRESQL=false
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=news_tunneler
POSTGRES_USER=news_tunneler
POSTGRES_PASSWORD={postgres_password}
POSTGRES_POOL_SIZE=10
POSTGRES_MAX_OVERFLOW=20

# Admin
ADMIN_TOKEN={admin_token}

# Optional API Keys (set these manually)
OPENAI_API_KEY=
NEWSAPI_KEY=
ALPHAVANTAGE_KEY=
POLYGON_API_KEY=

# Notifications (set these manually)
SLACK_WEBHOOK_URL=
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
ALERT_EMAIL_TO=

# Monitoring
SENTRY_DSN=
PROMETHEUS_ENABLED=true
LOG_LEVEL=INFO
"""
    return template


if __name__ == "__main__":
    # CLI tool to generate secure .env file
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "generate":
        print(generate_env_template())
    else:
        # Validate current environment
        env = os.getenv("ENV", "dev")
        validate_secrets_on_startup(env)

