import os
import pyotp

otpQR = os.getenv('ODS_REPORT_TOTP')
getOtp = pyotp.TOTP(otpQR)
otp = getOtp.now()
print(otp)