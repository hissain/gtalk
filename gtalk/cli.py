#!/usr/bin/env python3

import sys
import time
import platform
import argparse
import threading
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


class ProgressIndicator:
    """Thread-safe progress indicator for terminal"""
    def __init__(self, message="Processing", enabled=True):
        self.message = message
        self.enabled = enabled
        self.running = False
        self.thread = None
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.current_idx = 0
        
    def _spin(self):
        """Background spinner animation"""
        while self.running:
            if self.enabled:
                sys.stdout.write(f'\r{self.spinner_chars[self.current_idx]} {self.message}...')
                sys.stdout.flush()
                self.current_idx = (self.current_idx + 1) % len(self.spinner_chars)
            time.sleep(0.1)
    
    def start(self):
        """Start the progress indicator"""
        if not self.enabled:
            return
        self.running = True
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()
    
    def stop(self, final_message=None):
        """Stop the progress indicator"""
        if not self.enabled:
            return
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.5)
        sys.stdout.write('\r' + ' ' * (len(self.message) + 20) + '\r')
        sys.stdout.flush()
        if final_message:
            print(final_message)


class GoogleAIMode:
    def __init__(self, verbose=False, short_mode=False):
        self.driver = None
        self.memory = ""
        self.is_windows = platform.system() == "Windows"
        self.retry_delay = 3 if self.is_windows else 2
        self.first_query = True
        self.last_query = ""
        self.conversation_history = []
        self.verbose = verbose
        self.short_mode = short_mode
        
    def log(self, message):
        """Print message only if verbose mode is enabled"""
        if self.verbose:
            print(message)

    def init_driver(self):
        """Initialize browser with cross-platform optimizations"""
        if self.driver is not None:
            return

        progress = ProgressIndicator("Initializing browser", enabled=not self.verbose)
        progress.start()
        
        self.log("🔄 Initializing browser...")
        options = Options()
        
        # Platform-specific configurations
        if self.is_windows:
            options.add_argument('--headless=new')
        else:
            options.add_argument('--headless')
        
        # Core options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-gpu')
        options.add_argument('--lang=en-US')
        options.add_argument('--window-size=1920,1080')
        
        # Suppress logs in non-verbose mode
        if not self.verbose:
            options.add_argument('--log-level=3')
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        # User agent
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
            
            # Warm-up session
            self.log("🔄 Warming up session...")
            self.driver.get("https://www.google.com")
            time.sleep(self.retry_delay)
            
            progress.stop()
            self.log("✓ Browser ready!\n")
            
        except Exception as e:
            progress.stop()
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

    def contains_code_or_structured_data(self, content):
        """Check if response contains code blocks, lists, or tables"""
        if not content:
            return False
        for item in content:
            if item[0] in ['code', 'list', 'table']:
                return True
        return False

    def extract_summary_from_html(self, html):
        """Extract AI summary from Google's response."""
        soup = BeautifulSoup(html, 'html.parser')
        main_container = soup.select_one('div.mZJni.Dn7Fzd')
        if not main_container:
            return None

        result = []

        # Combined selector for all relevant content types
        content_elements = main_container.select('div.r1PmQe, ul.KsbFXc, div.Y3BBE, div.AdPoic, span.T286Pc')

        for element in content_elements:
            # Handle code blocks
            if element.name == 'div' and 'r1PmQe' in element.get('class', []):
                lang_div = element.select_one('div.vVRw1d')
                language = lang_div.get_text(strip=True) if lang_div else ''
                code_elem = element.select_one('pre code')
                if code_elem:
                    code = code_elem.get_text()
                    result.append(('code', language, code))
            # Handle lists
            elif element.name == 'ul' and 'KsbFXc' in element.get('class', []):
                list_items = []
                for li in element.select('li'):
                    li_text = li.get_text(separator=' ', strip=True)
                    li_text = re.sub(r'\s+', ' ', li_text)
                    if li_text:
                        list_items.append(li_text)
                if list_items:
                    result.append(('list', list_items))
            # Handle text
            elif (element.name == 'div' and ('Y3BBE' in element.get('class', []) or 'AdPoic' in element.get('class', []))) or \
                 (element.name == 'span' and 'T286Pc' in element.get('class', []) or 'pWvJNd' in element.get('class', [])):
                text = element.get_text(separator=' ', strip=True)
                text = re.sub(r'\s+', ' ', text).strip()
                if text:
                    result.append(('text', text))

        # Fallback
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
        """Asks Google to summarize the given text within 150 words and updates memory."""
        progress = ProgressIndicator("Generating summary", enabled=not self.verbose)
        progress.start()
        
        summary_query_text = f"Summarize the following text in 150 words and also, specifically, include what topic it talked about within the summary. Text: {text_to_summarize}."
        encoded_summary_query = urllib.parse.quote_plus(summary_query_text)
        summary_url = f"https://www.google.com/search?udm=50&aep=11&hl=en&lr=lang_en&q={encoded_summary_query}"

        try:
            self.driver.get(summary_url)
            time.sleep(self.retry_delay)

            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.Y3BBE, div.kCrYT, div.hgKElc"))
                )
            except:
                pass
            time.sleep(2)

            html = self.driver.page_source
            summary_content = self.extract_summary_from_html(html)

            if summary_content:
                new_summary = self.extract_first_paragraph_100_words(summary_content)
                if new_summary:
                    self.memory = new_summary
                    self.log(f"✓ Summary generated: {self.memory[:50]}...")
        except Exception as e:
            self.log(f"⚠ Summary generation failed: {str(e)}")
        finally:
            progress.stop()

    def check_follow_up_with_ai(self, current_query):
        """Ask Google AI to determine if current query is a follow-up with probability"""
        if not self.conversation_history and not self.last_query:
            return False, 0.0
        
        progress = ProgressIndicator("Analyzing context", enabled=not self.verbose)
        progress.start()
        self.log("🤔 Checking if this is a follow-up question...")
        
        try:
            # Build context summary
            context_parts = []
            if self.conversation_history:
                for exchange in self.conversation_history[-2:]:
                    context_parts.append(f"Previous Q: {exchange['query']}")
                    context_parts.append(f"Previous A: {exchange['summary'][:200]}")
            
            context_text = " ".join(context_parts) if context_parts else f"Last query: {self.last_query}"
            
            # Ask AI to analyze
            analysis_query = f"""Given this conversation context: {context_text}

Is the following new question "{current_query}" a follow-up question that references or builds upon the previous conversation? 

Respond ONLY in this exact format:
FOLLOW_UP: [YES or NO]
PROBABILITY: [0-100]
REASON: [one sentence explanation]"""
            
            encoded = urllib.parse.quote_plus(analysis_query)
            url = f"https://www.google.com/search?udm=50&aep=11&hl=en&lr=lang_en&q={encoded}"
            
            self.driver.get(url)
            time.sleep(self.retry_delay)
            
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.Y3BBE, div.kCrYT, div.hgKElc"))
                )
            except:
                pass
            
            time.sleep(2)
            html = self.driver.page_source
            content = self.extract_summary_from_html(html)
            
            if content:
                # Parse the response
                response_text = ""
                for item in content:
                    if item[0] == 'text':
                        response_text += item[1] + " "
                
                self.log(f"AI Analysis: {response_text[:200]}")
                
                # Extract decision
                is_follow_up = "YES" in response_text.upper() and "FOLLOW_UP" in response_text.upper()
                
                # Extract probability
                prob_match = re.search(r'PROBABILITY:\s*(\d+)', response_text, re.IGNORECASE)
                probability = float(prob_match.group(1)) / 100.0 if prob_match else (0.8 if is_follow_up else 0.2)
                
                progress.stop()
                
                if is_follow_up and probability > 0.5:
                    self.log(f"✓ Detected as follow-up (probability: {probability:.0%})")
                else:
                    self.log(f"✓ Detected as new topic (probability: {probability:.0%})")
                
                return is_follow_up and probability > 0.5, probability
                
        except Exception as e:
            self.log(f"⚠ Follow-up detection failed: {str(e)}")
        finally:
            progress.stop()
        
        return False, 0.0

    def build_query_prompt(self, raw_query, has_context):
        """Build intelligent query prompt based on query type and context"""
        # In short mode, always request concise response
        if self.short_mode:
            return f"{raw_query}\n\nProvide a brief, concise answer in a single paragraph (3-5 sentences maximum)."
        
        # Detect if query is asking for code, lists, or structured data
        code_keywords = ['code', 'program', 'script', 'function', 'algorithm', 'implementation', 'example code']
        list_keywords = ['list', 'steps', 'ways to', 'how to', 'methods', 'tips', 'options', 'alternatives']
        
        raw_lower = raw_query.lower()
        
        # Check if query explicitly asks for structured content
        wants_code = any(keyword in raw_lower for keyword in code_keywords)
        wants_list = any(keyword in raw_lower for keyword in list_keywords)
        wants_structured = wants_code or wants_list
        
        if wants_structured:
            # Don't add formatting instructions for code/list queries
            return raw_query
        else:
            # For general queries, request paragraph format
            if has_context:
                # With context, keep it concise
                return f"{raw_query}\n\nProvide a clear, concise answer in natural paragraph form (1-3 paragraphs). Avoid bullet points or numbered lists unless absolutely necessary."
            else:
                # Without context, allow slightly longer responses
                return f"{raw_query}\n\nProvide a comprehensive answer in natural paragraph form. Write in flowing prose without using bullet points or numbered lists unless the information absolutely requires structured formatting."

    def query(self, raw_query, retry_count=0, max_retries=2):
        """Execute query with automatic retry on CAPTCHA"""
        try:
            if self.driver is None:
                self.init_driver()

            current_raw_query = raw_query
            
            if self.first_query:
                final_query_text = self.build_query_prompt(current_raw_query, has_context=False)
                self.first_query = False
            else:
                # Use AI to check if this is a follow-up query
                is_follow_up, probability = self.check_follow_up_with_ai(current_raw_query)
                
                if is_follow_up and (self.conversation_history or self.last_query or self.memory):
                    self.log(f"🔗 Building context (follow-up probability: {probability:.0%})...")
                    # Build richer context from conversation history
                    context_parts = []
                    
                    # Include recent conversation exchanges (last 2-3 for context)
                    if self.conversation_history:
                        context_parts.append("Conversation history:")
                        for i, exchange in enumerate(self.conversation_history[-3:], 1):
                            context_parts.append(f"User asked: {exchange['query']}")
                            context_parts.append(f"You answered: {exchange['summary']}")
                    
                    combined_context = " ".join(context_parts)
                    base_query = self.build_query_prompt(current_raw_query, has_context=True)
                    final_query_text = f"{combined_context}\n\nNow the user asks: {base_query}\n\nRemember to reference the conversation above when answering."
                else:
                    # Fresh query - clear memory
                    self.log("🆕 Starting new conversation topic...")
                    final_query_text = self.build_query_prompt(current_raw_query, has_context=False)
                    self.memory = ""
                    self.last_query = ""
                    self.conversation_history = []
            
            time.sleep(1)

            encoded = urllib.parse.quote_plus(final_query_text)
            url = f"https://www.google.com/search?udm=50&aep=11&hl=en&lr=lang_en&q={encoded}"

            progress = ProgressIndicator("Searching", enabled=not self.verbose)
            progress.start()
            self.log("🔍 Thinking...")
            
            self.driver.get(url)

            initial_wait = 4 if self.is_windows else 3
            time.sleep(initial_wait)
            
            # Check for CAPTCHA
            page_source_lower = self.driver.page_source.lower()
            if "captcha" in page_source_lower or "unusual traffic" in page_source_lower:
                progress.stop()
                if retry_count < max_retries:
                    wait_time = (retry_count + 1) * self.retry_delay
                    self.log(f"⚠ CAPTCHA detected, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    return self.query(raw_query, retry_count + 1, max_retries)
                else:
                    print("❌ CAPTCHA detected after multiple retries.")
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
            progress.stop()

            content = self.extract_summary_from_html(html)            

            # Retry if empty or useless
            if self.is_useless_result(content):
                if retry_count < max_retries:
                    wait_time = (retry_count + 1) * self.retry_delay
                    self.log(f"⚠ Empty result, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    return self.query(raw_query + ", answer it anyway", retry_count + 1, max_retries)
                else:
                    print("❌ No valid AI summary after retries.\n")
                    return

            if not content:
                print("❌ No AI summary found.")
                print("💡 Google AI Mode might not have generated a response for this query.\n")
                return

            # Display results
            print("\n" + "="*60)
            full_answer_text = []
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
                    full_answer_text.append(code)
                elif item[0] == 'list':
                    for list_item in item[1]:
                        print(f"- {list_item}")
                    print()
                    full_answer_text.extend(item[1])
                elif item[0] == 'table':
                    for row in item[1]:
                        print(" | ".join(row))
                    print()
                    full_answer_text.extend([" ".join(row) for row in item[1]])
            print("="*60 + "\n")

            # Summarize for memory and update history AFTER displaying results
            # Skip summarization in short mode since responses are already concise
            if full_answer_text and not self.short_mode:
                self.summarize_query(" ".join(full_answer_text))
                
                # Update conversation history (keep last 3 exchanges)
                self.conversation_history.append({
                    'query': current_raw_query,
                    'summary': self.memory
                })
                if len(self.conversation_history) > 3:
                    self.conversation_history.pop(0)
                
                # Update last_query for next iteration
                self.last_query = current_raw_query
            elif full_answer_text and self.short_mode:
                # In short mode, use the answer directly as memory
                short_memory = " ".join(full_answer_text)[:200]
                self.conversation_history.append({
                    'query': current_raw_query,
                    'summary': short_memory
                })
                if len(self.conversation_history) > 3:
                    self.conversation_history.pop(0)
                self.last_query = current_raw_query

        except KeyboardInterrupt:
            raise
        except Exception as e:
            if "chrome not reachable" in str(e).lower():
                self.driver = None
                if retry_count < max_retries:
                    self.log(f"⚠ Browser unreachable, reinitializing...")
                    return self.query(raw_query, retry_count + 1, max_retries)

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
    print("  verbose   - Toggle verbose mode (show/hide detailed logs)")
    print("  short     - Toggle short mode (concise/detailed responses)")
    print("  status    - Show current mode settings")
    print("  quit      - Exit the program")
    print("="*60 + "\n")


def main():
    """Main interactive loop"""
    parser = argparse.ArgumentParser(
        description='Google AI Mode - Interactive Terminal Query Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s                          # Interactive mode
  %(prog)s "what is Python"         # Single query
  %(prog)s -s "explain AI"          # Short mode query
  %(prog)s -v "what is ML"          # Verbose mode query
  %(prog)s -sv "quick answer"       # Short + verbose
  echo "query" | %(prog)s           # Pipe input
        '''
    )
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose mode (show detailed logs)')
    parser.add_argument('-s', '--short', action='store_true',
                       help='Enable short mode (concise responses)')
    parser.add_argument('query', nargs='*',
                       help='Query text (if not provided, enters interactive mode)')
    
    args = parser.parse_args()
    
    # Handle query from arguments
    if args.query:
        ai = GoogleAIMode(verbose=args.verbose, short_mode=args.short)
        try:
            query_text = " ".join(args.query)
            if not args.verbose:
                print(f"Query: {query_text}\n")
            ai.init_driver()
            ai.query(query_text)
        finally:
            ai.close()
        return
    
    # Interactive mode
    if not args.verbose:
        clear_screen()
    print("="*60)
    print("  Google AI Mode - Interactive Terminal Query Tool")
    print("="*60)
    print(f"  Platform: {platform.system()} | Python: {platform.python_version()}")
    if args.verbose:
        print("  Initial Mode: VERBOSE (detailed logs)")
    if args.short:
        print("  Initial Mode: SHORT (concise responses)")
    print("="*60)
    print("\nType 'help' for commands, 'quit' to exit")
    print("You can toggle verbose/short modes anytime during the session\n")

    ai = GoogleAIMode(verbose=args.verbose, short_mode=args.short)
    
    # Pre-initialize browser
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
                ai.last_query = ""
                ai.conversation_history = []
                print("✓ Conversation memory reset.\n")
                continue
            elif q_lower == 'verbose':
                ai.verbose = not ai.verbose
                status = "enabled" if ai.verbose else "disabled"
                print(f"✓ Verbose mode {status}.\n")
                continue
            elif q_lower == 'short':
                ai.short_mode = not ai.short_mode
                status = "enabled" if ai.short_mode else "disabled"
                print(f"✓ Short mode {status}.\n")
                continue
            elif q_lower == 'status':
                print("\n" + "="*60)
                print("Current Settings:")
                print(f"  Verbose Mode: {'ON' if ai.verbose else 'OFF'} (detailed logs)")
                print(f"  Short Mode:   {'ON' if ai.short_mode else 'OFF'} (concise responses)")
                print("="*60 + "\n")
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
    
    # Parse arguments properly
    parser = argparse.ArgumentParser(description='Google AI Mode CLI')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose mode')
    parser.add_argument('-s', '--short', action='store_true',
                       help='Enable short mode')
    parser.add_argument('query', nargs='*',
                       help='Query text')
    
    args = parser.parse_args(argv)
    
    ai = GoogleAIMode(verbose=args.verbose, short_mode=args.short)
    try:
        if args.query:
            ai.init_driver()
            query_text = " ".join(args.query)
            if not args.verbose:
                print(f"Querying: {query_text}\n")
            ai.query(query_text)
        else:
            main()
    finally:
        ai.close()


if __name__ == "__main__":
    # Handle stdin input
    if not sys.stdin.isatty():
        stdin_text = sys.stdin.read().strip()
        if stdin_text:
            # Check for flags in sys.argv
            parser = argparse.ArgumentParser()
            parser.add_argument('-v', '--verbose', action='store_true')
            parser.add_argument('-s', '--short', action='store_true')
            args, _ = parser.parse_known_args()
            
            ai = GoogleAIMode(verbose=args.verbose, short_mode=args.short)
            try:
                if not args.verbose:
                    print(f"Query: {stdin_text}\n")
                ai.init_driver()
                ai.query(stdin_text)
            finally:
                ai.close()
        else:
            main()
    else:
        main()