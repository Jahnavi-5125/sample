from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordRequestForm

from src.backend.models.model import EmailVerificationRequest, ResetPasswordRequest, VerifyOTPRequest
load_dotenv(dotenv_path=".env", override=True)
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Response
from typing import Annotated
import json
from passlib.context import CryptContext
from urllib.parse import urlencode
import anyio
import src.backend.db.mongodb as mongodb
from src.backend.models.app_io_schemas import Registration
from src.backend.utils.api_utils import generate_otp, redis_manager

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter()

@router.post("/login")
async def login_user_endpoint(login: Annotated[OAuth2PasswordRequestForm, Depends()], response: Response):
    user = await mongodb.get_user(login.username)
    is_new_user = False
    
    if user and user.password==None:
        raise HTTPException(
            status_code=400, detail="User does not have a password set. Please use password reset to set your password.")
    if not user or not pwd_context.verify(login.password.encode('utf-8'), user.password):
        raise HTTPException(
            status_code=400, detail="Invalid email or password or account does not exists.")
    
    access_token = mongodb.jwt_handler.create_access_token(
        {"user_id": str(user.id), "email": user.email, "is_new_user":is_new_user}
    )
    response.set_cookie(
        key="access_token", value=access_token, httponly=False, max_age=60 * 60 * 24 * 30
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/registration")
async def register_user_endpoint(reg: Registration):
    # Check if email exists
    if await mongodb.get_user(reg.email):
        raise HTTPException(400, "Email already exists. Please log in.")

    key = f"otp:{reg.email}"
    existing = await redis_manager.safe_execute("get", key)
    
    if existing:
        await redis_manager.safe_execute("delete", key)
        existing = None
    
    # Generate OTP and store registration data
    if not existing:
        otp = generate_otp()
        expiry = datetime.now() + timedelta(minutes=5)
        
        regdata = {
            "email": reg.email,
            "password": pwd_context.hash(reg.password.encode('utf-8')),
            "full_name": reg.full_name,
            "auth_provider": "local",
            "created_at": datetime.utcnow().isoformat()
        }

        value = {
            "otp": otp,
            "expiry": expiry.isoformat(),
            "purpose": "registration",
            "verified": False,
            "registration_data": regdata
        }

        await redis_manager.safe_execute("set", key, json.dumps(value), ex=300)  # 5 minutes
        
        # Print OTP to backend logs instead of sending email
        print("="*60)
        print(f"[REGISTRATION OTP]")
        print(f"Email: {reg.email}")
        print(f"Full Name: {reg.full_name}")
        print(f"OTP Code: {otp}")
        print(f"Expires at: {expiry}")
        print("="*60)

        return {
            "otp_sent": True, 
            "message": "Verification OTP generated (check backend logs). Please verify to complete registration.",
            "OTP":otp
        }

    # Token exists but not verified
    existing_data = json.loads(existing)
    if not existing_data.get("verified", False):
        raise HTTPException(400, "Please verify the OTP sent to your email.")

    raise HTTPException(400, "Registration already completed, please log in.")


@router.post("/forgot-password/reset")
async def reset_password(data: ResetPasswordRequest):
    key = f"otp:{data.email}"
    token_raw = await redis_manager.safe_execute("get",key)
    
    # Verify token exists and is verified
    if not token_raw:
        raise HTTPException(status_code=400, detail="Please verify OTP first")
    
    token_data = json.loads(token_raw)

    if not token_data.get("verified", False):
        raise HTTPException(status_code=400, detail="Please verify OTP first")
    
    # Verify this was for password reset
    if token_data["purpose"] != "password_reset":
        raise HTTPException(
            status_code=400, 
            detail="Email verification was not done for password reset"
        )
    
    if datetime.now() > datetime.fromisoformat(token_data["expiry"]):
        await redis_manager.safe_execute("delete",key)
        raise HTTPException(status_code=400, detail="Reset session has expired")
    
    # Get user from database
    user = await mongodb.get_user(data.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update password in database
    user.password = pwd_context.hash(data.new_password.encode('utf-8'))
    await user.save()
    
    # Clean up the token after successful password reset
    await redis_manager.safe_execute("delete",key)
    
    return {
        "message": "Password has been reset successfully. Please log in with your new password.",
        "success": True
    }

@router.post("/send-verification-otp")
async def send_verification_otp(data: EmailVerificationRequest):
    # For registration: Check if user already exists
    if data.purpose == "registration":
        existing_user = await mongodb.get_user(data.email)
        if existing_user:
            raise HTTPException(
                status_code=400, detail="Email already exists. Please log in.")
    
    # For password reset: Check if user exists
    elif data.purpose == "password_reset":
        user = await mongodb.get_user(data.email)
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User email doesn't exist"
            )
        # Use the actual user name from DB
        data.name = user.full_name

    # Generate and store OTP with expiration time (15 minutes)
    otp = generate_otp()
    expiry_time = datetime.now() + timedelta(minutes=15)

    token_data = {
        "otp": otp,
        "expiry": expiry_time.isoformat(),
        "purpose": data.purpose,
        "verified": False
    }

    # Save to Redis with 15-minute expiry
    key = f"otp:{data.email}"
    await redis_manager.safe_execute("set", key, json.dumps(token_data), ex=900)
    
    # ===== SIMPLIFIED: Just print OTP to backend logs =====
    print("="*60)
    print(f"[OTP GENERATED]")
    print(f"Purpose: {data.purpose}")
    print(f"Email: {data.email}")
    print(f"OTP Code: {otp}")
    print(f"Expires at: {expiry_time}")
    print("="*60)
    
    # Log in a more structured format if you have a logger configured
    # logger.info(f"OTP Generated - Purpose: {data.purpose}, Email: {data.email}, Code: {otp}, Expires: {expiry_time}")

    return {
        "message": "Verification code has been generated (check backend logs)", 
        "success": True,
        "OTP":otp
    }

@router.post("/verify-otp")
async def verify_otp(data: VerifyOTPRequest, response: Response):
    key = f"otp:{data.email}"
    stored = await redis_manager.safe_execute("get",key)
    print("Stored OTP Data:", stored)
    if not stored:
        raise HTTPException(400, "Invalid or expired request")
    
    token = json.loads(stored)
    print("OTP Token Data:", token)

    if datetime.now() > datetime.fromisoformat(token["expiry"]):
        await redis_manager.safe_execute("delete",key)
        raise HTTPException(400, "OTP has expired")

    if data.otp != token["otp"]:
        raise HTTPException(400, "Invalid OTP")

    token["verified"] = True
    await redis_manager.safe_execute("set", key, json.dumps(token), ex=300)

    # ────────── case A: registration ──────────
    if token["purpose"] == "registration":
        regdata = None
        if "registration_data" in token:
            regdata = token["registration_data"]
        if not regdata:
            raise HTTPException(500, "Missing registration data in OTP token")
        # double-check user still absent
        if await mongodb.get_user(regdata["email"]):
            await redis_manager.safe_execute("delete",key)
            raise HTTPException(400, "Email already exists. Please log in.")
        new_user = await mongodb.create_user(regdata)
        access   = mongodb.jwt_handler.create_access_token(
                      {"user_id": str(new_user.id), "email": new_user.email, "is_new_user": True})

        #  set auth cookie               (optional—comment out if using JWT header only)
        response.set_cookie("access_token", access, httponly=False,
                            max_age=60 * 60 * 24 * 30)

        # cleanup
        await redis_manager.safe_execute("delete",key)

        return {
            "message": "OTP verified & account created",
            "success": True,
            "access_token": access,
            "token_type": "bearer",
        }

    # ────────── case B: password reset ──────────
    # simply acknowledge; actual reset happens in /forgot-password/reset
    return {
        "message": "OTP verified successfully",
        "success": True,
        "purpose": "password_reset"
    }