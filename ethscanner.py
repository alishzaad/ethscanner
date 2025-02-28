import os
import hashlib
import ecdsa
import requests
import sys
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

# --- بررسی موجودی با Infura ---
def check_balance_infura(address):
    try:
        infura_url = "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"  # جایگزین کنید با Project ID خودتان
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getBalance",
            "params": [address, "latest"],
            "id": 1
        }
        response = requests.post(infura_url, json=payload, timeout=10)
        response.raise_for_status()
        balance_hex = response.json().get('result', '0x0')
        return int(balance_hex, 16) / 10**18  # تبدیل از Wei به Ether
    except requests.exceptions.RequestException as e:
        return f"Infura Error: {e}"

# --- بررسی موجودی با Etherscan (اختیاری) ---
def check_balance_etherscan(address):
    try:
        etherscan_api_key = "YOUR_ETHERSCAN_API_KEY"  # جایگزین کنید با API Key خودتان
        response = requests.get(
            f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={etherscan_api_key}",
            timeout=10,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        response.raise_for_status()
        result = response.json().get('result')
        if result == "Invalid API Key":
            return "Etherscan Error: Invalid API Key"
        balance = int(result)
        return balance / 10**18  # تبدیل از Wei به Ether
    except requests.exceptions.RequestException as e:
        return f"Etherscan Error: {e}"

def check_balance(address):
    # اول از Infura استفاده می‌کنیم
    infura_balance = check_balance_infura(address)
    if isinstance(infura_balance, (int, float)):
        return infura_balance
    # اگر Infura خطا داد، از Etherscan استفاده می‌کنیم
    etherscan_balance = check_balance_etherscan(address)
    if isinstance(etherscan_balance, (int, float)):
        return etherscan_balance
    return f"{infura_balance} | {etherscan_balance}"

# --- اجرای اصلی ---
def main():
    try:
        while True:
            private_hex = generate_private_key()
            address = private_to_address(private_hex)
            
            # بررسی موجودی
            balance = check_balance(address)
            
            # نمایش اطلاعات در ترمینال
            sys.stdout.write("\033[K")  # پاک کردن خط قبلی
            status = f"Private Key: {private_hex} | Address: {address[:10]}... | Balance: "
            if isinstance(balance, (int, float)):
                status += f"{balance} ETH"
            else:
                status += colored(balance, 'red')  # نمایش خطا با رنگ قرمز
            print(f"\r{status}", end="", flush=True)
            
            # بررسی موجودی و خطاها
            if isinstance(balance, (int, float)) and balance > 0:
                print("\n\n!!! موجودی یافت شد !!!")
                print(f"کلید خصوصی (Hex): {private_hex}")
                print(f"آدرس: {address}")
                print(f"موجودی: {balance} ETH")
                
                # ذخیره اطلاعات در فایل
                with open('found_eth.txt', 'a') as f:
                    f.write(f"Private Key (Hex): {private_hex}\n")
                    f.write(f"Address: {address}\n")
                    f.write(f"Balance: {balance} ETH\n\n")
                sys.exit(0)
            elif isinstance(balance, str):  # نمایش خطاها
                print(f"\n\n!!! خطا !!!")
                print(f"آدرس: {address}")
                print(colored(f"خطا: {balance}", 'red'))
                
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
