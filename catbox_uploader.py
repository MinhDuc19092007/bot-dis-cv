"""
Catbox Uploader - Upload files lên catbox.moe
Catbox cho phép upload file lên 200MB, lưu vĩnh viễn, miễn phí!
"""
import requests
from typing import Optional, Tuple

def upload_to_catbox(file_path: str, timeout: int = 300) -> Tuple[bool, str]:
    """
    Upload file lên catbox.moe
    
    Args:
        file_path: Đường dẫn file cần upload
        timeout: Timeout (giây)
    
    Returns:
        (success: bool, url_or_error: str)
        - Success: (True, "https://files.catbox.moe/abc123.zip")
        - Fail: (False, "Error message")
    """
    try:
        # Catbox API endpoint
        url = "https://catbox.moe/user/api.php"
        
        # Prepare file
        with open(file_path, 'rb') as f:
            files = {
                'fileToUpload': f,
                'reqtype': (None, 'fileupload')
            }
            
            # Upload
            response = requests.post(url, files=files, timeout=timeout)
            response.raise_for_status()
            
            # Catbox trả về URL trực tiếp
            file_url = response.text.strip()
            
            if file_url.startswith('http'):
                return (True, file_url)
            else:
                return (False, f"Invalid response: {file_url}")
    
    except requests.Timeout:
        return (False, "Upload timeout (quá 5 phút)")
    except requests.RequestException as e:
        return (False, f"Upload error: {str(e)}")
    except Exception as e:
        return (False, f"Unknown error: {str(e)}")

def upload_multiple_to_catbox(file_paths: list, timeout: int = 300) -> dict:
    """
    Upload nhiều files lên Catbox
    
    Args:
        file_paths: List đường dẫn files
        timeout: Timeout cho mỗi file
    
    Returns:
        {
            'success': [(filename, url), ...],
            'failed': [(filename, error), ...]
        }
    """
    import os
    
    results = {
        'success': [],
        'failed': []
    }
    
    for fp in file_paths:
        filename = os.path.basename(fp)
        success, result = upload_to_catbox(fp, timeout)
        
        if success:
            results['success'].append((filename, result))
        else:
            results['failed'].append((filename, result))
    
    return results


# ════════════════════════════════════════════════════════════
#  GOFILE UPLOADER - Fallback khi Catbox fail
# ════════════════════════════════════════════════════════════

def upload_to_gofile(file_path: str, timeout: int = 300) -> Tuple[bool, str]:
    """
    Upload file lên gofile.io (backup khi Catbox fail)
    
    Gofile features:
    - Upload lên 100GB
    - Lưu 10 ngày (free)
    - Unlimited downloads
    - No ads
    
    Args:
        file_path: Đường dẫn file cần upload
        timeout: Timeout (giây)
    
    Returns:
        (success: bool, url_or_error: str)
    """
    try:
        # Step 1: Get best server
        server_response = requests.get("https://api.gofile.io/getServer", timeout=30)
        server_response.raise_for_status()
        server_data = server_response.json()
        
        if server_data.get("status") != "ok":
            return (False, "Cannot get Gofile server")
        
        server = server_data["data"]["server"]
        
        # Step 2: Upload file
        upload_url = f"https://{server}.gofile.io/uploadFile"
        
        with open(file_path, 'rb') as f:
            files = {'file': f}
            
            upload_response = requests.post(upload_url, files=files, timeout=timeout)
            upload_response.raise_for_status()
            
            upload_data = upload_response.json()
            
            if upload_data.get("status") != "ok":
                return (False, f"Upload failed: {upload_data.get('message', 'Unknown error')}")
            
            # Get download link
            download_page = upload_data["data"]["downloadPage"]
            return (True, download_page)
    
    except requests.Timeout:
        return (False, "Gofile upload timeout")
    except requests.RequestException as e:
        return (False, f"Gofile error: {str(e)}")
    except Exception as e:
        return (False, f"Unknown error: {str(e)}")


def upload_with_fallback(file_path: str, timeout: int = 300) -> Tuple[bool, str, str]:
    """
    Upload file với fallback: Catbox → Gofile
    
    Returns:
        (success: bool, url: str, service: str)
        service: 'catbox' hoặc 'gofile'
    """
    import os
    filename = os.path.basename(file_path)
    
    # Try Catbox first
    success, result = upload_to_catbox(file_path, timeout)
    if success:
        return (True, result, 'catbox')
    
    # Fallback to Gofile
    print(f"⚠️  Catbox failed for {filename}, trying Gofile...")
    success, result = upload_to_gofile(file_path, timeout)
    if success:
        return (True, result, 'gofile')
    
    # Both failed
    return (False, f"Both Catbox and Gofile failed", 'none')


def upload_multiple_with_fallback(file_paths: list, timeout: int = 300) -> dict:
    """
    Upload nhiều files với fallback tự động
    
    Returns:
        {
            'success': [(filename, url, service), ...],
            'failed': [(filename, error), ...]
        }
    """
    import os
    
    results = {
        'success': [],
        'failed': []
    }
    
    for fp in file_paths:
        filename = os.path.basename(fp)
        success, result, service = upload_with_fallback(fp, timeout)
        
        if success:
            results['success'].append((filename, result, service))
        else:
            results['failed'].append((filename, result))
    
    return results
