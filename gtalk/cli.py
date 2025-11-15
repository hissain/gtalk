#!/usr/bin/env python3

"""
Interactive Google AI Mode Terminal Query Tool
Requires: pip install selenium beautifulsoup4

Usage: python3 gtalk.py
Then type your queries interactively!
"""

import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import urllib.parse

class GoogleAIMode:
    def __init__(self):
        self.driver = None
        
    def init_driver(self):
        """Initialize Chrome driver with appropriate options"""
        if self.driver is not None:
            return  # Already initialized
            
        print("🔄 Initializing browser (this may take a moment)...")
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        service = Service()
        self.driver = webdriver.Chrome(service=service, options=options)
        
        # Hide webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("✓ Browser ready!\n")
    
    def extract_summary_from_html(self, html):
        """Extract summary text and code blocks from Google AI Mode HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find the main container
        main_container = soup.select_one('div.mZJni.Dn7Fzd')
        if not main_container:
            return None
        
        result = []
        
        # Process all Y3BBE divs (text blocks)
        for text_div in main_container.select('div.Y3BBE'):
            # Skip if it's inside a code block container
            if text_div.find_parent('div', class_='r1PmQe'):
                continue
                
            text = text_div.get_text(separator=' ', strip=True)
            
            # Clean up
            import re
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            if text:
                result.append(('text', text))
        
        # Process all code blocks
        for code_container in main_container.select('div.r1PmQe'):
            # Get the language (if specified)
            lang_div = code_container.select_one('div.vVRw1d')
            language = lang_div.get_text(strip=True) if lang_div else ''
            
            # Get the code content
            code_elem = code_container.select_one('pre code')
            if code_elem:
                code = code_elem.get_text()
                result.append(('code', language, code))
            
            # Check if there's a label after the code (like "Output:")
            next_text = code_container.find_next_sibling('div', class_='Y3BBE')
            if next_text:
                label = next_text.get_text(strip=True)
                if label and len(label) < 50:  # Short labels only
                    result.append(('text', label))
        
        return result if result else None
    
    def query(self, query_text):
        """Query Google AI Mode and extract summary"""
        try:
            # Initialize driver if needed
            if self.driver is None:
                self.init_driver()
            
            # Construct the URL
            encoded_query = urllib.parse.quote_plus(query_text)
            url = f"https://www.google.com/search?udm=50&aep=11&q={encoded_query}"
            
            print("🔍 Searching...")
            self.driver.get(url)
            
            # Wait for the page to load
            time.sleep(3)
            
            # Check if we hit a CAPTCHA
            if "sorry" in self.driver.page_source.lower() or "captcha" in self.driver.page_source.lower():
                print("❌ Google has detected automated access (CAPTCHA).")
                print("Tip: Wait a few minutes and try again, or use a VPN.\n")
                return
            
            # Try to wait for the AI summary to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.Y3BBE, div.kCrYT, div.hgKElc"))
                )
            except:
                pass
            
            # Additional wait for dynamic content
            time.sleep(2)
            
            # Get the page source
            html = self.driver.page_source
            
            # Extract content
            content = self.extract_summary_from_html(html)
            
            if content:
                print("\n" + "="*60)
                
                for item in content:
                    if item[0] == 'text':
                        # Print text content
                        print(item[1])
                        print()
                    elif item[0] == 'code':
                        # Print code block
                        language = item[1]
                        code = item[2]
                        
                        if language:
                            print(f"```{language}")
                        else:
                            print("```")
                        print(code.rstrip())
                        print("```")
                        print()
                
                print("="*60 + "\n")
            else:
                print("❌ No AI summary found.")
                print("Tip: Try rephrasing your query (e.g., 'What is...', 'How to...', etc.)\n")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}\n")
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            self.driver = None

def print_help():
    """Print help message"""
    print("\n" + "="*60)
    print("Commands:")
    print("  [any text]  - Query Google AI Mode")
    print("  help        - Show this help message")
    print("  clear       - Clear the screen")
    print("  quit/exit   - Exit the program")
    print("="*60 + "\n")

def clear_screen():
    """Clear the terminal screen"""
    import os
    os.system('clear' if os.name == 'posix' else 'cls')

def main():
    """Main interactive loop"""
    # Print banner
    clear_screen()
    print("="*60)
    print("  Google AI Mode - Interactive Terminal Query Tool")
    print("="*60)
    print("\nType 'help' for commands, 'quit' to exit\n")
    
    ai_mode = GoogleAIMode()
    
    try:
        while True:
            # Get user input
            try:
                query = input("Query> ").strip()
            except EOFError:
                print("\nExiting...")
                break
            
            # Handle empty input
            if not query:
                continue
            
            # Handle commands
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye! 👋")
                break
            elif query.lower() == 'help':
                print_help()
                continue
            elif query.lower() == 'clear':
                clear_screen()
                continue
            
            # Query Google AI Mode
            print()
            ai_mode.query(query)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye! 👋")
    
    finally:
        # Clean up
        ai_mode.close()

if __name__ == "__main__":
    # Check if running in interactive mode or with argument
    if len(sys.argv) > 1:
        # Legacy mode: single query from command line
        query = sys.argv[1]
        ai_mode = GoogleAIMode()
        try:
            print(f"Querying: {query}\n")
            ai_mode.query(query)
        finally:
            ai_mode.close()
    else:
        # Interactive mode
        main()