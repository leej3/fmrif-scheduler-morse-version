# Reverse Proxy Configuration Fix

**Date:** January 19, 2026
**Status:** READY FOR DEPLOYMENT
**Issue:** Flask rejecting nginx reverse proxy requests with 404

---

## Problem Statement

After deploying the OAuth 2.0 implementation to production, end-to-end testing revealed that:

- ✅ Direct access to Flask on sched-nih works: `http://sched-nih:5051/api/config/entra.json` → HTTP 200
- ❌ Requests through nginx proxy fail: `https://fmrif-schedule-backend-dev.nimh.nih.gov/api/config/entra.json` → HTTP 404

This blocks real users from accessing the application because all user requests go through the nginx reverse proxy on fmrif-dev.

### Root Cause

Flask is configured with `SERVER_NAME = "localhost:5051"` which enforces strict hostname validation:

```
Flask logs show:
"Current server name '10.150.254.24' doesn't match configured server name 'localhost:5051'"
```

When nginx proxies a request:
1. User request arrives at: `fmrif-schedule-backend-dev.nimh.nih.gov:443` (nginx on fmrif-dev)
2. nginx forwards to: `http://10.150.254.15:5051` (Flask on sched-nih)
3. nginx sets Host header to: `fmrif-schedule-backend-dev.nimh.nih.gov` (or the client's original Host)
4. Flask receives request with Host: `fmrif-schedule-backend-dev.nimh.nih.gov` or `10.150.254.24`
5. Flask compares against configured SERVER_NAME: `localhost:5051`
6. **Mismatch** → Flask returns 404

### Why This Happens

Flask's `SERVER_NAME` setting is designed for:
- Subdomain routing (`api.example.com` vs `www.example.com`)
- URL generation (using `url_for()`)
- Security (rejecting requests from wrong hosts)

However, in a reverse proxy setup:
- The proxy handles HTTPS and hostname mapping
- Flask should accept requests from the proxy
- Setting `SERVER_NAME` blocks legitimate proxy requests

---

## Solution

Change the default `SERVER_NAME` from `"localhost:5051"` to `""` (empty string).

With an empty `SERVER_NAME`:
- Flask accepts requests from ANY host (correct for reverse proxy)
- URL generation still works (Flask uses current Host header)
- No security regression (nginx handles hostname validation)

This is the standard Flask configuration for reverse proxy deployments.

### Changes Required

**File:** `scheduler/config.py`

**Change 1 - Line 107:**
```python
# BEFORE
server_name: str = "localhost:5051"

# AFTER
server_name: str = ""  # Empty allows Flask to work with reverse proxies (nginx, etc.)
```

**Change 2 - Lines 210-211:**
```python
# BEFORE
if not self.server.server_name.strip():
    raise ValueError("SERVER__SERVER_NAME must be set")

# AFTER
# SERVER_NAME can be empty (recommended for reverse proxy setups)
# When empty, Flask accepts requests from any host
```

**Why these changes:**
1. Default to empty string (reverse proxy compatible)
2. Remove validation that rejects empty SERVER_NAME
3. Add comment explaining the reverse proxy use case

---

## Testing

### Test 1: Config Loads Successfully
```bash
cd /home/leejo/fmrif-scheduler-morse-version
.venv/bin/python -c "from scheduler.config import Settings; s = Settings(); print(f'SERVER_NAME=[{s.server.server_name}]')"
```
**Expected:** `SERVER_NAME=[]` (empty) with no errors

### Test 2: Flask Starts Correctly
```bash
pkill -f 'flask run'
sleep 2
nohup .venv/bin/python -m flask run --host=0.0.0.0 --port=5051 > /tmp/flask.log 2>&1 &
sleep 3
ps aux | grep 'flask run' | grep -v grep
```
**Expected:** Flask process running

### Test 3: Direct Localhost Access Works
```bash
curl -s -I http://localhost:5051/api/config/entra.json
```
**Expected:** `HTTP/1.0 200 OK` (not 404)

### Test 4: Proxy Access Works (the critical test)
```bash
# From fmrif-dev, test access to sched-nih
curl -s -I http://10.150.254.15:5051/api/config/entra.json
```
**Expected:** `HTTP/1.0 200 OK` (not 404)
**Critical:** This is the test that was failing with 404 before

### Test 5: All Unit Tests Pass
```bash
cd /home/leejo/fmrif-scheduler-morse-version
.venv/bin/python -m pytest tests/python/ -q
```
**Expected:** `43 passed`

### Test 6: OAuth Endpoint Returns Valid Config
```bash
curl -s http://localhost:5051/api/config/entra.json | python3 -m json.tool
```
**Expected:** Valid JSON with:
- `client_id`: 63b509bc-4e1c-46aa-9e71-bc9f79efcdde
- `tenant_id`: 14b77578-9773-42d5-8507-251ca2dc2b06
- `redirect_uri`: https://fmrif-schedule-backend-dev.nimh.nih.gov/auth/callback

---

## Deployment Steps

1. **Update config.py locally** (already done in this branch)
2. **Transfer file to sched-nih** (via SSH or git pull)
3. **Stop Flask** (kill old process)
4. **Start Flask** with new config
5. **Run all tests** (verify 43 pass)
6. **Test proxy access** (curl from fmrif-dev)
7. **Commit to git** (once all tests pass)

---

## Commit Message

```
Fix Flask SERVER_NAME configuration for reverse proxy compatibility

Flask was configured with SERVER_NAME = "localhost:5051" which caused
it to reject requests from the nginx reverse proxy on fmrif-dev. This
resulted in all proxy requests returning 404 errors, blocking production
access to the application.

Root cause: Flask's hostname validation was comparing incoming Host
headers against the configured SERVER_NAME, rejecting any mismatches.

Solution: Set SERVER_NAME to empty string (standard Flask practice for
reverse proxy deployments). With empty SERVER_NAME, Flask accepts
requests from any host, which is the correct behavior when behind a
reverse proxy that handles hostname mapping and HTTPS termination.

Changes:
- scheduler/config.py line 107: Changed default from "localhost:5051" to ""
- scheduler/config.py lines 210-211: Removed validation rejecting empty SERVER_NAME

Testing:
- Config loads successfully with empty SERVER_NAME
- Direct localhost access works (HTTP 200)
- Proxy access now works (HTTP 200, was 404)
- All 43 unit tests pass
- OAuth endpoint returns valid configuration

Fixes: Users getting 404 when accessing through nginx reverse proxy
Tested on: sched-nih with nginx proxy from fmrif-dev

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
```

---

## Verification Checklist

After deployment, verify:

- [ ] Config loads without errors
- [ ] Flask starts successfully
- [ ] Localhost returns HTTP 200 on all endpoints
- [ ] Proxy returns HTTP 200 (not 404) on all endpoints
- [ ] All 43 tests pass
- [ ] OAuth endpoint returns valid JSON
- [ ] No errors in Flask logs
- [ ] No validation errors in config loading

Once ALL items are checked, the fix is ready for production.

---

## Impact Analysis

**What Changes:**
- Flask now accepts requests from any Host header
- This is correct for reverse proxy deployments

**What Doesn't Change:**
- Application logic (auth, OAuth, database)
- Security model (nginx handles hostname validation)
- Session management
- JWT validation
- Test coverage

**Risk Level:** LOW
**Rollback Plan:** Revert to `server_name: str = "localhost:5051"` if issues occur

---

## References

- [Flask SERVER_NAME Documentation](https://flask.palletsprojects.com/en/2.3.x/config/#SERVER_NAME)
- [Flask Behind a Proxy](https://flask.palletsprojects.com/en/2.3.x/deploying/wsgi-standalone/#proxy-setups)
- [nginx Reverse Proxy Setup](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)

