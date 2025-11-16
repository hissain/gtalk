#!/usr/bin/env python3

import sys
import time
import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import urllib.parse
import re
import json


class GoogleAIMode:
    def __init__(self):
        self.driver = None
        self.memory = ""
        self.is_windows = platform.system() == "Windows"
        self.retry_delay = 3 if self.is_windows else 2
        self.first_query = True
        self.last_query = "" # New: Store the previous raw query

    def init_driver(self):
        """Initialize browser with cross-platform optimizations"""
        if self.driver is not None:
            return

        print("🔄 Initializing browser...")
        options = Options()
        
        # Platform-specific configurations
        if self.is_windows:
            options.add_argument('--headless=new')  # Better for Windows
        else:
            options.add_argument('--headless')
        
        # Core options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-gpu')  # Helps with headless stability
        options.add_argument('--lang=en-US')
        options.add_argument('--window-size=1920,1080')
        
        # User agent (Windows-based for consistency)
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        options.add_argument(f'--user-agent={user_agent}')
        
        # Anti-detection
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.geolocation": 2
        })

        try:
            service = Service()
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Enhanced stealth scripts
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": user_agent
            })
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
            
            # Warm-up session to avoid first-request CAPTCHA
            print("🔄 Warming up session...")
            self.driver.get("https://www.google.com")
            time.sleep(self.retry_delay)
            
            print("✓ Browser ready!\n")
            
        except Exception as e:
            print(f"❌ Failed to initialize browser: {str(e)}")
            print("Make sure Chrome and ChromeDriver are installed and in PATH")
            sys.exit(1)

    def is_useless_result(self, content):
        if not content:
            return True
        if len(content) == 1 and content[0][0] == 'text':
            txt = content[0][1].lower()
            if "top web results" in txt and "exploring this topic" in txt:
                return True
        return False

    def extract_summary_from_html(self, html):
        """Extract AI summary from Google's response."""
        soup = BeautifulSoup(html, 'html.parser')
        main_container = soup.select_one('div.mZJni.Dn7Fzd')
        if not main_container:
            return None

        result = []

        # Combined selector for all relevant content types, maintaining document order
        content_elements = main_container.select('div.r1PmQe, ul.KsbFXc, div.Y3BBE, div.AdPoic, span.T286Pc')

        for element in content_elements:
            # Handle code blocks (div with class r1PmQe)
            if element.name == 'div' and 'r1PmQe' in element.get('class', []):
                lang_div = element.select_one('div.vVRw1d')
                language = lang_div.get_text(strip=True) if lang_div else ''
                code_elem = element.select_one('pre code')
                if code_elem:
                    code = code_elem.get_text()
                    result.append(('code', language, code))
            # Handle lists (ul with class KsbFXc)
            elif element.name == 'ul' and 'KsbFXc' in element.get('class', []):
                list_items = []
                for li in element.select('li'):
                    li_text = li.get_text(separator=' ', strip=True)
                    li_text = re.sub(r'\s+', ' ', li_text)
                    if li_text:
                        list_items.append(li_text)
                if list_items:
                    result.append(('list', list_items))
            # Handle text (div.Y3BBE, div.AdPoic, or span.T286Pc)
            elif (element.name == 'div' and ('Y3BBE' in element.get('class', []) or 'AdPoic' in element.get('class', []))) or \
                 (element.name == 'span' and 'T286Pc' in element.get('class', []) or 'pWvJNd' in element.get('class', [])):
                text = element.get_text(separator=' ', strip=True)
                text = re.sub(r'\s+', ' ', text).strip()
                if text:
                    result.append(('text', text))

        # Fallback: if no specific content was found, get all text from the main container
        if not result:
            text = main_container.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text).strip()
            if text:
                result.append(('text', text))

        return result if result else None

    def extract_first_paragraph_100_words(self, content_blocks):
        """Extract first paragraph and cut to 100 words for memory"""
        for item in content_blocks:
            if item[0] == 'text':
                words = item[1].split()
                return " ".join(words[:100])
        return ""

    def summarize_query(self, text_to_summarize):
        """Asks Google to summarize the given text within 100 words and updates memory."""
        # print("📝 Summarizing previous answer for memory...") # Removed log
        summary_query_text = f"Summarize the following text in 150 words and also, specifically, include what topic it talked about within the summary. Text: {text_to_summarize}."
        encoded_summary_query = urllib.parse.quote_plus(summary_query_text)
        summary_url = f"https://www.google.com/search?udm=50&aep=11&hl=en&lr=lang_en&q={encoded_summary_query}"

        try:
            self.driver.get(summary_url)
            time.sleep(self.retry_delay) # Give it some time to load

            # Wait for content to load, similar to the main query
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.Y3BBE, div.kCrYT, div.hgKElc"))
                )
            except:
                pass
            time.sleep(2) # Additional wait

            html = self.driver.page_source
            summary_content = self.extract_summary_from_html(html)

            if summary_content:
                # Extract the first paragraph of the summary
                new_summary = self.extract_first_paragraph_100_words(summary_content)
                if new_summary:
                    self.memory = new_summary
                    # print("✓ Memory updated with 150-word summary.") # Removed log
                # else:
                    # print("⚠️ Could not extract summary for memory update.") # Removed log
            # else:
                # print("⚠️ No summary found for memory update.") # Removed log
        except Exception as e:
            # print(f"❌ Error during summarization for memory: {str(e)}") # Removed log
            pass # Suppress error for abstraction

    def find_is_relevant_to_previous_information(self, new_query, combined_memory):
        """Asks Google if the new query is relevant to the current memory, expecting a JSON boolean response."""
        print("🤔 Analyzing...") # Re-enabled log for debugging
        relevance_query_text = f"Is the query '{new_query}' relevant to the previous information '{combined_memory}'? Answer in JSON format: {{'relevant': true/false}}"
        encoded_relevance_query = urllib.parse.quote_plus(relevance_query_text)
        relevance_url = f"https://www.google.com/search?udm=50&aep=11&hl=en&lr=lang_en&q={encoded_relevance_query}"

        try:
            self.driver.get(relevance_url)
            time.sleep(self.retry_delay)

            # Wait for content to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.Y3BBE, div.kCrYT, div.hgKElc"))
                )
            except:
                pass
            time.sleep(2)

            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            # Attempt to find JSON in preformatted text or script tags
            json_match = None
            for pre in soup.find_all('pre'):
                if 'relevant' in pre.get_text():
                    json_match = pre.get_text()
                    break
            if not json_match:
                for script in soup.find_all('script', type='application/ld+json'):
                    if 'relevant' in script.get_text():
                        json_match = script.get_text()
                        break
            if not json_match:
                # Fallback: try to find it in general text blocks
                for text_element in soup.select('div.Y3BBE, div.AdPoic, span.T286Pc'):
                    text = text_element.get_text(separator=' ', strip=True)
                    if 'relevant' in text and ('true' in text or 'false' in text):
                        json_match = text
                        break

            if json_match:
                # Use regex to extract the JSON object
                json_str_match = re.search(r'\{[^}]*?"relevant"\s*:\s*(true|false)[^}]*\}', json_match, re.IGNORECASE)
                if json_str_match:
                    json_str = json_str_match.group(0)
                    try:
                        relevance_data = json.loads(json_str)
                        is_relevant = relevance_data.get('relevant', False)
                        # print(f"✓ Relevance check: {'Relevant' if is_relevant else 'Not Relevant'}") # Re-enabled log for debugging
                        return is_relevant
                    except json.JSONDecodeError:
                        pass
            else:
                pass
            return False # Default to not relevant if parsing fails
        except Exception as e:
            return False

    def query(self, raw_query, retry_count=0, max_retries=2):
        """Execute query with automatic retry on CAPTCHA"""
        try:
            if self.driver is None:
                self.init_driver()

            # Store the current raw query as the last query
            current_raw_query = raw_query
            
            if self.first_query:
                final_query_text = current_raw_query
                self.first_query = False
            else:
                # Memory context now includes both previous query and its summary
                combined_memory = ""
                if self.last_query:
                    combined_memory += f"Previous Query: {self.last_query}. "
                if self.memory:
                    combined_memory += f"Previous Answer: {self.memory}. "

                # Check relevance before deciding to use memory
                is_relevant = self.find_is_relevant_to_previous_information(current_raw_query, combined_memory)

                if is_relevant:
                    final_query_text = f"{combined_memory}\n\nNew Query: {current_raw_query}\n\nNote: Answer the new query within one to three paragraphs only, depending on the query, unless it involves code blocks"
                    # print("✅ Appending context to query.") # Re-enabled log for debugging
                else:
                    final_query_text = current_raw_query
                    self.memory = "" # Clear summary memory if not relevant
                    self.last_query = "" # Clear previous query memory if not relevant
                    # print("❌ Query not relevant to previous context. Making a fresh request.") # Re-enabled log for debugging
            
            time.sleep(1) # Added a small delay here for stability

            # Update last_query for the next iteration
            self.last_query = current_raw_query

            encoded = urllib.parse.quote_plus(final_query_text)
            
            # URL with English language parameters
            url = f"https://www.google.com/search?udm=50&aep=11&hl=en&lr=lang_en&q={encoded}"

            # print("DEBUG: About to make main search request.") # New debug print
            print("🔍 Thinking...")
            self.driver.get(url)

            # Platform-specific wait times
            initial_wait = 4 if self.is_windows else 3
            time.sleep(initial_wait)
            
            # Check for CAPTCHA
            page_source_lower = self.driver.page_source.lower()
            if "captcha" in page_source_lower or "unusual traffic" in page_source_lower:
                if retry_count < max_retries:
                    wait_time = (retry_count + 1) * self.retry_delay
                    #print(f"⚠️  CAPTCHA detected. Retrying in {wait_time}s... (Attempt {retry_count + 2}/{max_retries + 1})")
                    time.sleep(wait_time)
                    return self.query(raw_query, retry_count + 1, max_retries)
                else:
                    #print("❌ CAPTCHA detected. Max retries reached.")
                    print("💡 Tip: Wait a few minutes before trying again.\n")
                    return

            # Wait for content to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.Y3BBE, div.kCrYT, div.hgKElc"))
                )
            except:
                pass

            time.sleep(2)
            html = self.driver.page_source

            content = self.extract_summary_from_html(html)            

            # Retry if empty or contains the useless preface
            if self.is_useless_result(content):
                if retry_count < max_retries:
                    wait_time = (retry_count + 1) * self.retry_delay
                    time.sleep(wait_time)
                    return self.query(raw_query + ", answer it anyway", retry_count + 1, max_retries)
                else:
                    print("❌ No valid AI summary after retries.\n")
                    return


            if not content:
                print("❌ No AI summary found.")
                print("💡 Google AI Mode might not have generated a response for this query.\n")
                return

            # Display results and collect full text for summarization
            print("\n" + "="*60)
            full_answer_text = [] # Collect all text for summarization
            for item in content:
                if item[0] == 'text':
                    print(item[1])
                    print()
                    full_answer_text.append(item[1])
                elif item[0] == 'code':
                    language = item[1]
                    code = item[2]
                    if language:
                        print(f"```{language}")
                    else:
                        print("```")
                    print(code.rstrip())
                    print("```")
                    print()
                    full_answer_text.append(code) # Include code in text for summarization
                elif item[0] == 'list':
                    for list_item in item[1]:
                        print(f"- {list_item}")
                    print()
                    full_answer_text.extend(item[1]) # Add list items to text for summarization
                elif item[0] == 'table':
                    # simple table formatting
                    for row in item[1]:
                        print(" | ".join(row))
                    print()
                    full_answer_text.extend([" ".join(row) for row in item[1]]) # Add table rows to text for summarization
            print("="*60 + "\n")

            # Call summarize_query after displaying the answer
            if full_answer_text:
                self.summarize_query(" ".join(full_answer_text))
            # else:
                # print("⚠️ No content to summarize for memory update.") # Removed log

        except KeyboardInterrupt:
            raise
        except Exception as e:
            # print(f"❌ Error: {str(e)}") # Removed log
            if "chrome not reachable" in str(e).lower():
                # print("💡 Browser crashed. Reinitializing...") # Removed log
                self.driver = None
                if retry_count < max_retries:
                    return self.query(raw_query, retry_count + 1, max_retries)
            # print() # Removed log

    def close(self):
        """Clean up browser resources"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None


def clear_screen():
    """Clear terminal screen (cross-platform)"""
    import os
    os.system('cls' if platform.system() == "Windows" else 'clear')


def print_help():
    """Display help information"""
    print("\n" + "="*60)
    print("Commands:")
    print("  [text]    - Query Google AI Mode")
    print("  help      - Show this help message")
    print("  clear     - Clear terminal screen")
    print("  reset     - Reset conversation memory")
    print("  quit      - Exit the program")
    print("="*60 + "\n")


def main():
    """Main interactive loop"""
    clear_screen()
    print("="*60)
    print("  Google AI Mode - Interactive Terminal Query Tool")
    print("="*60)
    print(f"  Platform: {platform.system()} | Python: {platform.python_version()}")
    print("="*60)
    print("\nType 'help' for commands, 'quit' to exit\n")

    ai = GoogleAIMode()
    
    # Pre-initialize browser to avoid first-query issues
    ai.init_driver()

    try:
        while True:
            try:
                q = input("Query> ").strip()
            except EOFError:
                print("\nExiting...")
                break

            if not q:
                continue

            q_lower = q.lower()
            
            if q_lower in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            elif q_lower == 'help':
                print_help()
                continue
            elif q_lower == 'clear':
                clear_screen()
                continue
            elif q_lower == 'reset':
                ai.memory = ""
                ai.first_query = True
                print("✓ Conversation memory reset.\n")
                continue

            print()
            ai.query(q)

    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!")

    finally:
        ai.close()

def cli(argv=None):
    """CLI entry point for pip console script"""
    if argv is None:
        argv = sys.argv[1:]

    ai = GoogleAIMode()
    try:
        if argv:
            ai.init_driver()
            query_text = " ".join(argv)
            print(f"Querying: {query_text}\n")
            ai.query(query_text)
        else:
            main()  # fallback interactive mode
    finally:
        ai.close()


if __name__ == "__main__":
    # debug: show what the process actually received
    print("DEBUG: sys.argv =", repr(sys.argv))

    ai = GoogleAIMode()
    try:
        # 1) Command-line args
        if len(sys.argv) > 1:
            ai.init_driver()
            query_text = " ".join(sys.argv[1:])
            print(f"Querying: {query_text}\n")
            ai.query(query_text)

        # 2) Non-interactive stdin (e.g. echo "q" | gtalk)
        elif not sys.stdin.isatty():
            stdin_text = sys.stdin.read().strip()
            if stdin_text:
                ai.init_driver()
                print(f"Querying from stdin: {stdin_text!r}\n")
                ai.query(stdin_text)
            else:
                print("No stdin input detected - dropping to interactive mode.\n")
                main()

        # 3) Interactive fallback
        else:
            main()
    finally:
        ai.close()

