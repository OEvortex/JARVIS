from typing import List, Optional, Dict, Union
from pathlib import Path
import PyPDF2
import logging
from dataclasses import dataclass
from datetime import datetime
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class PDFDocument:
    """Data class to store PDF document information"""
    file_path: Path
    content: str
    page_count: int
    metadata: Dict

class PDFConverter:
    """Class to handle PDF to text conversion operations"""
    
    def __init__(self, input_path: str) -> None:
        """Initialize the PDF converter with input file path"""
        self.input_path = Path(input_path)
        self.validate_file()

    def validate_file(self) -> None:
        """Validate if the input file exists and is a PDF"""
        if not self.input_path.exists():
            raise FileNotFoundError(f"File not found: {self.input_path}")
        if self.input_path.suffix.lower() != '.pdf':
            raise ValueError(f"File must be a PDF: {self.input_path}")

    def extract_text(self) -> PDFDocument:
        """Extract text from PDF file and return a PDFDocument object"""
        try:
            with open(self.input_path, 'rb') as file:
                # Create PDF reader object
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract text from all pages
                text_content = ""
                total_pages = len(pdf_reader.pages)
                
                # Show progress while extracting
                print(f"Extracting text from {total_pages} pages...")
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    text_content += f"\n{'='*50}\nPage {page_num}\n{'='*50}\n"
                    text_content += page.extract_text() + "\n"
                    print(f"Progress: {page_num}/{total_pages} pages processed", end='\r')
                
                print("\nExtraction completed!")

                # Create PDFDocument instance
                document = PDFDocument(
                    file_path=self.input_path,
                    content=text_content,
                    page_count=total_pages,
                    metadata=pdf_reader.metadata if pdf_reader.metadata else {}
                )
                
                return document

        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise

class TextOutputManager:
    """Class to handle text output operations"""
    
    @staticmethod
    def save_text(content: str, output_path: Optional[Path] = None) -> Path:
        """Save text content to a file"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path(f"extracted_text_{timestamp}.txt")

        try:
            output_path.write_text(content, encoding='utf-8')
            logger.info(f"Text successfully saved to: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error saving text file: {str(e)}")
            raise

    @staticmethod
    def print_text(content: str, show_page_breaks: bool = True) -> None:
        """Print text content to console"""
        if show_page_breaks:
            print(content)
        else:
            # Remove page break markers and print clean text
            clean_content = content.replace('='*50, '').replace('\n\n', '\n')
            print(clean_content)

class PDFProcessingManager:
    """Main class to manage PDF processing operations"""
    
    @staticmethod
    def process_pdf(
        input_path: str, 
        output_mode: str = 'both',
        output_path: Optional[str] = None,
        show_page_breaks: bool = True
    ) -> str:  # Changed return type to str
        """
        Process PDF file and return extracted text content.
        
        Instead of printing or saving output, the extracted text is returned.
        """
        try:
            converter = PDFConverter(input_path)
            pdf_document = converter.extract_text()
            
            logger.info(f"PDF Processing Summary:")
            logger.info(f"- Input file: {pdf_document.file_path}")
            logger.info(f"- Pages processed: {pdf_document.page_count}")
            
            return pdf_document.content

        except Exception as e:
            logger.error(f"PDF processing failed: {str(e)}")
            raise

def main() -> None:
    """Main function to demonstrate usage"""
    try:
        input_pdf = sys.argv[1] if len(sys.argv) > 1 else "Aditya_L1_Booklet.pdf"
        
        # Process PDF and capture the returned text
        extracted_text = PDFProcessingManager.process_pdf(
            input_path=input_pdf,
            output_mode='both',
            output_path="output.txt",
            show_page_breaks=True
        )
        
        print("\nExtracted Text:")
        print("="*70)
        print(extracted_text)
        print("\nProcessing completed successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"Application error: {str(e)}")

if __name__ == "__main__":
    main()