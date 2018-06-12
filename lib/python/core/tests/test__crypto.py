import pytest

from directorofme.crypto import RSACipher

@pytest.fixture
def private_key():
    return """-----BEGIN RSA PRIVATE KEY-----
MIICXAIBAAKBgQCice5T7hT6WWRW4mD5w4HtWXgLq5hHlzqjfVB5ZCazjWRVH68J
gOYybPEM0DXwfYc+QNqVYHkPOPnmgXce/KMdRx/jAnDulLqbM+kv1Gcj+bMUNDd6
2FNlKeucQe3YxAHN1GqLC94/imjIhJIU8ZlPNUTD5M61fZCF9uBHosRHDwIDAQAB
AoGAGVtbbnJ9h86oYP+ZT6N7Boeuu3Ofo50xpA+NnkVJ3UE25iq58evTAxAKWIuv
v8h4cflBpYuXmg60w4x2AbpB47InSS+CchWRUSv/HAGmF2Vnm7fH10PvPEvJt9Rx
T+Q+zMdWRz4oxHHf2ni1wtZ/mnA/RIEOyXI7hok+W1NtdMECQQC6P5YrUMrhxfYF
bX3PiCqMl8tPaVTQJjJ+ZsegmziXRJfL5FH9kt/NQ4gAzYD1LOelkhibJKp+R3Cj
lExQTZp/AkEA30g32ZZQpIGqGoGzgGOgs8AeHgWtODYAMfMl2wAjA3tFZRaZcGPV
MAAOmhV35vECt3Gv1YS+cmxy2PR7ZxBrcQJAYuxNHZqe98YGgyGBtk3zk5M4SGiA
xMHVBfAfTb3EFAw5t/EAX3e4aTTaMtr0CMUeEIIFkbmq2MGnISsuUWS2jwJBAIDG
wB9oSF54wkjDYWm9DCRfu38JOxxeWMJ2P/ENJSSO5jklTZ26lmw2vDU2CI9TlYOD
uCvngYew8JQcfUe1+qECQGmyAmfpHaAiyc8DvwAa35qwIKoGXwr/chOoz33L9I6E
AArvfT8Gst6rfbb404/QqqFMZhSVTUpE6o4jbfCYc/4=
-----END RSA PRIVATE KEY-----"""

@pytest.fixture
def public_key():
    return """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCice5T7hT6WWRW4mD5w4HtWXgL
q5hHlzqjfVB5ZCazjWRVH68JgOYybPEM0DXwfYc+QNqVYHkPOPnmgXce/KMdRx/j
AnDulLqbM+kv1Gcj+bMUNDd62FNlKeucQe3YxAHN1GqLC94/imjIhJIU8ZlPNUTD
5M61fZCF9uBHosRHDwIDAQAB
-----END PUBLIC KEY-----"""

class TestRSACipher:
    def test__init__(self, private_key, public_key):
        with pytest.raises(ValueError):
            RSACipher()

        assert RSACipher(private_key=private_key).public_key is None, "no public_key is passed, public_key is None"
        assert RSACipher(public_key).private_key is None, "no private_key is passed, private_key is None"

        assert hasattr(RSACipher(public_key).public_key, "encrypt"), "public_key set when passed"
        assert hasattr(RSACipher(public_key, private_key).private_key, "decrypt"), "private_key set when passed"

    def test__encrypt_decrypt(self, public_key, private_key):
        cipher = RSACipher(public_key)
        encrypted = cipher.encrypt("secret")

        assert encrypted != "secret", "encrypted value is not plain text"

        with pytest.raises(AttributeError):
            cipher.decrypt(encrypted)


        assert RSACipher(private_key=private_key).decrypt(encrypted) == "secret", "decryption works"
