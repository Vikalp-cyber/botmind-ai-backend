from app.core.security import create_access_token, decode_token, hash_password, verify_password


def test_password_hash_round_trip():
    password = "super-secret-password"
    digest = hash_password(password)
    assert verify_password(password, digest) is True


def test_jwt_round_trip():
    token = create_access_token("user-1", "tenant-1", "admin")
    payload = decode_token(token)
    assert payload.sub == "user-1"
    assert payload.tenant_id == "tenant-1"
    assert payload.role == "admin"
