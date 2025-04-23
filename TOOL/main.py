from AGENTS.functioncall import tools
from .askwebsite import WebsiteTextConverter, WebsiteConfig, OutputFormat, OutputMode
from .internetspeed import InternetSpeedTester, SpeedTestResult
from .news import NewsService
from .pdf import PDFProcessingManager
from RESEARCH.felo import Felo, DefaultResponseFormatter

@tools
def ask_website(url: str, **kwargs) -> str:
    """
    Fetches content from a website and returns the extracted text.
    
    Args:
        url (str): URL of the website to extract.
        ignore_links (bool, optional): Ignore links while extracting. Default: True
        ignore_images (bool, optional): Ignore images while extracting. Default: True
        output_format (str, optional): 'text' or 'markdown'. Default: 'text'
        output_path (str, optional): Path for saving text file if needed. Default: 'output.txt'
        show_page_breaks (bool, optional): Show page breaks. Default: True
    
    Returns:
        str: Text content of the website, or an error message.
    """
    try:
        # Get optional parameters with defaults
        ignore_links = kwargs.get('ignore_links', True)
        ignore_images = kwargs.get('ignore_images', True)
        output_format_str = kwargs.get('output_format', 'text')
        output_path = kwargs.get('output_path', 'output.txt')
        show_page_breaks = kwargs.get('show_page_breaks', True)
        
        # Convert output format string to enum
        output_format_enum = OutputFormat.TEXT if output_format_str.lower() == "text" else OutputFormat.MARKDOWN
        
        config = WebsiteConfig(
            url=url,
            ignore_links=ignore_links,
            ignore_images=ignore_images,
            output_format=output_format_enum,
            output_mode=OutputMode.NONE,
            output_path=output_path,
            show_page_breaks=show_page_breaks
        )
        converter = WebsiteTextConverter(config)
        result = converter.process()

        if not result.success:
            return f"Error processing website: {result.error_message}"
        
        return result.text
    except Exception as e:
        return f"Error processing website: {str(e)}"

@tools
def check_internet_speed() -> str:
    """
    Checks internet speed and returns the result.
    
    Returns:
      str: Download and upload speeds in Mbps and the ping in ms.
    """
    tester = InternetSpeedTester()
    try:
        result: SpeedTestResult = tester.perform_speed_test()
        return (
            f"Download Speed: {result.download_speed:.2f} Mbps, "
            f"Upload Speed: {result.upload_speed:.2f} Mbps, "
            f"Ping: {result.ping:.2f} ms"
        )
    except Exception as e:
        # Return a more detailed error message
        error_msg = str(e)
        if "403" in error_msg:
            return "Error: Speedtest servers returned a 403 Forbidden error. This may be due to firewall restrictions or API changes. Try again later or check your network connection."
        return f"Error testing internet speed: {error_msg}"

@tools
def get_news(topic: str, max_results: int = 3) -> str:
    """
    Retrieves news articles for a specific topic.
    
     Args:
        topic (str): Topic of news to retrieve.
        max_results (int): Max results to retrieve.

    Returns:
      str: News articles.
    """
    service = NewsService(max_results=max_results)
    return service.get_news(topic)

@tools
def websearch(query: str, timeout: int = 30, stream: bool = False) -> str:
    """
    Performs web search on a topic and returns comprehensive information.
    
    Args:
        query (str): The search query or topic to investigate.
        timeout (int, optional): Request timeout in seconds. Default: 30
        stream (bool, optional): Whether to stream the response. Default: False
    
    Returns:
        str: Web search results with detailed information.
    """
    if not query:
        return "Please provide a search query."
        
    try:
        felo_agent = Felo(timeout=timeout, formatter=DefaultResponseFormatter())
        
        if stream:
            # For streaming responses, we collect chunks and return the full text
            chunks = []
            for chunk in felo_agent.chat(query, stream=True):
                chunks.append(chunk)
            return ''.join(chunks)
        else:
            # For normal responses, just return the result
            return felo_agent.chat(query)
    except Exception as e:
        error_msg = str(e)
        if "timeout" in error_msg.lower():
            return f"Error: Web search timed out after {timeout} seconds. Try increasing the timeout or simplifying your query."
        elif "connection" in error_msg.lower():
            return "Error: Could not connect to search service. Please check your internet connection and try again."
        else:
            return f"Error performing web search: {error_msg}"

@tools
def process_pdf(input_path: str, output_mode: str = 'both', output_path: str = None, show_page_breaks: bool = True) -> str:
    """
    Extracts text from a PDF file.
    
    Args:
        input_path (str): Path to the PDF file.
        output_mode (str): 'print', 'save', or 'both' (now ignored).
        output_path (str): Path for saving text file (now ignored).
        show_page_breaks (bool): Show page breaks.
    
    Returns:
        str: Extracted text from the PDF.
    """
    try:
        extracted_text = PDFProcessingManager.process_pdf(
            input_path=input_path,
            output_mode=output_mode,
            output_path=output_path,
            show_page_breaks=show_page_breaks
        )
        return extracted_text
    except Exception as e:
        return f"Error processing PDF: {str(e)}"