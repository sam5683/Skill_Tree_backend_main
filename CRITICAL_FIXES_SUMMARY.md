# 🔴 CRITICAL FIXES FOR RENDER DEPLOYMENT
## 3 Issues That MUST Be Fixed Before Going Live

---

## FIX #1: Database Connection Pooling (2 minutes)

**File:** `app/db/session.py`

**Current (Lines 6-11):**
```python
engine = create_engine(
    settings.DATABASE_URL,
    future=True,
    echo=False
)
```

**Change To:**
```python
engine = create_engine(
    settings.DATABASE_URL,
    future=True,
    echo=False,
    # Production connection pooling
    pool_size=15,              # Keep 15 connections ready
    max_overflow=10,           # Allow 10 overflow (bursts)
    pool_recycle=280,          # Recycle every 280s (Supabase closes at 600s)
    pool_pre_ping=True,        # Test connection before using
)
```

**Why:** Without this, Supabase closes idle connections after 600s, causing "connection closed" errors. Render will timeout.

**Render Impact:** REQUIRED or service will crash on any traffic

---

## FIX #2: Cookie Configuration for HTTPS (5 minutes)

**File:** `app/api/v1/auth.py`

**Current (Lines 43-49):**
```python
response.set_cookie(
    key="access_token",
    value=token,
    httponly=True,
    secure=True,
    samesite="None",
    max_age=60 * 60 * 24,
    path="/"
)
```

**Change To:**
```python
from app.core.config import settings

# ... in login function ...
# Production (Render uses HTTPS)
if settings.ENVIRONMENT == "production":
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="Lax",  # Changed from "None"
        max_age=60 * 60 * 24,
        path="/"
    )
else:
    # Development (localhost HTTP)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,
        samesite="Lax",
        max_age=60 * 60 * 24,
        path="/"
    )
```

**Do the same for logout** (line ~61):
```python
@router.post("/auth/logout")
def logout(response: Response):
    if settings.ENVIRONMENT == "production":
        response.delete_cookie(
            key="access_token",
            path="/",
            samesite="Lax",
            secure=True
        )
    else:
        response.delete_cookie(
            key="access_token",
            path="/",
            samesite="Lax",
            secure=False
        )
    return {"message": "Logged out successfully"}
```

**Why:** Render uses HTTPS. `samesite="None"` without proper setup causes browsers to DROP the cookie. Users can't stay logged in.

**Render Impact:** REQUIRED or login will fail

---

## FIX #3: Set ENVIRONMENT Variable (2 minutes)

**In Render Dashboard:**

1. Go to your service settings
2. Find "Environment" section
3. Add new variable:
   - **Key:** `ENVIRONMENT`
   - **Value:** `production`

**Or use render.yaml:**
```yaml
services:
  - type: web
    name: skilltree-api
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: DATABASE_URL
        fromDatabase:
          name: skilltree-db
          property: connectionString
      # ... other vars ...
```

**File also needs update:** `app/core/config.py`

**Current (Line 17):**
```python
ENVIRONMENT: str = "development"  # ✗ HARDCODED
```

**Change To:**
```python
ENVIRONMENT: str  # ✗ No default - required
```

**Why:** Without `ENVIRONMENT=production`, all settings default to dev behavior. Cookies fail, logging breaks, security is compromised.

**Render Impact:** REQUIRED for production behavior

---

## Quick Checklist

- [ ] Fix #1: Add pooling config to `app/db/session.py`
- [ ] Fix #2: Update cookie logic in `app/api/v1/auth.py` (2 places: login + logout)
- [ ] Fix #3: Remove default from `app/core/config.py` + Set in Render dashboard
- [ ] Test: Login on Render → Check cookies are sent
- [ ] Verify: `ENVIRONMENT=production` appears in app logs

---

## Test Commands

Before pushing to Render:

```bash
# Start locally with production config
ENVIRONMENT=production uvicorn app.main:app --reload

# Test login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test&password=test" \
  -v  # Shows headers including Set-Cookie

# Check for cookie
# Should see: Set-Cookie: access_token=...; HttpOnly; Secure; SameSite=Lax

# Protected endpoint
curl http://localhost:8000/api/v1/notes \
  -H "Cookie: access_token=YOUR_TOKEN"
```

---

## Deployment Flow

1. **Apply all 3 fixes locally**
2. **Test with:** `ENVIRONMENT=production uvicorn app.main:app --reload`
3. **Push to GitHub**
4. **Render auto-deploys**
5. **Add `ENVIRONMENT=production` in Render dashboard** → Service auto-restarts
6. **Verify login works** on production URL
7. **Done!** 🎉

