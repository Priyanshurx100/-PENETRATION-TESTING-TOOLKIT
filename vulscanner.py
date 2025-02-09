import requests
import re
from urllib.parse import urljoin
from colorama import init, Fore
import time
import json

init()  # Initialize colorama for colored terminal text

# Constants
XSS_PAYLOADS = [
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert('XSS')>",
    "<svg onload=alert('XSS')>"
]
SQL_PAYLOADS = [
    "' OR '1'='1",
    "' OR SLEEP(5) --",
    "' UNION SELECT null,null --"
]
RATE_LIMIT_DELAY = 1  # Delay between requests in seconds

def check_security_headers(url):
    headers_to_check = [
        'X-Frame-Options',
        'Content-Security-Policy',
        'Strict-Transport-Security',
        'X-Content-Type-Options',
        'Referrer-Policy',
        'Permissions-Policy'
    ]
    try:
        response = requests.get(url)
        print(f"{Fore.CYAN}\nChecking security headers for {url}:{Fore.RESET}")
        for header in headers_to_check:
            if header in response.headers:
                print(f"{Fore.GREEN}[+] {header}: {response.headers[header]}{Fore.RESET}")
                if header == 'Content-Security-Policy':
                    validate_csp(response.headers[header])
            else:
                print(f"{Fore.RED}[-] {header} is missing{Fore.RESET}")
    except requests.RequestException as e:
        print(f"{Fore.RED}Error checking security headers: {e}{Fore.RESET}")

def validate_csp(csp_header):
    """Validate Content-Security-Policy header."""
    if "default-src 'none'" not in csp_header:
        print(f"{Fore.YELLOW}[!] Content-Security-Policy is not restrictive: {csp_header}{Fore.RESET}")

def check_common_vulnerabilities(url):
    print(f"{Fore.CYAN}\nChecking for common vulnerabilities:{Fore.RESET}")
    try:
        response = requests.get(url)
        # Check for X-Powered-By header
        if 'X-Powered-By' in response.headers:
            print(f"{Fore.YELLOW}[!] X-Powered-By header found: {response.headers['X-Powered-By']}{Fore.RESET}")
        
        # Check for Server header
        if 'Server' in response.headers:
            print(f"{Fore.YELLOW}[!] Server header found: {response.headers['Server']}{Fore.RESET}")
        
        # Check for directory listing
        if "Index of /" in response.text:
            print(f"{Fore.RED}[!] Directory listing is enabled{Fore.RESET}")
        
        # Check for insecure cookies
        if 'Set-Cookie' in response.headers:
            cookies = response.headers['Set-Cookie']
            if 'Secure' not in cookies or 'HttpOnly' not in cookies:
                print(f"{Fore.RED}[!] Insecure cookies detected: {cookies}{Fore.RESET}")
        
        # Check for potential XSS
        for payload in XSS_PAYLOADS:
            test_url = urljoin(url, f"?q={payload}")
            xss_response = requests.get(test_url)
            if payload in xss_response.text:
                print(f"{Fore.RED}[!] Potential XSS vulnerability detected with payload: {payload}{Fore.RESET}")
                break
        
        # Check for potential SQL Injection
        for payload in SQL_PAYLOADS:
            test_url = urljoin(url, f"?id={payload}")
            sql_response = requests.get(test_url)
            if "error" in sql_response.text.lower() or "sql" in sql_response.text.lower():
                print(f"{Fore.RED}[!] Potential SQL Injection vulnerability detected with payload: {payload}{Fore.RESET}")
                break
        
        # Check for CSRF token
        if 'csrf' in response.text.lower() or 'csrf_token' in response.text.lower():
            print(f"{Fore.YELLOW}[!] CSRF token found in response{Fore.RESET}")
        
        # Check for clickjacking vulnerability
        if 'X-Frame-Options' not in response.headers:
            print(f"{Fore.RED}[!] Clickjacking vulnerability detected (missing X-Frame-Options header){Fore.RESET}")
        
    except requests.RequestException as e:
        print(f"{Fore.RED}Error checking vulnerabilities: {e}{Fore.RESET}")

def check_ssl_tls(url):
    print(f"{Fore.CYAN}\nChecking SSL/TLS configuration:{Fore.RESET}")
    try:
        response = requests.get(url)
        if response.url.startswith('https://'):
            print(f"{Fore.GREEN}[+] HTTPS is enabled{Fore.RESET}")
            # Perform deeper SSL/TLS analysis (e.g., using sslyze or ssl library)
        else:
            print(f"{Fore.RED}[-] HTTPS is not enabled{Fore.RESET}")
    except requests.RequestException as e:
        print(f"{Fore.RED}Error checking SSL/TLS: {e}{Fore.RESET}")

def scan_vulnerabilities(url):
    print(f"{Fore.BLUE}\nStarting vulnerability scan for {url}...{Fore.RESET}")
    check_security_headers(url)
    check_common_vulnerabilities(url)
    check_ssl_tls(url)
    print(f"{Fore.BLUE}\nVulnerability scan completed.{Fore.RESET}")

if __name__ == "__main__":
    url = input("Enter target URL: ")
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url  # Default to HTTP if no scheme is provided
    scan_vulnerabilities(url)