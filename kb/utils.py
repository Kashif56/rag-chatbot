import PyPDF2
from docx import Document
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse, urljoin
from datetime import datetime

def extract_pdf_text(pdf_file):
    with open(pdf_file, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""

        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text()

    return text
    

def extract_docx_text(doc_file):
    doc = Document(doc_file)
    text = ""

    for para in doc.paragraphs:
        text += para.text + "\n"

    return text

def extract_txt_text(txt_file):
    with open(txt_file, 'r') as file:
        text = file.read()
    return text




def extract_text_from_url(url, scrap_interal_pages=False):
    # Helper function to extract text from a single URL
    def extract_from_single_url(page_url):
        try:
            response = requests.get(page_url, timeout=10)
            response.raise_for_status()  # Raise exception for HTTP errors
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get title
            title = soup.title.string if soup.title else page_url
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
                
            # Extract text
            text = soup.get_text(separator=' ', strip=True)
            
            return {
                "url": page_url,
                "title": title,
                "text": text,
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Error fetching {page_url}: {str(e)}"
            print(error_msg)
            return {
                "url": page_url,
                "title": page_url,
                "text": "",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    # Parse the base domain to restrict scraping to the same site
    parsed_url = urlparse(url)
    base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    # List to store page data
    results = []
    
    # Extract text from the main URL
    main_page_data = extract_from_single_url(url)
    main_page_data["is_main_page"] = True
    main_page_data["depth"] = 0
    results.append(main_page_data)

    print(f"DEBUG: Extracted text from {url}")
    
    # If scraping internal pages is enabled
    if scrap_interal_pages:
        # Track visited URLs to avoid duplicates
        visited_urls = {url}
        # URLs to be processed
        urls_to_visit = set()
        
        # Get all internal links from the main page
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all links
            for a_tag in soup.find_all('a', href=True):
                print(f"DEBUG: Found link: {a_tag['href']}")
                link = a_tag['href']
                
                # Handle relative URLs
                if not link.startswith('http'):
                    link = urljoin(url, link)
                
                # Only include links from the same domain
                if link.startswith(base_domain) and link not in visited_urls:
                    urls_to_visit.add(link)
            
            # Scrape each internal page
            for internal_url in urls_to_visit:
                print(f"DEBUG: Visiting internal URL: {internal_url}")
                if internal_url not in visited_urls:
                    visited_urls.add(internal_url)
                    page_data = extract_from_single_url(internal_url)
                    page_data["is_main_page"] = False
                    page_data["depth"] = 1  # First level depth
                    page_data["parent_url"] = url
                    results.append(page_data)
        
        except Exception as e:
            error_msg = f"Error processing internal links: {str(e)}"
            print(error_msg)
            # Add error information to results
            results.append({
                "url": url,
                "title": "Error Processing Links",
                "text": error_msg,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "is_main_page": False,
                "depth": -1
            })
    
    return results


