from dataclasses import dataclass
from typing import Optional, Dict, List, Union
import html2text
import requests
from urllib.parse import urlparse
import sys
from datetime import datetime
import os
from enum import Enum

class FetchError(Exception):
    """Custom exception for URL fetching errors"""
    pass

class ConversionError(Exception):
    """Custom exception for HTML to text conversion errors"""
    pass

class OutputFormat(Enum):
    """Enum for supported output formats"""
    TEXT = "txt"
    MARKDOWN = "md"

class OutputMode(Enum):
    """Enum for output modes"""
    PRINT = "print"
    SAVE = "save"
    BOTH = "both"
    NONE = "none"  # Added NONE option for no output

@dataclass
class WebsiteConfig:
    """Configuration for website processing"""
    url: str
    ignore_links: bool = True
    ignore_images: bool = True
    output_format: OutputFormat = OutputFormat.TEXT
    encoding: str = 'utf-8'
    output_mode: OutputMode = OutputMode.BOTH
    output_path: str = "output.txt"
    show_page_breaks: bool = True

@dataclass
class ConversionResult:
    """Structure to hold conversion results"""
    text: str
    metadata: Dict[str, str]
    success: bool
    error_message: Optional[str] = None

class WebsiteTextConverter:
    """Main class for converting website content to text"""
    
    def __init__(self, config: WebsiteConfig) -> None:
        self.config = config
        # Normalize the URL before processing
        self.config.url = self._normalize_url(self.config.url)
        self.converter = html2text.HTML2Text()
        self._configure_converter()

    def _normalize_url(self, url: str) -> str:
        """Normalize URL by adding protocol if missing"""
        if not url:
            return url
            
        # If URL doesn't start with http:// or https://, add https://
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
            
        return url

    def _configure_converter(self) -> None:
        """Configure the HTML2Text converter settings"""
        self.converter.ignore_links = self.config.ignore_links
        self.converter.ignore_images = self.config.ignore_images
        self.converter.body_width = 0  # No wrapping

    def _fetch_website_content(self) -> str:
        """Fetch website content with error handling"""
        try:
            response = requests.get(self.config.url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            raise FetchError(f"Failed to fetch website content: {str(e)}")

    def _generate_metadata(self) -> Dict[str, str]:
        """Generate metadata for the conversion"""
        return {
            "source_url": self.config.url,
            "conversion_date": datetime.now().isoformat(),
            "domain": urlparse(self.config.url).netloc
        }

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe saving"""
        return "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()

    def convert(self) -> ConversionResult:
        """Convert website content to text"""
        try:
            # Removed print statement for fetching
            html_content = self._fetch_website_content()
            converted_text = self.converter.handle(html_content)
            
            if self.config.show_page_breaks:
                converted_text = f"\n{'='*80}\n{converted_text}\n{'='*80}\n"
            
            metadata = self._generate_metadata()
            
            return ConversionResult(
                text=converted_text,
                metadata=metadata,
                success=True
            )
        except (FetchError, ConversionError) as e:
            return ConversionResult(
                text="",
                metadata={},
                success=False,
                error_message=str(e)
            )

    def save_to_file(self, result: ConversionResult) -> Optional[str]:
        """Save conversion result to file"""
        if not result.success:
            return None

        try:
            output_dir = os.path.dirname(self.config.output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            with open(self.config.output_path, 'w', encoding=self.config.encoding) as f:
                f.write(result.text)

            return self.config.output_path
        except IOError:
            return None

    def process(self) -> ConversionResult:
        """Main processing method - returns conversion result"""
        result = self.convert()
        
        if result.success and self.config.output_mode in [OutputMode.SAVE, OutputMode.BOTH]:
            self.save_to_file(result)
        
        return result

def main() -> str:
    """Main function that returns the converted text content"""
    config = WebsiteConfig(
        url="https://kingnish24.github.io/assets/?subject=maths&chapter=vector-algebra&topic=scalar-or-dot-product-of-two-vectors-and-its-applications&question-number=1",
        ignore_links=True,
        ignore_images=True,
        output_format=OutputFormat.TEXT,
        output_mode=OutputMode.NONE,
        output_path="output.txt",
        show_page_breaks=True
    )

    converter = WebsiteTextConverter(config)
    result = converter.process()
    
    if result.success:
        return result.text
    return ""

if __name__ == "__main__":
    try:
        content = main()
        print(content)  # Only print the final result when run as script
    except Exception as e:
        sys.exit(1)