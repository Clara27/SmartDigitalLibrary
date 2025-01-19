import fitz  # PyMuPDF
import io
from PIL import Image, ImageDraw, ImageFont
import base64
from typing import Optional, Tuple
import docx
import tempfile
import os
from pdf2image import convert_from_bytes
import hashlib

class ThumbnailGenerator:
    THUMBNAIL_SIZE = (200, 200)  # Default thumbnail size
    DEFAULT_BG_COLOR = "#f5f5f5"
    
    @staticmethod
    def generate_thumbnail(file_content: bytes, file_type: str, filename: str) -> Optional[str]:
        """
        Generate a thumbnail for the document.
        Returns base64 encoded PNG thumbnail.
        """
        try:
            print(f"Generating thumbnail for {filename} of type {file_type}")
            
            if file_type == 'application/pdf':
                print("Processing PDF file...")
                thumbnail = ThumbnailGenerator._process_pdf_thumbnail(file_content)
                print(f"PDF thumbnail generated: {'Success' if thumbnail else 'Failed'}")
                return thumbnail
                
            elif file_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                print("Processing DOCX file...")
                thumbnail = ThumbnailGenerator._process_docx_thumbnail(file_content, filename)
                print(f"DOCX thumbnail generated: {'Success' if thumbnail else 'Failed'}")
                return thumbnail
                
            elif file_type == 'text/plain' or filename.endswith('.txt'):
                print("Processing text file...")
                thumbnail = ThumbnailGenerator._process_text_thumbnail(filename)
                print(f"Text thumbnail generated: {'Success' if thumbnail else 'Failed'}")
                return thumbnail
                
            print(f"Unsupported file type: {file_type}, generating default thumbnail")
            return ThumbnailGenerator._generate_default_thumbnail(filename)
            
        except Exception as e:
            print(f"Error generating thumbnail: {str(e)}")
            return ThumbnailGenerator._generate_default_thumbnail(filename)


    @staticmethod
    def _process_pdf_thumbnail(pdf_content: bytes) -> Optional[str]:
        """Generate thumbnail from first page of PDF using PyMuPDF."""
        try:
            print("Processing PDF using PyMuPDF...")
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            if doc.page_count > 0:
                page = doc[0]
                
                # Set zoom factors for better quality
                zoom = 2  # Increase resolution
                mat = fitz.Matrix(zoom, zoom)
                
                # Get page preview
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image for processing
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Resize to a reasonable preview size
                max_width = 800
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_size = (max_width, int(img.height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Convert to base64
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG', optimize=True)
                img_byte_arr = img_byte_arr.getvalue()
                
                print("Successfully generated PDF thumbnail")
                return base64.b64encode(img_byte_arr).decode()
                
            else:
                print("No pages found in PDF")
                return None
                
        except Exception as e:
            print(f"Error in _process_pdf_thumbnail: {str(e)}")
            return None
        finally:
            if 'doc' in locals():
                doc.close()

    @staticmethod
    def _create_doc_icon() -> Image:
        """Create a DOCX file icon."""
        img = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw document shape
        draw.rectangle([(20, 10), (80, 90)], fill='#4B8BF4', outline='#3973D4', width=2)
        draw.rectangle([(30, 30), (70, 35)], fill='white')
        draw.rectangle([(30, 45), (70, 50)], fill='white')
        draw.rectangle([(30, 60), (70, 65)], fill='white')
        
        return img

    @staticmethod
    def _create_text_icon() -> Image:
        """Create a text file icon."""
        img = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw text file shape
        draw.rectangle([(20, 10), (80, 90)], fill='#95A5A6', outline='#7F8C8D', width=2)
        draw.rectangle([(30, 30), (70, 35)], fill='white')
        draw.rectangle([(30, 45), (70, 50)], fill='white')
        draw.rectangle([(30, 60), (50, 65)], fill='white')
        
        return img

    @staticmethod
    def _create_generic_icon() -> Image:
        """Create a generic document icon."""
        img = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw generic document shape
        draw.rectangle([(20, 10), (80, 90)], fill='#E74C3C', outline='#C0392B', width=2)
        draw.rectangle([(30, 30), (70, 35)], fill='white')
        draw.rectangle([(30, 45), (70, 50)], fill='white')
        draw.rectangle([(30, 60), (70, 65)], fill='white')
        
        return img

    @staticmethod
    def _truncate_text(text: str, max_length: int) -> str:
        """Truncate text to specified length and add ellipsis if needed."""
        return text[:max_length] + '...' if len(text) > max_length else text