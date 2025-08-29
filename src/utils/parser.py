from markitdown import MarkItDown
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import mimetypes

logger = logging.getLogger(__name__)

class DocumentParser:
    def __init__(self):
        self.markitdown = MarkItDown()
        self.supported_extensions = {
            '.pdf', '.docx', '.pptx', '.xlsx', 
            '.txt', '.md', '.html', '.htm', 
            '.csv', '.json', '.xml'
        }
    
    def is_supported(self, file_path: str) -> bool:
        return Path(file_path).suffix.lower() in self.supported_extensions
    
    def parse_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        try:
            if not self.is_supported(file_path):
                logger.warning(f"Unsupported file type: {file_path}")
                return None
            
            result = self.markitdown.convert(file_path)
            
            if not result or not result.text_content:
                logger.warning(f"No content extracted from {file_path}")
                return None
            
            file_path_obj = Path(file_path)
            
            mime_type = mimetypes.guess_type(file_path)[0]
            if mime_type is None:
                # Default to application/octet-stream when mime_type is None
                mime_type = "application/octet-stream"
                
            return {
                'content': result.text_content.strip(),
                'title': result.title or file_path_obj.stem,
                'file_path': str(file_path_obj),
                'file_name': file_path_obj.name,
                'file_size': file_path_obj.stat().st_size if file_path_obj.exists() else 0,
                'file_type': file_path_obj.suffix.lower(),
                'mime_type': mime_type,
                'metadata': {
                    'source': 'file_upload',
                    'parser': 'markitdown'
                }
            }
        except Exception as e:
            logger.error(f"Failed to parse file {file_path}: {e}")
            return None
    
    def parse_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        results = []
        for file_path in file_paths:
            result = self.parse_file(file_path)
            if result:
                results.append(result)
        return results
    
    def parse_content(self, content: str, source_info: Dict[str, Any]) -> Dict[str, Any]:
        # Get mime_type from source_info or default to text/plain, ensuring it's not None
        mime_type = source_info.get('mime_type', 'text/plain')
        if mime_type is None:
            mime_type = 'text/plain'
            
        return {
            'content': content.strip(),
            'title': source_info.get('title', 'Untitled'),
            'file_path': source_info.get('file_path', ''),
            'file_name': source_info.get('file_name', ''),
            'file_size': len(content.encode('utf-8')),
            'file_type': source_info.get('file_type', '.txt'),
            'mime_type': mime_type,
            'metadata': source_info.get('metadata', {})
        }

def get_parser() -> DocumentParser:
    return DocumentParser()