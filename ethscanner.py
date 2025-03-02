import os
import hashlib
import ecdsa
import requests
import sys
import time
import threading
from termcolor import colored
from concurrent.futures import ThreadPoolExecutor

# --- توابع تولید آدرس‌ها ---
def generate_private_key():
    return os.urandom(32).hex()

def private_to_public(private_hex):
    sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_hex), curve=ecdsa.SECP256k1)
    vk = sk.verifying_key
    return b'\x04' + vk.to_string()

def private_to_address(private_hex):
    public_key = private_to_public(private_hex)
    sha256_public_key = hashlib.sha256(public_key).digest()
    ripemd160_public_key = hashlib.new('ripemd160', sha256_public_key).digest()
    return '0x' + ripemd160_public_key.hex()

# --- بررسی موجودی با Etherscan ---
def check_balance(address):
    try:
        etherscan_api_key = "AG1KPAJGQYTXQX8BCBWDR4EJZBW8AHKAYW"  # کلید API شما
        response = requests.get(
            f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={etherscan_api_key}",
            timeout=10,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        response.raise_for_status()  # بررسی خطاهای HTTP
        result = response.json().get('result')
        if result == "Invalid API Key":
            return "Etherscan Error: Invalid API Key"
        balance = int(result)
        return balance / 10**18  # تبدیل از Wei به Ether
    except requests.exceptions.RequestException as e:
        return f"Etherscan Error: {e}"

# --- شمارنده و قفل برای هماهنگی در چاپ ---
counter = 0
counter_lock = threading.Lock()

# --- تابع پردازش هر آدرس ---
def process_address():
    global counter
    private_hex = generate_private_key()
    address = private_to_address(private_hex)
    balance = check_balance(address)
    
    with counter_lock:
        counter += 1
        current_count = counter

    # آماده‌سازی رشته خروجی
    if isinstance(balance, (int, float)):
        balance_str = f"{balance} ETH"
    else:
        balance_str = colored(balance, 'red')
    
    # چاپ نتیجه بررسی (آدرس‌های قبلی پاک نمی‌شوند)
    print(f"#{current_count} | Private Key: {private_hex} | Address: {address} | Balance: {balance_str}")

    # در صورت یافتن موجودی مثبت، اطلاعات را ذخیره و برنامه را خاتمه می‌دهد
    if isinstance(balance, (int, float)) and balance > 0:
        print("\n\n!!! موجودی یافت شد !!!")
        print(f"کلید خصوصی (Hex): {private_hex}")
        print(f"آدرس: {address}")
        print(f"موجودی: {balance} ETH")
        with open('found_eth.txt', 'a') as f:
            f.write(f"Private Key (Hex): {private_hex}\n")
            f.write(f"Address: {address}\n")
            f.write(f"موجودی: {balance} ETH\n\n")
        sys.exit(0)

# --- اجرای اصلی ---
def main():
    try:
        # استفاده از ThreadPoolExecutor با تعداد بیشینه نخ‌ها
        with ThreadPoolExecutor(max_workers=20) as executor:
            while True:
                # در هر ثانیه ۵ وظیفه (تسک) به صورت همزمان اجرا می‌شود
                for _ in range(5):
                    executor.submit(process_address)
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nعملیات توسط کاربر لغو شد.")

if __name__ == "__main__":
    print("""
    ███████╗████████╗██╗  ██╗██████╗ ███████╗
    ██╔════╝╚══██╔══╝██║  ██║██╔══██╗██╔════╝
    █████╗     ██║   ███████║██████╔╝█████╗  
    ██╔══╝     ██║   ██╔══██║██╔══██╗██╔══╝  
    ███████╗   ██║   ██║  ██║██║  ██║███████╗
    ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝
    """)
    main()
