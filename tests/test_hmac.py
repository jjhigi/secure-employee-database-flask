import hashlib
import hmac

import pytest

import AddAPayRaiseServer
import ProcessPayRaiseDeletionsServer
from config import HMAC_SECRET


@pytest.mark.parametrize(
    "verify_hmac",
    [
        AddAPayRaiseServer.verify_hmac,
        ProcessPayRaiseDeletionsServer.verify_hmac,
    ],
)
def test_verify_hmac_accepts_valid_tag(verify_hmac):
    message = b"1^%$2025-01-31^%$123.45"
    tag = hmac.new(HMAC_SECRET, message, digestmod=hashlib.sha3_512).digest()

    assert verify_hmac(message, tag)


@pytest.mark.parametrize(
    "verify_hmac",
    [
        AddAPayRaiseServer.verify_hmac,
        ProcessPayRaiseDeletionsServer.verify_hmac,
    ],
)
def test_verify_hmac_rejects_tampered_message(verify_hmac):
    message = b"1^%$2025-01-31^%$123.45"
    tampered_message = b"1^%$2025-01-31^%$999.99"
    tag = hmac.new(HMAC_SECRET, message, digestmod=hashlib.sha3_512).digest()

    assert not verify_hmac(tampered_message, tag)
