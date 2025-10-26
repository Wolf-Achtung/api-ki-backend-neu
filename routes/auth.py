"""Authentication routes for Magic Link login"""
import logging
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.email_service import send_magic_link_email

logger = logging.getLogger("routes.auth")
router = APIRouter()

# Models
class EmailRequest(BaseModel):
    email: EmailStr
    
class LoginRequest(BaseModel):
    email: EmailStr
    code: str
    
    @validator('code')
    def code_must_be_6_digits(cls, v):
        if not v.isdigit() or len(v) != 6:
            raise ValueError('Code must be 6 digits')
        return v

# Helper functions
def hash_code(code: str) -> str:
    """Hash a login code using SHA-256"""
    return hashlib.sha256(code.encode()).hexdigest()

def generate_6_digit_code() -> str:
    """Generate a secure 6-digit code"""
    return f"{secrets.randbelow(1000000):06d}"

async def log_auth_event(
    db: AsyncSession,
    email: str,
    action: str,
    success: bool,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """Log authentication events for security auditing"""
    try:
        await db.execute(
            text("""
                INSERT INTO login_audit (email, action, success, ip_address, user_agent)
                VALUES (:email, :action, :success, :ip_address, :user_agent)
            """),
            {
                "email": email,
                "action": action,
                "success": success,
                "ip_address": ip_address,
                "user_agent": user_agent
            }
        )
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to log auth event: {str(e)}")
        await db.rollback()

async def cleanup_expired_codes(db: AsyncSession):
    """Clean up expired login codes"""
    try:
        await db.execute(
            text("""
                DELETE FROM login_codes 
                WHERE expires_at < NOW()
            """)
        )
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to cleanup expired codes: {str(e)}")
        await db.rollback()

async def invalidate_previous_codes(db: AsyncSession, email: str):
    """Invalidate all previous codes for an email"""
    try:
        await db.execute(
            text("""
                DELETE FROM login_codes 
                WHERE email = :email AND consumed_at IS NULL
            """),
            {"email": email}
        )
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to invalidate previous codes: {str(e)}")
        await db.rollback()

# Routes
@router.post("/request-code")
async def request_login_code(
    request_data: EmailRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Request a magic link login code"""
    email = request_data.email.lower()
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    try:
        # Cleanup expired codes
        await cleanup_expired_codes(db)
        
        # Rate limiting check (max 3 requests per hour per email)
        result = await db.execute(
            text("""
                SELECT COUNT(*) as count
                FROM login_codes
                WHERE email = :email 
                AND created_at > NOW() - INTERVAL '1 hour'
            """),
            {"email": email}
        )
        count = result.scalar()
        
        if count and count >= 3:
            await log_auth_event(db, email, "request_code_rate_limited", False, ip_address, user_agent)
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please wait before requesting a new code."
            )
        
        # Invalidate previous codes
        await invalidate_previous_codes(db, email)
        
        # Generate new code and hash it
        code = generate_6_digit_code()
        code_hash = hash_code(code)
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        # Store hashed code in database
        await db.execute(
            text("""
                INSERT INTO login_codes (email, code_hash, created_at, expires_at, attempts)
                VALUES (:email, :code_hash, NOW(), :expires_at, 0)
            """),
            {
                "email": email,
                "code_hash": code_hash,
                "expires_at": expires_at
            }
        )
        await db.commit()
        
        # Send email with plain code (not hash!)
        await send_magic_link_email(email, code)
        
        # Log success
        await log_auth_event(db, email, "request_code", True, ip_address, user_agent)
        
        logger.info(f"✓ Login code sent to {email}")
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Code sent successfully",
                "email": email,
                "expires_in_minutes": 10
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate code for {email}: {str(e)}")
        await db.rollback()
        await log_auth_event(db, email, "request_code", False, ip_address, user_agent)
        raise HTTPException(
            status_code=500,
            detail="Failed to send login code"
        )

@router.post("/verify-code")
async def verify_login_code(
    login_data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Verify a login code and create session"""
    email = login_data.email.lower()
    code = login_data.code
    code_hash = hash_code(code)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    try:
        # Find valid code
        result = await db.execute(
            text("""
                SELECT id, expires_at, consumed_at, attempts
                FROM login_codes
                WHERE email = :email 
                AND code_hash = :code_hash
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"email": email, "code_hash": code_hash}
        )
        code_record = result.fetchone()
        
        if not code_record:
            await log_auth_event(db, email, "verify_code_invalid", False, ip_address, user_agent)
            raise HTTPException(
                status_code=401,
                detail="Invalid code"
            )
        
        code_id, expires_at, consumed_at, attempts = code_record
        
        # Check if already consumed
        if consumed_at:
            await log_auth_event(db, email, "verify_code_already_used", False, ip_address, user_agent)
            raise HTTPException(
                status_code=401,
                detail="Code already used"
            )
        
        # Check if expired
        if expires_at < datetime.utcnow():
            await log_auth_event(db, email, "verify_code_expired", False, ip_address, user_agent)
            raise HTTPException(
                status_code=401,
                detail="Code expired"
            )
        
        # Check attempts
        if attempts >= 5:
            await log_auth_event(db, email, "verify_code_too_many_attempts", False, ip_address, user_agent)
            raise HTTPException(
                status_code=401,
                detail="Too many failed attempts"
            )
        
        # Mark code as consumed
        await db.execute(
            text("""
                UPDATE login_codes
                SET consumed_at = NOW()
                WHERE id = :code_id
            """),
            {"code_id": code_id}
        )
        
        # Create or update user
        await db.execute(
            text("""
                INSERT INTO users (email, last_login, is_active)
                VALUES (:email, NOW(), TRUE)
                ON CONFLICT (email) 
                DO UPDATE SET last_login = NOW(), is_active = TRUE
            """),
            {"email": email}
        )
        
        await db.commit()
        
        # Log success
        await log_auth_event(db, email, "verify_code", True, ip_address, user_agent)
        
        logger.info(f"✓ Successful login for {email}")
        
        # In production, create proper session token here
        return JSONResponse(
            status_code=200,
            content={
                "message": "Login successful",
                "email": email,
                "session_token": f"temp_token_{secrets.token_urlsafe(32)}"
            }
        )
        
    except HTTPException:
        # Increment attempts on failed verification
        if code_hash:
            try:
                await db.execute(
                    text("""
                        UPDATE login_codes
                        SET attempts = attempts + 1
                        WHERE email = :email AND code_hash = :code_hash
                    """),
                    {"email": email, "code_hash": code_hash}
                )
                await db.commit()
            except:
                pass
        raise
    except Exception as e:
        logger.error(f"Failed to verify code for {email}: {str(e)}")
        await db.rollback()
        await log_auth_event(db, email, "verify_code", False, ip_address, user_agent)
        raise HTTPException(
            status_code=500,
            detail="Failed to verify login code"
        )

@router.post("/logout")
async def logout(request: Request, db: AsyncSession = Depends(get_db)):
    """Logout and invalidate session"""
    # In production, invalidate session token
    return JSONResponse(
        status_code=200,
        content={"message": "Logged out successfully"}
    )
