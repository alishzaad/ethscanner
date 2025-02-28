import os
import hashlib
import ecdsa
import requests
import sys
from termcolor import colored

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
