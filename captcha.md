# Captcha

Ourchive currently supports [hCaptcha](https://www.hcaptcha.com/), a privacy-first CAPTCHA service with a free tier.

CAPTCHA is enabled through your environment settings. When you sign up for hcaptcha, you will be given two values: a site key and a secret key. The site key is used by the site; the secret key is used for verification. Keep these values somewhere safe, like a password manager.

The following values should be modified in your .env file or environment variables [tk - add details for managed services]:

'''
OURCHIVE_CAPTCHA_SITE_KEY=[change to site key from hcaptcha]
OURCHIVE_USE_CAPTCHA=True
OURCHIVE_CAPTCHA_PROVIDER=hcaptcha
OURCHIVE_CAPTCHA_PARAM=h-captcha-response
OURCHIVE_CAPTCHA_SECRET=[change to secret from hcaptcha]
'''

Captcha is used for anonymous comments. **If you have anonymous comments enabled we strongly recommend using captcha.**

Our assumption is that site users are trusted people who aren't bots. Please refer to our [tk add link]config documentation for advice on preventing spam comments & signups.