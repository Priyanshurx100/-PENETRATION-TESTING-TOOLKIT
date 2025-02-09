import socket
import threading
import time
from colorama import init, Fore
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

init()  # Initialize colorama for colored terminal text

def get_service_name(port):
    try:
        return socket.getservbyport(port)
    except OSError:
        return "Unknown"

def grab_banner(ip, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(2)
            sock.connect((ip, port))
            sock.send(b"GET / HTTP/1.1\r\n\r\n")
            banner = sock.recv(1024).decode().strip()
            return banner
    except Exception:
        return None

def port_scan(target, port, results, lock):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((target, port))
            with lock:
                if result == 0:
                    service = get_service_name(port)
                    banner = grab_banner(target, port)
                    if banner:
                        results[port] = f"{Fore.GREEN}Port {port} is open - Service: {service} - Banner: {banner}{Fore.RESET}"
                    else:
                        results[port] = f"{Fore.GREEN}Port {port} is open - Service: {service}{Fore.RESET}"
                else:
                    results[port] = f"{Fore.RED}Port {port} is closed{Fore.RESET}"
    except Exception as e:
        with lock:
            results[port] = f"{Fore.YELLOW}Error scanning port {port}: {str(e)}{Fore.RESET}"

def scan_ports(target, ports, max_threads=100, speed=0.1):
    results = {}
    lock = threading.Lock()
    futures = []
    
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        for port in ports:
            future = executor.submit(port_scan, target, port, results, lock)
            futures.append(future)
            if speed > 0:
                time.sleep(speed)  # Control the speed of scan

        for future in as_completed(futures):
            future.result()  # Wait for all threads to complete

    return results

if __name__ == "__main__":
    target = input("Enter target IP or hostname: ")
    ports_input = input("Enter ports to scan (comma-separated, e.g., 22,80,443) or range (e.g., 1-1000): ")
    
    if '-' in ports_input:
        start, end = map(int, ports_input.split('-'))
        ports = list(range(start, end + 1))
    else:
        ports = [int(port) for port in ports_input.split(',')]

    max_threads = int(input("Enter maximum number of threads (default 100): ") or "100")
    speed = float(input("Enter scan speed (delay between threads, 0 for max speed): ") or "0.1")

    print(f"Scanning {target} on ports {ports_input}...")
    start_time = time.time()
    scan_results = scan_ports(target, ports, max_threads, speed)
    
    sorted_results = sorted(scan_results.items(), key=lambda x: x[0])
    
    print("\nScan Results:")
    for port, result in sorted_results:
        print(result)
    
    duration = time.time() - start_time
    print(f"\nScan completed in {duration:.2f} seconds.")

    # Save results to file
    # Sanitize filename by removing invalid characters
    safe_filename = re.sub(r'[<>:"/\\|?*]', '_', target)
    with open(f"scan_results_{safe_filename}.txt", 'w') as file:
        for port, result in sorted_results:
            file.write(result + '\n')
    print(f"Results saved to scan_results_{safe_filename}.txt")