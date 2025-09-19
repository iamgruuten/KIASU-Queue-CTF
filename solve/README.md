# Kiasu Queue System — Write‑up

## Goal
Obtain the full flag:

```
flag{K1asu_SQ1_Unl33sh3d_G1tHub_0S1NT_R3v3al}
```

## Steps

1. **Join the queue** to receive a `user_id` UUID and a guest JWT.
2. Exploit **SQL injection** in `/admin-kiasu-interface` to:
   * Leak PostgreSQL version.
   * Dump the admin MD5 hash.
   * Update your row in `queue_positions` so `position = 1` (reveals first half of flag).
3. Inspect the HTML/SVG to find a **base64‑encoded secret key**. Corroborate via GitHub commits (OSINT).
4. Forge an **admin JWT** with `{"user":"admin","uuid":"<YOUR_UUID>"}` signed with the leaked key.
5. Access `/admin-dashboard` using the forged cookie to obtain the second half of the flag.
