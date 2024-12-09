import json
from web3 import Web3
import requests
from eth_account import Account
from eth_account.messages import encode_defunct
from requests_toolbelt.multipart.encoder import MultipartEncoder
from datetime import datetime, timedelta
import time

# Daftar RPC Endpoints
rpc_endpoints = [
    "https://mainnet-rpc-01.swanchain.org",
    "https://mainnet-rpc-02.swanchain.org",
    "https://mainnet-rpc-03.swanchain.org",
    "https://mainnet-rpc-04.swanchain.org",
    "https://rpc-swan-tp.nebulablock.com"
]

# Fungsi untuk koneksi ke Web3
def connect_web3():
    for rpc_url in rpc_endpoints:
        try:
            print(f"Attempting to connect to RPC: {rpc_url}")
            web3 = Web3(Web3.HTTPProvider(rpc_url))
            if web3.is_connected():
                print(f"Successfully connected to RPC: {rpc_url}\n")
                return web3
        except Exception as e:
            print(f"Error connecting to RPC {rpc_url}: {e}")
        time.sleep(2)
    print("Unable to connect to any RPC endpoint.")
    exit()

# Fungsi untuk membaca akun dari file JSON
def load_private_keys(file_path):
    try:
        with open(file_path, 'r') as file:
            private_keys = json.load(file)
            return private_keys
    except Exception as e:
        print(f"Error loading private keys file: {e}")
        exit()

# Fungsi untuk mendapatkan waktu dengan pembulatan 10 menit
def get_rounded_timestamp():
    now = datetime.now()
    rounded_minute = (now.minute // 10) * 10
    if now.minute % 10 >= 10:
        rounded_minute += 10
    rounded_time = now.replace(minute=rounded_minute, second=0, microsecond=0)
    if rounded_minute == 60:
        rounded_time = rounded_time + timedelta(hours=1)
        rounded_time = rounded_time.replace(minute=0)
    return rounded_time, int(rounded_time.timestamp())

# Fungsi untuk mendapatkan token misi
def get_access_token(private_key, web3):
    try:
        sender = Account.from_key(private_key)
        rounded_time, timestamp = get_rounded_timestamp()
        msg = f"Signing in to mission.swanchain.io at {timestamp}"
        message = encode_defunct(text=msg)
        signed_message = web3.eth.account.sign_message(message, private_key=private_key)
        signature = web3.to_hex(signed_message.signature)
        
        url = "https://campaign-api.swanchain.io/wallet_login"
        headers = {
            'Content-Type': 'application/json',
            'Origin': 'https://mission.swanchain.io',
            'Referer': 'https://mission.swanchain.io/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0'
        }
        data = [web3.to_checksum_address(sender.address), signature]
        response = requests.post(url, headers=headers, data=json.dumps(data))
        result = response.json()
        token = result.get('data', {}).get('access_token')
        if not token:
            print(f"Failed to retrieve access token for account {sender.address}.")
            return None
        print(f"Access token retrieved for account: {sender.address}")
        return token
    except Exception as e:
        print(f"Error during get_access_token: {e}")
        return None

# Fungsi untuk DailyCombo
def DailyCombo(sender, token, combo_numbers):
    try:
        combo1, combo2, combo3 = combo_numbers
        url = "https://campaign-api.swanchain.io/task/daily_combo"
        m = MultipartEncoder(fields={
            'number1': str(combo1),
            'number2': str(combo2),
            'number3': str(combo3)
        })
        headers = {
            'Content-Type': m.content_type,
            'Authorization': f'Bearer {token}',
            'Origin': 'https://mission.swanchain.io',
            'Referer': 'https://mission.swanchain.io/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0'
        }
        response = requests.post(url, headers=headers, data=m)
        result = response.json()
        if result.get('status') == 200:
            print("Daily Combo task completed successfully.")
        elif result.get('message') == "Already submitted combo today.":
            print("Combo already submitted. Skipping.")
        else:
            print(f"Daily Combo failed: {result.get('message')}")
    except Exception as e:
        print(f"Error during DailyCombo: {e}")

# Proses semua akun
def process_accounts(private_keys_file, combo_numbers):
    web3 = connect_web3()
    private_keys = load_private_keys(private_keys_file)
    for private_key in private_keys:
        print(f"Processing account with private key: {private_key[:10]}...")
        token = get_access_token(private_key, web3)
        if token:
            sender = Account.from_key(private_key).address
            DailyCombo(sender, token, combo_numbers)

# Menjalankan program utama
if __name__ == "__main__":
    private_keys_file = "private_keys.json"  # File berisi private keys dalam format JSON
    combo_numbers = [7, 9, 12]  # Masukkan angka combo di sini
    process_accounts(private_keys_file, combo_numbers)
