"""
routes/auth.py – Magic-Link Auth (Code anfordern & Login)
Router mit /auth Prefix; main.py mountet ihn unter /api -> /api/auth/*
"""
from __future__ import annotations

import logging
import secrets
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr

from settings import get_settings
from services.mailer import Mailer
from services.rate_limit import RateLimiter
from services.redis_utils import RedisBox
from utils.idempotency import IdempotencyBox
from core.security import create_access_token, get_current_user, TokenPayload

# Whitelist für erlaubte E-Mail-Adressen (Testphase)
# Diese Liste muss synchron mit setup_database.py TESTUSERS gehalten werden
# Alle Emails sind lowercase für case-insensitive Vergleich
EMAIL_WHITELIST = {email.lower() for email in [
    "j.hohl@freenet.de",
    "kerstin.geffert@gmail.com",
    "post@zero2.de",
    "giselapeter@peter-partner.de",
    "wolf.hohl@web.de",
    "geffertj@mac.com",
    "geffertkilian@gmail.com",
    "berndemhart46@gmail.com",
    "po@wbs-slg.de",
    "trailerman01@outlook.de",
    "hilfe@ki-sicherheit.jetzt",
    "levent.graef@posteo.de",
    "birgit.cook@ulitzka-partner.de",
    "alexander.luckow@icloud.com",
    "frank.beer@kabelmail.de",
    "patrick@silk-relations.com",
    "marc@trailerhaus-onair.de",
    "norbert@trailerhaus.de",
    "sonia-souto@mac.com",
    "christian.ulitzka@ulitzka-partner.de",
    "srack@gmx.net",
    "buss@maria-hilft.de",
    "w.beestermoeller@web.de",
    "bewertung@ki-sicherheit.jetzt",  # Admin
    "test@example.com",  # Für CI/CD Tests
    # v7.0 Production Testing
    "test-v7-final@ki-sicherheit.jetzt",
    "test-v7-1@ki-sicherheit.jetzt",
    "test-v7-2@ki-sicherheit.jetzt",
    "test-v7-3@ki-sicherheit.jetzt",
    "test-v7-4@ki-sicherheit.jetzt",
    "test-v7-5@ki-sicherheit.jetzt",
    "test-v7-6@ki-sicherheit.jetzt",
    "test-v7-7@ki-sicherheit.jetzt",
    "test-v7-8@ki-sicherheit.jetzt",
    "test-v7-10@ki-sicherheit.jetzt",
    "test-v7-11@ki-sicherheit.jetzt",
    "test-v7-12@ki-sicherheit.jetzt",
    "test-v7-13@ki-sicherheit.jetzt",
    "test-v7-14@ki-sicherheit.jetzt",
    "test-v7-15@ki-sicherheit.jetzt",
    "test-v7-16@ki-sicherheit.jetzt",
    "test-v7-17@ki-sicherheit.jetzt",
    "test-v7-18@ki-sicherheit.jetzt",
    "test-v7-19@ki-sicherheit.jetzt",
    "test-v7-20@ki-sicherheit.jetzt",
    "test-v7-21@ki-sicherheit.jetzt",
    "test-v7-22@ki-sicherheit.jetzt",
    "test-v7-23@ki-sicherheit.jetzt",
    "test-v7-24@ki-sicherheit.jetzt",
    "test-v7-25@ki-sicherheit.jetzt",
    "test-v7-26@ki-sicherheit.jetzt",
    "test-v7-27@ki-sicherheit.jetzt",
    "test-v7-28@ki-sicherheit.jetzt",
    "test-v7-29@ki-sicherheit.jetzt",
    "test-v7-30@ki-sicherheit.jetzt",
    "test-v7-31@ki-sicherheit.jetzt",
    "test-v7-32@ki-sicherheit.jetzt",
    "test-v7-33@ki-sicherheit.jetzt",
    "test-v7-34@ki-sicherheit.jetzt",
    "test-v7-35@ki-sicherheit.jetzt",
    "test-v7-36@ki-sicherheit.jetzt",
    "test-v7-37@ki-sicherheit.jetzt",
    "test-v7-38@ki-sicherheit.jetzt",
    "test-v7-39@ki-sicherheit.jetzt",
    "test-v7-40@ki-sicherheit.jetzt",
    "test-v7-41@ki-sicherheit.jetzt",
    "test-v7-42@ki-sicherheit.jetzt",
    "test-v7-43@ki-sicherheit.jetzt",
    "test-v7-44@ki-sicherheit.jetzt",
    "test-v7-45@ki-sicherheit.jetzt",
    "test-v7-46@ki-sicherheit.jetzt",
    "test-v7-47@ki-sicherheit.jetzt",
    "test-v7-48@ki-sicherheit.jetzt",
    "test-v7-49@ki-sicherheit.jetzt",
    "test-v7-50@ki-sicherheit.jetzt",
    "test-v7-51@ki-sicherheit.jetzt",
    "test-v7-52@ki-sicherheit.jetzt",
    "test-v7-53@ki-sicherheit.jetzt",
    "test-v7-54@ki-sicherheit.jetzt",
    "test-v7-55@ki-sicherheit.jetzt",
    "test-v7-56@ki-sicherheit.jetzt",
    "test-v7-57@ki-sicherheit.jetzt",
    "test-v7-58@ki-sicherheit.jetzt",
    "test-v7-59@ki-sicherheit.jetzt",
    "test-v7-60@ki-sicherheit.jetzt",
    "test-v7-61@ki-sicherheit.jetzt",
    "test-v7-62@ki-sicherheit.jetzt",
    "test-v7-63@ki-sicherheit.jetzt",
    "test-v7-64@ki-sicherheit.jetzt",
    "test-v7-65@ki-sicherheit.jetzt",
    "test-v7-66@ki-sicherheit.jetzt",
    "test-v7-67@ki-sicherheit.jetzt",
    "test-v7-68@ki-sicherheit.jetzt",
    "test-v7-69@ki-sicherheit.jetzt",
    "test-v7-70@ki-sicherheit.jetzt",
    "test-v7-71@ki-sicherheit.jetzt",
    "test-v7-72@ki-sicherheit.jetzt",
    "test-v7-73@ki-sicherheit.jetzt",
    "test-v7-74@ki-sicherheit.jetzt",
    "test-v7-75@ki-sicherheit.jetzt",
    "test-v7-76@ki-sicherheit.jetzt",
    "test-v7-77@ki-sicherheit.jetzt",
    "test-v7-78@ki-sicherheit.jetzt",
    "test-v7-79@ki-sicherheit.jetzt",
    "test-v7-80@ki-sicherheit.jetzt",
    "test-v7-81@ki-sicherheit.jetzt",
    "test-v7-82@ki-sicherheit.jetzt",
    "test-v7-83@ki-sicherheit.jetzt",
    "test-v7-84@ki-sicherheit.jetzt",
    "test-v7-85@ki-sicherheit.jetzt",
    "test-v7-86@ki-sicherheit.jetzt",
    "test-v7-87@ki-sicherheit.jetzt",
    "test-v7-88@ki-sicherheit.jetzt",
    "test-v7-89@ki-sicherheit.jetzt",
    "test-v7-90@ki-sicherheit.jetzt",
    "test-v7-91@ki-sicherheit.jetzt",
    "test-v7-92@ki-sicherheit.jetzt",
    "test-v7-93@ki-sicherheit.jetzt",
    "test-v7-94@ki-sicherheit.jetzt",
    "test-v7-95@ki-sicherheit.jetzt",
    "test-v7-96@ki-sicherheit.jetzt",
    "test-v7-97@ki-sicherheit.jetzt",
    "test-v7-98@ki-sicherheit.jetzt",
    "test-v7-99@ki-sicherheit.jetzt",
    "test-v7-100@ki-sicherheit.jetzt",
    "test-v7-101@ki-sicherheit.jetzt",
    "test-v7-102@ki-sicherheit.jetzt",
    "test-v7-103@ki-sicherheit.jetzt",
    "test-v7-104@ki-sicherheit.jetzt",
    "test-v7-105@ki-sicherheit.jetzt",
    "test-v7-106@ki-sicherheit.jetzt",
    "test-v7-107@ki-sicherheit.jetzt",
    "test-v7-108@ki-sicherheit.jetzt",
    "test-v7-109@ki-sicherheit.jetzt",
    "test-v7-110@ki-sicherheit.jetzt",
    "test-v7-111@ki-sicherheit.jetzt",
    "test-v7-112@ki-sicherheit.jetzt",
    "test-v7-113@ki-sicherheit.jetzt",
    "test-v7-114@ki-sicherheit.jetzt",
    "test-v7-115@ki-sicherheit.jetzt",
    "test-v7-116@ki-sicherheit.jetzt",
    "test-v7-117@ki-sicherheit.jetzt",
    "test-v7-118@ki-sicherheit.jetzt",
    "test-v7-119@ki-sicherheit.jetzt",
    "test-v7-120@ki-sicherheit.jetzt",
    "test-v7-121@ki-sicherheit.jetzt",
    "test-v7-122@ki-sicherheit.jetzt",
    "test-v7-123@ki-sicherheit.jetzt",
    "test-v7-124@ki-sicherheit.jetzt",
    "test-v7-125@ki-sicherheit.jetzt",
    "test-v7-126@ki-sicherheit.jetzt",
    "test-v7-127@ki-sicherheit.jetzt",
    "test-v7-128@ki-sicherheit.jetzt",
    "test-v7-129@ki-sicherheit.jetzt",
    "test-v7-130@ki-sicherheit.jetzt",
    "test-v7-131@ki-sicherheit.jetzt",
    "test-v7-132@ki-sicherheit.jetzt",
    "test-v7-133@ki-sicherheit.jetzt",
    "test-v7-134@ki-sicherheit.jetzt",
    "test-v7-135@ki-sicherheit.jetzt",
    "test-v7-136@ki-sicherheit.jetzt",
    "test-v7-137@ki-sicherheit.jetzt",
    "test-v7-138@ki-sicherheit.jetzt",
    "test-v7-139@ki-sicherheit.jetzt",
    "test-v7-140@ki-sicherheit.jetzt",
    "test-v7-141@ki-sicherheit.jetzt",
    "test-v7-142@ki-sicherheit.jetzt",
    "test-v7-143@ki-sicherheit.jetzt",
    "test-v7-144@ki-sicherheit.jetzt",
    "test-v7-145@ki-sicherheit.jetzt",
    "test-v7-146@ki-sicherheit.jetzt",
    "test-v7-147@ki-sicherheit.jetzt",
    "test-v7-148@ki-sicherheit.jetzt",
    "test-v7-149@ki-sicherheit.jetzt",
    "test-v7-150@ki-sicherheit.jetzt",
    "test-v7-151@ki-sicherheit.jetzt",
    "test-v7-152@ki-sicherheit.jetzt",
    "test-v7-153@ki-sicherheit.jetzt",
    "test-v7-154@ki-sicherheit.jetzt",
    "test-v7-155@ki-sicherheit.jetzt",
    "test-v7-156@ki-sicherheit.jetzt",
    "test-v7-157@ki-sicherheit.jetzt",
    "test-v7-158@ki-sicherheit.jetzt",
    "test-v7-159@ki-sicherheit.jetzt",
    "test-v7-160@ki-sicherheit.jetzt",
    "test-v7-161@ki-sicherheit.jetzt",
    "test-v7-162@ki-sicherheit.jetzt",
    "test-v7-163@ki-sicherheit.jetzt",
    "test-v7-164@ki-sicherheit.jetzt",
    "test-v7-165@ki-sicherheit.jetzt",
    "test-v7-166@ki-sicherheit.jetzt",
    "test-v7-167@ki-sicherheit.jetzt",
    "test-v7-168@ki-sicherheit.jetzt",
    "test-v7-169@ki-sicherheit.jetzt",
    "test-v7-170@ki-sicherheit.jetzt",
    "test-v7-171@ki-sicherheit.jetzt",
    "test-v7-172@ki-sicherheit.jetzt",
    "test-v7-173@ki-sicherheit.jetzt",
    "test-v7-174@ki-sicherheit.jetzt",
    "test-v7-175@ki-sicherheit.jetzt",
    "test-v7-176@ki-sicherheit.jetzt",
    "test-v7-177@ki-sicherheit.jetzt",
    "test-v7-178@ki-sicherheit.jetzt",
    "test-v7-179@ki-sicherheit.jetzt",
    "test-v7-180@ki-sicherheit.jetzt",
    "test-v7-181@ki-sicherheit.jetzt",
    "test-v7-182@ki-sicherheit.jetzt",
    "test-v7-183@ki-sicherheit.jetzt",
    "test-v7-184@ki-sicherheit.jetzt",
    "test-v7-185@ki-sicherheit.jetzt",
    "test-v7-186@ki-sicherheit.jetzt",
    "test-v7-187@ki-sicherheit.jetzt",
    "test-v7-188@ki-sicherheit.jetzt",
    "test-v7-189@ki-sicherheit.jetzt",
    "test-v7-190@ki-sicherheit.jetzt",
    "test-v7-191@ki-sicherheit.jetzt",
    "test-v7-192@ki-sicherheit.jetzt",
    "test-v7-193@ki-sicherheit.jetzt",
    "test-v7-194@ki-sicherheit.jetzt",
    "test-v7-195@ki-sicherheit.jetzt",
    "test-v7-196@ki-sicherheit.jetzt",
    "test-v7-197@ki-sicherheit.jetzt",
    "test-v7-198@ki-sicherheit.jetzt",
    "test-v7-199@ki-sicherheit.jetzt",
    "test-v7-200@ki-sicherheit.jetzt",
    "test-v7-201@ki-sicherheit.jetzt",
    "test-v7-202@ki-sicherheit.jetzt",
    "test-v7-203@ki-sicherheit.jetzt",
    "test-v7-204@ki-sicherheit.jetzt",
    "test-v7-205@ki-sicherheit.jetzt",
    "test-v7-206@ki-sicherheit.jetzt",
    "test-v7-207@ki-sicherheit.jetzt",
    "test-v7-208@ki-sicherheit.jetzt",
    "test-v7-209@ki-sicherheit.jetzt",
    "test-v7-210@ki-sicherheit.jetzt",
    "test-v7-211@ki-sicherheit.jetzt",
    "test-v7-212@ki-sicherheit.jetzt",
    "test-v7-213@ki-sicherheit.jetzt",
    "test-v7-214@ki-sicherheit.jetzt",
    "test-v7-215@ki-sicherheit.jetzt",
    "test-v7-216@ki-sicherheit.jetzt",
    "test-v7-217@ki-sicherheit.jetzt",
    "test-v7-218@ki-sicherheit.jetzt",
    "test-v7-219@ki-sicherheit.jetzt",
    "test-v7-220@ki-sicherheit.jetzt",
    "test-v7-221@ki-sicherheit.jetzt",
    "test-v7-222@ki-sicherheit.jetzt",
    "test-v7-223@ki-sicherheit.jetzt",
    "test-v7-224@ki-sicherheit.jetzt",
    "test-v7-225@ki-sicherheit.jetzt",
    "test-v7-226@ki-sicherheit.jetzt",
    "test-v7-227@ki-sicherheit.jetzt",
    "test-v7-228@ki-sicherheit.jetzt",
    "test-v7-229@ki-sicherheit.jetzt",
    "test-v7-230@ki-sicherheit.jetzt",
    "test-v7-231@ki-sicherheit.jetzt",
    "test-v7-232@ki-sicherheit.jetzt",
    "test-v7-233@ki-sicherheit.jetzt",
    "test-v7-234@ki-sicherheit.jetzt",
    "test-v7-235@ki-sicherheit.jetzt",
    "test-v7-236@ki-sicherheit.jetzt",
    "test-v7-237@ki-sicherheit.jetzt",
    "test-v7-238@ki-sicherheit.jetzt",
    "test-v7-239@ki-sicherheit.jetzt",
    "test-v7-240@ki-sicherheit.jetzt",
    "test-v7-241@ki-sicherheit.jetzt",
    "test-v7-242@ki-sicherheit.jetzt",
    "test-v7-243@ki-sicherheit.jetzt",
    "test-v7-244@ki-sicherheit.jetzt",
    "test-v7-245@ki-sicherheit.jetzt",
    "test-v7-246@ki-sicherheit.jetzt",
    "test-v7-247@ki-sicherheit.jetzt",
    "test-v7-248@ki-sicherheit.jetzt",
    "test-v7-249@ki-sicherheit.jetzt",
    "test-v7-250@ki-sicherheit.jetzt",
    "test-v7-251@ki-sicherheit.jetzt",
    "test-v7-252@ki-sicherheit.jetzt",
    "test-v7-253@ki-sicherheit.jetzt",
    "test-v7-254@ki-sicherheit.jetzt",
    "test-v7-255@ki-sicherheit.jetzt",
    "test-v7-256@ki-sicherheit.jetzt",
    "test-v7-257@ki-sicherheit.jetzt",
    "test-v7-258@ki-sicherheit.jetzt",
    "test-v7-259@ki-sicherheit.jetzt",
    "test-v7-260@ki-sicherheit.jetzt",
    "test-v7-261@ki-sicherheit.jetzt",
    "test-v7-262@ki-sicherheit.jetzt",
    "test-v7-263@ki-sicherheit.jetzt",
    "test-v7-264@ki-sicherheit.jetzt",
    "test-v7-265@ki-sicherheit.jetzt",
    "test-v7-266@ki-sicherheit.jetzt",
    "test-v7-267@ki-sicherheit.jetzt",
    "test-v7-268@ki-sicherheit.jetzt",
    "test-v7-269@ki-sicherheit.jetzt",
    "test-v7-270@ki-sicherheit.jetzt",
    "test-v7-271@ki-sicherheit.jetzt",
    "test-v7-272@ki-sicherheit.jetzt",
    "test-v7-273@ki-sicherheit.jetzt",
    "test-v7-274@ki-sicherheit.jetzt",
    "test-v7-275@ki-sicherheit.jetzt",
    "test-v7-276@ki-sicherheit.jetzt",
    "test-v7-277@ki-sicherheit.jetzt",
    "test-v7-278@ki-sicherheit.jetzt",
    "test-v7-279@ki-sicherheit.jetzt",
    "test-v7-280@ki-sicherheit.jetzt",
    "test-v7-281@ki-sicherheit.jetzt",
    "test-v7-282@ki-sicherheit.jetzt",
    "test-v7-283@ki-sicherheit.jetzt",
    "test-v7-284@ki-sicherheit.jetzt",
    "test-v7-285@ki-sicherheit.jetzt",
    "test-v7-286@ki-sicherheit.jetzt",
    "test-v7-287@ki-sicherheit.jetzt",
    "test-v7-288@ki-sicherheit.jetzt",
    "test-v7-289@ki-sicherheit.jetzt",
    "test-v7-290@ki-sicherheit.jetzt",
    "test-v7-291@ki-sicherheit.jetzt",
    "test-v7-292@ki-sicherheit.jetzt",
    "test-v7-293@ki-sicherheit.jetzt",
    "test-v7-294@ki-sicherheit.jetzt",
    "test-v7-295@ki-sicherheit.jetzt",
    "test-v7-296@ki-sicherheit.jetzt",
    "test-v7-297@ki-sicherheit.jetzt",
    "test-v7-298@ki-sicherheit.jetzt",
    "test-v7-299@ki-sicherheit.jetzt",
    "test-v7-300@ki-sicherheit.jetzt",
    "test-v7-301@ki-sicherheit.jetzt",
    "test-v7-302@ki-sicherheit.jetzt",
    "test-v7-303@ki-sicherheit.jetzt",
    "test-v7-304@ki-sicherheit.jetzt",
    "test-v7-305@ki-sicherheit.jetzt",
    "test-v7-306@ki-sicherheit.jetzt",
    "test-v7-307@ki-sicherheit.jetzt",
    "test-v7-308@ki-sicherheit.jetzt",
    "test-v7-309@ki-sicherheit.jetzt",
    "test-v7-310@ki-sicherheit.jetzt",
    "test-v7-311@ki-sicherheit.jetzt",
    "test-v7-312@ki-sicherheit.jetzt",
    "test-v7-313@ki-sicherheit.jetzt",
    "test-v7-314@ki-sicherheit.jetzt",
    "test-v7-315@ki-sicherheit.jetzt",
    "test-v7-316@ki-sicherheit.jetzt",
    "test-v7-317@ki-sicherheit.jetzt",
    "test-v7-318@ki-sicherheit.jetzt",
    "test-v7-319@ki-sicherheit.jetzt",
    "test-v7-320@ki-sicherheit.jetzt",
    "test-v7-321@ki-sicherheit.jetzt",
    "test-v7-322@ki-sicherheit.jetzt",
    "test-v7-323@ki-sicherheit.jetzt",
    "test-v7-324@ki-sicherheit.jetzt",
    "test-v7-325@ki-sicherheit.jetzt",
    "test-v7-326@ki-sicherheit.jetzt",
    "test-v7-327@ki-sicherheit.jetzt",
    "test-v7-328@ki-sicherheit.jetzt",
    "test-v7-329@ki-sicherheit.jetzt",
    "test-v7-330@ki-sicherheit.jetzt",
    "test-v7-331@ki-sicherheit.jetzt",
    "test-v7-332@ki-sicherheit.jetzt",
    "test-v7-333@ki-sicherheit.jetzt",
    "test-v7-334@ki-sicherheit.jetzt",
    "test-v7-335@ki-sicherheit.jetzt",
    "test-v7-336@ki-sicherheit.jetzt",
    "test-v7-337@ki-sicherheit.jetzt",
    "test-v7-338@ki-sicherheit.jetzt",
    "test-v7-339@ki-sicherheit.jetzt",
    "test-v7-340@ki-sicherheit.jetzt",
    "test-v7-341@ki-sicherheit.jetzt",
    "test-v7-342@ki-sicherheit.jetzt",
    "test-v7-343@ki-sicherheit.jetzt",
    "test-v7-344@ki-sicherheit.jetzt",
    "test-v7-345@ki-sicherheit.jetzt",
    "test-v7-346@ki-sicherheit.jetzt",
    "test-v7-347@ki-sicherheit.jetzt",
    "test-v7-348@ki-sicherheit.jetzt",
    "test-v7-349@ki-sicherheit.jetzt",
    "test-v7-350@ki-sicherheit.jetzt",
    "test-v7-351@ki-sicherheit.jetzt",
    "test-v7-352@ki-sicherheit.jetzt",
    "test-v7-353@ki-sicherheit.jetzt",
    "test-v7-354@ki-sicherheit.jetzt",
    "test-v7-355@ki-sicherheit.jetzt",
    "test-v7-356@ki-sicherheit.jetzt",
    "test-v7-357@ki-sicherheit.jetzt",
    "test-v7-358@ki-sicherheit.jetzt",
    "test-v7-359@ki-sicherheit.jetzt",
    "test-v7-360@ki-sicherheit.jetzt",    
    "test-v7-9@ki-sicherheit.jetzt",
    "test-v7-361@ki-sicherheit.jetzt",
    "test-v7-362@ki-sicherheit.jetzt",
    "test-v7-363@ki-sicherheit.jetzt",
    "test-v7-364@ki-sicherheit.jetzt",
    "test-v7-365@ki-sicherheit.jetzt",
    "test-v7-366@ki-sicherheit.jetzt",
    "test-v7-367@ki-sicherheit.jetzt",
    "test-v7-368@ki-sicherheit.jetzt",
    "test-v7-369@ki-sicherheit.jetzt",
    "test-v7-370@ki-sicherheit.jetzt",
    "test-v7-371@ki-sicherheit.jetzt",
    "test-v7-372@ki-sicherheit.jetzt",
    "test-v7-373@ki-sicherheit.jetzt",
    "test-v7-374@ki-sicherheit.jetzt",
    "test-v7-375@ki-sicherheit.jetzt",
    "test-v7-376@ki-sicherheit.jetzt",
    "test-v7-377@ki-sicherheit.jetzt",
    "test-v7-378@ki-sicherheit.jetzt",
    "test-v7-379@ki-sicherheit.jetzt",
    "test-v7-380@ki-sicherheit.jetzt",   ]}

router = APIRouter(prefix="/auth", tags=["auth"])
log = logging.getLogger(__name__)

# Speicher für Codes (Fallback, wenn kein Redis verfügbar)
import threading
_inmem_codes: dict[str, tuple[str, float]] = {}  # email -> (code, expires_at)
_inmem_lock = threading.Lock()

class RequestCodeIn(BaseModel):
    email: EmailStr


class LoginIn(BaseModel):
    email: EmailStr
    code: str


def _store_code(email: str, code: str, ttl_sec: int = 600) -> None:
    s = get_settings()
    if RedisBox.enabled():
        RedisBox.setex(f"login:{email}", ttl_sec, code)
    else:
        with _inmem_lock:
            _inmem_codes[email] = (code, time.time() + ttl_sec)


def _read_code(email: str) -> Optional[str]:
    if RedisBox.enabled():
        return RedisBox.get(f"login:{email}")
    with _inmem_lock:
        data = _inmem_codes.get(email)
        if not data:
            return None
        code, exp = data
        if time.time() > exp:
            _inmem_codes.pop(email, None)
            return None
        return code


@router.post("/request-code", status_code=204, response_model=None)
async def request_code(payload: RequestCodeIn, request: Request):
    """
    Request a login code via email.

    Sends a 6-digit verification code to the provided email address.
    The code is valid for 10 minutes.

    Args:
        payload: Contains the email address to send the code to
        request: FastAPI request object for rate limiting and idempotency

    Raises:
        HTTPException 403: Email not in whitelist (test phase)
        HTTPException 503: Email sending failed

    Returns:
        None (204 No Content on success)
    """
    s = get_settings()
    limiter = RateLimiter(namespace="request_code", limit=s.rate.max_request_code, window_sec=s.rate.window_sec)
    limiter.hit(key=str(payload.email))

    # Whitelist-Prüfung (Testphase)
    email_lower = str(payload.email).lower()
    if email_lower not in EMAIL_WHITELIST:
        log.warning("🚫 Login-Code verweigert für nicht-whitelisted E-Mail: %s", payload.email)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Diese E-Mail-Adresse ist nicht für die Testphase freigeschaltet."
        )

    # Idempotency berücksichtigen (Header: Idempotency-Key)
    idem = IdempotencyBox(namespace="request_code")
    if idem.is_duplicate(request):
        return

    code = f"{secrets.randbelow(1000000):06d}"
    _store_code(str(payload.email), code, ttl_sec=600)

    mailer = Mailer.from_settings(s)
    
    # Build minimal login email (deliverability-first)
    ttl_sec = 600
    mins = max(1, ttl_sec // 60)
    subject = "Ihr Anmeldecode"

    text_template = (
        "Ihr persönlicher Anmeldecode lautet:\n\n"
        f"{code}\n\n"
        f"Der Code ist {mins} Minuten gültig.\n\n"
        "Falls Sie diese Anmeldung nicht angefordert haben, können Sie diese E-Mail ignorieren.\n\n"
        "Kein Code angekommen?\n"
        "• Spam- oder Junk-Ordner prüfen\n"
        "• Code einfach erneut anfordern\n"
        "• Bei Problemen: support@ki-sicherheit.jetzt\n\n"
        "Diese E-Mail gehört zum Login-Prozess von ki-sicherheit.jetzt.\n"
        "Es handelt sich nicht um Werbung.\n\n"
        "– ki-sicherheit.jetzt\n"
    )

    try:
        await mailer.send(
            to=str(payload.email),
            subject=subject,
            text=text_template.strip(),
            html=None,
        )
    except Exception as e:
        log.error("Failed to send login code email to %s: %s", payload.email, str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to send email. Please try again later."
        )
    return


@router.post("/login")
async def login(payload: LoginIn, request: Request, response: Response) -> dict:
    """
    Authenticate user with email and verification code.

    Validates the 6-digit code sent via /request-code and returns a JWT token.
    Also sets an httpOnly cookie for secure authentication.

    Args:
        payload: Email and verification code
        request: FastAPI request object
        response: FastAPI response object for cookie setting

    Returns:
        dict: Contains access_token and token_type

    Raises:
        HTTPException 401: Invalid or expired code
        HTTPException 409: Duplicate request (idempotency)
    """
    s = get_settings()
    limiter = RateLimiter(namespace="login", limit=s.rate.max_login, window_sec=s.rate.window_sec)
    limiter.hit(key=str(payload.email))

    # Idempotency
    idem = IdempotencyBox(namespace="login")
    if idem.is_duplicate(request):
        # Bei echter Idempotenz könnte man hier das vorherige Ergebnis liefern.
        # Für den einfachen Fall: einfach 200 OK ohne Token verhindern wir Doppel-POSTs.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicate request")

    stored = _read_code(str(payload.email))
    if not stored or stored != payload.code:
        log.warning("❌ Login failed for %s: invalid or expired code", payload.email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired code")

    log.info("Creating access token for user: %s", payload.email)
    token = create_access_token(email=str(payload.email))
    log.debug("Token created successfully for user: %s", payload.email)

    # Phase 1: Set httpOnly cookie (hybrid mode)
    # Cookie specs: name=auth_token, httpOnly, Secure, SameSite=None, max_age=3600
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,
        secure=True,  # Only send over HTTPS
        samesite="none",  # Allow cross-site cookies (required for cross-origin requests)
        max_age=3600,  # 1 hour in seconds
        path="/",  # Cookie available for entire domain
    )
    log.info("🍪 Set httpOnly cookie for user: %s", payload.email)

    # Phase 1: Also return token in response body for backward compatibility
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
async def get_me(current_user: TokenPayload = Depends(get_current_user)):
    """
    Get current user information from httpOnly cookie or Authorization header.

    Phase 1 Hybrid Mode: This endpoint accepts authentication via:
    - httpOnly cookie (auth_token) - preferred
    - Authorization header (Bearer token) - fallback

    Returns:
        dict: User information including email and token expiration
    """
    return {
        "email": current_user.email,
        "sub": current_user.sub,
        "exp": current_user.exp,
        "iat": current_user.iat,
    }


@router.post("/logout")
async def logout(response: Response):
    """
    Logout by clearing the authentication cookie.

    This endpoint deletes the httpOnly auth_token cookie, effectively
    logging out the user on the server side.

    Returns:
        dict: Success message
    """
    # Delete the auth_token cookie by setting max_age to 0
    response.delete_cookie(
        key="auth_token",
        path="/",
        httponly=True,
        secure=True,
        samesite="none",
    )
    log.info("🚪 User logged out, cookie cleared")

    return {"ok": True, "message": "Logged out successfully"}
