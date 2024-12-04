# Brute Force Bypass with Rate Limiting and Alternating Bypass

This Python script demonstrates techniques to bypass rate limiting during brute-force attacks and perform username enumeration and password guessing on vulnerable login forms. It includes tools to spoof IPs, randomize headers, and rotate proxies.

---

## Features

- **Username Enumeration via Response Timing:** Identify valid usernames based on response times.
- **Rate Limiting Bypass:** Spoof IP addresses and alternate login attempts to bypass brute-force protections.
- **Password Brute Forcing:** Test passwords against identified usernames.
- **Proxy Support:** Route traffic through Burp Suite or a custom proxy.
- **SSL Verification:** Supports custom CA certificates for secure communication.

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-folder>
```

### 2. Install Dependencies

Create a virtual environment and install the required Python modules.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Certificates

- **Custom CA Certificate:**
  Save the complete certificate chain used by your proxy (e.g., Burp Suite) in `certs/burp_cacert_chain.pem`.
  - Combine your custom CA and the default CA bundle:
    ```bash
    cat /path/to/custom_ca.pem >> certs/burp_cacert_chain.pem
    ```
  - Keep the file updated to prevent certificate expiration issues.

---

## Usage

Run the script with the target URL as a command-line argument:

```bash
python brute_bypass.py <target_url>
```

For example:
```bash
python brute_bypass.py https://example.com/login
```

### Example File Structure:
```plaintext
project/
├── brute_bypass.py
├── certs/
│   └── burp_cacert_chain.pem
├── res/
│   ├── usernames.txt
│   └── passwords.txt
└── requirements.txt
```

---

## Script Options

### Brute Force Protection Bypass
Modify the section in `main()` to enable the **Broken Brute-Force Protection Lab**:

```python
valid_user = "wiener"
valid_password = "peter"
username_target = "carlos"
alternating_brute_force(url, session, cookies, valid_user, valid_password, username_target)
```

### Username Enumeration via Timing
Enable the **Username Enumeration Lab**:

```python
long_password = "howdy" * 20
username = find_username_bypass_rate_limit(url, session, cookies, long_password, ca_cert_path)
```

---

## Advanced Features

### Proxy Configuration
Modify `get_proxies()` to use either:
- Burp Suite (`http://127.0.0.1:8080`)
- ScraperAPI or other services for anonymity.

### IP Spoofing
Random IPs are generated using the `X-Forwarded-For` header:
```python
def generate_random_ip():
    return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"
```

---

## Important Notes

- **Ethical Use Only:** Use this script for testing and educational purposes on authorized systems.
- **Proxy Warnings:** Routing traffic through Tor or public proxies can expose your data to malicious nodes.
- **CA Certificate:** Ensure your CA certificate includes the full chain to avoid SSL errors.

---

## SSL Troubleshooting

### Combining Certificates:
If using Burp Suite, append your CA chain:
```bash
cat /etc/ssl/certs/ca-certificates.crt >> certs/burp_cacert_chain.pem
```

### Test SSL with `openssl`:
```bash
openssl s_client -connect <target_host>:443 -showcerts
```

---

## Contributing

Feel free to fork and contribute to the project. Open issues for bugs or feature requests.

---

## Disclaimer

This tool is intended for educational purposes only. Unauthorized use against systems you do not own or have explicit permission to test is illegal.
