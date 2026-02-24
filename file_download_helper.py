"""
Helper functions để download file từ nhiều nguồn
"""
import requests
import re
from urllib.parse import urlparse, parse_qs

def detect_file_source(url: str) -> str:
    """
    Phát hiện nguồn file từ URL.
    Returns: 'onedrive', 'dropbox', 'google_drive', 'direct', hoặc 'unknown'
    """
    url_lower = url.lower()
    
    if 'onedrive' in url_lower or '1drv.ms' in url_lower or 'sharepoint' in url_lower:
        return 'onedrive'
    elif 'dropbox' in url_lower:
        return 'dropbox'
    elif 'drive.google.com' in url_lower or 'docs.google.com' in url_lower:
        return 'google_drive'
    elif url_lower.endswith('.zip'):
        return 'direct'
    else:
        return 'unknown'

def get_direct_download_url(url: str, source: str) -> str:
    """
    Chuyển đổi URL chia sẻ thành direct download URL.
    
    Args:
        url: URL gốc
        source: Loại nguồn (onedrive, dropbox, google_drive, direct)
    
    Returns:
        Direct download URL
    """
    if source == 'onedrive':
        # OneDrive: thêm &download=1 hoặc chuyển embed thành download
        if 'embed' in url:
            return url.replace('embed', 'download')
        elif '?' in url:
            return url + '&download=1'
        else:
            return url + '?download=1'
    
    elif source == 'dropbox':
        # Dropbox: thay ?dl=0 thành ?dl=1
        if 'dl=0' in url:
            return url.replace('dl=0', 'dl=1')
        elif '?' in url:
            return url + '&dl=1'
        else:
            return url + '?dl=1'
    
    elif source == 'google_drive':
        # Google Drive: extract file ID và tạo direct URL
        # Format: https://drive.google.com/file/d/FILE_ID/view
        # Direct: https://drive.google.com/uc?export=download&id=FILE_ID
        
        # Try to extract file ID
        file_id = None
        
        # Pattern 1: /file/d/FILE_ID
        match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
        if match:
            file_id = match.group(1)
        
        # Pattern 2: id=FILE_ID
        if not file_id:
            match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', url)
            if match:
                file_id = match.group(1)
        
        if file_id:
            return f'https://drive.google.com/uc?export=download&id={file_id}'
        else:
            # Fallback: thử dùng URL gốc
            return url
    
    else:  # direct or unknown
        return url

def download_file_from_url(url: str, save_path: str, timeout: int = 300) -> tuple:
    """
    Download file từ URL và lưu vào save_path.
    
    Args:
        url: URL của file
        save_path: Đường dẫn lưu file
        timeout: Timeout (giây)
    
    Returns:
        (success: bool, message: str, size_mb: float)
    """
    try:
        # Detect source
        source = detect_file_source(url)
        
        # Get direct download URL
        download_url = get_direct_download_url(url, source)
        
        # Download với streaming để hỗ trợ file lớn
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(download_url, headers=headers, stream=True, timeout=timeout)
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('Content-Type', '').lower()
        
        # Nếu là HTML, có thể là trang xác nhận download (Google Drive)
        if 'text/html' in content_type and source == 'google_drive':
            # Try to get confirm download link
            text = response.text
            match = re.search(r'href="(/uc\?export=download[^"]+)"', text)
            if match:
                confirm_url = 'https://drive.google.com' + match.group(1).replace('&amp;', '&')
                response = requests.get(confirm_url, headers=headers, stream=True, timeout=timeout)
                response.raise_for_status()
        
        # Download file
        total_size = 0
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total_size += len(chunk)
        
        size_mb = total_size / (1024 * 1024)
        
        return (True, f"Downloaded successfully ({size_mb:.2f} MB)", size_mb)
    
    except requests.Timeout:
        return (False, "Download timeout (quá 5 phút)", 0)
    except requests.RequestException as e:
        return (False, f"Lỗi download: {str(e)}", 0)
    except Exception as e:
        return (False, f"Lỗi không xác định: {str(e)}", 0)

def validate_download_url(url: str) -> tuple:
    """
    Validate URL trước khi download.
    
    Returns:
        (valid: bool, message: str, source: str)
    """
    if not url or not url.startswith('http'):
        return (False, "URL không hợp lệ! Vui lòng cung cấp URL đầy đủ (bắt đầu với http:// hoặc https://)", "")
    
    source = detect_file_source(url)
    
    if source == 'unknown':
        return (False, "Không nhận diện được nguồn file. Hỗ trợ: OneDrive, Dropbox, Google Drive, hoặc direct download link.", source)
    
    return (True, f"URL hợp lệ (nguồn: {source})", source)
