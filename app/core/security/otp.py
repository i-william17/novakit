import io
from base64 import b64encode
import pyotp
import qrcode
from io import BytesIO


def generate_otp_secret():
    return pyotp.random_base32()


class OTPService:

    @staticmethod
    def generate_secret():
        return pyotp.random_base32()

    @staticmethod
    def verify_code(secret: str, code: str):
        totp = pyotp.TOTP(secret)
        return totp.verify(code)

    @staticmethod
    def generate_qr_uri(username: str, secret: str, issuer: str = "NovaKit"):
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=username, issuer_name=issuer)

    @staticmethod
    def generate_qr_image(uri: str):
        qr = qrcode.make(uri)
        buf = BytesIO()
        qr.save(buf, format="PNG")
        return buf.getvalue()

    def get_totp_uri(secret: str, account_name: str, issuer: str):
        return pyotp.totp.TOTP(secret).provisioning_uri(name=account_name, issuer_name=issuer)

    def make_qr_datauri(uri: str):
        img = qrcode.make(uri)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return "data:image/png;base64," + b64encode(buffer.getvalue()).decode()
