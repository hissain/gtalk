#!/usr/bin/env python3

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
import re

class GoogleAIMode:
    def __init__(self):
        self.driver = None
        self.memory = ""   # -------- added memory --------

    def init_driver(self):
        if self.driver is not None:
            return

        print("🔄 Initializing browser...")
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
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print("✓ Browser ready!\n")

    # ---------- EXACTLY THE SAME EXTRACTION AS YOURS ----------
    def extract_summary_from_html(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        main_container = soup.select_one('div.mZJni.Dn7Fzd')
        if not main_container:
            return None

        result = []

        for text_div in main_container.select('div.Y3BBE'):
            if text_div.find_parent('div', class_='r1PmQe'):
                continue
            text = text_div.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text).strip()
            if text:
                result.append(('text', text))

        for code_container in main_container.select('div.r1PmQe'):
            lang_div = code_container.select_one('div.vVRw1d')
            language = lang_div.get_text(strip=True) if lang_div else ''
            code_elem = code_container.select_one('pre code')
            if code_elem:
                code = code_elem.get_text()
                result.append(('code', language, code))
            next_text = code_container.find_next_sibling('div', class_='Y3BBE')
            if next_text:
                label = next_text.get_text(strip=True)
                if label and len(label) < 50:
                    result.append(('text', label))

        return result if result else None
    # ---------------------------------------------------------

    def extract_first_paragraph_100_words(self, content_blocks):
        """From extracted blocks, get first paragraph and cut to 100 words."""
        for item in content_blocks:
            if item[0] == 'text':
                words = item[1].split()
                return " ".join(words[:100])
        return ""

    def query(self, raw_query):
        try:
            if self.driver is None:
                self.init_driver()

            # ----- Memory prefix -----
            memory_part = f"Previous summary: {self.memory}. " if self.memory else ""

            # ----- Google trick -----
            trick = (
                "Return a summary of your answer in no more than 100 words in the first paragraph, "
                "then provide the full original answer normally."
            )

            final_query_text = f"{memory_part}{trick} Users query: {raw_query}"

            encoded = urllib.parse.quote_plus(final_query_text)
            url = f"https://www.google.com/search?udm=50&aep=11&q={encoded}"

            print("🔍 Searching...")
            self.driver.get(url)

            time.sleep(3)
            if "captcha" in self.driver.page_source.lower():
                print("❌ CAPTCHA detected. Try again later.")
                return

            try:
                WebDriverWait(self.driver, 8).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.Y3BBE, div.kCrYT, div.hgKElc"))
                )
            except:
                pass

            time.sleep(2)
            html = self.driver.page_source

            content = self.extract_summary_from_html(html)

            if not content:
                print("❌ No AI summary found.\n")
                return

            # ---- Extract and store 100-word memory -----
            new_summary = self.extract_first_paragraph_100_words(content)
            if new_summary:
                self.memory = new_summary  # overwrite

            # ---- Print full answer except memory -----
            print("\n" + "="*60)
            for item in content:
                if item[0] == 'text':
                    print(item[1])
                    print()
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
            print("="*60 + "\n")

        except Exception as e:
            print(f"❌ Error: {str(e)}\n")

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None


def clear_screen():
    import os
    os.system('clear' if os.name == 'posix' else 'cls')

def print_help():
    print("\n" + "="*60)
    print("Commands:")
    print("  [text]    - Query Google AI Mode")
    print("  help      - Show help")
    print("  clear     - Clear terminal")
    print("  quit      - Exit")
    print("="*60 + "\n")

def main():
    clear_screen()
    print("="*60)
    print("  Google AI Mode - Interactive Terminal Query Tool")
    print("="*60)
    print("\nType 'help' for commands, 'quit' to exit\n")

    ai = GoogleAIMode()

    try:
        while True:
            try:
                q = input("Query> ").strip()
            except EOFError:
                print("\nExiting...")
                break

            if not q:
                continue

            if q.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            elif q.lower() == 'help':
                print_help()
                continue
            elif q.lower() == 'clear':
                clear_screen()
                continue

            print()
            ai.query(q)

    except KeyboardInterrupt:
        print("\n\nInterrupted. Bye!")

    finally:
        ai.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        ai = GoogleAIMode()
        try:
            print(f"Querying: {sys.argv[1]}\n")
            ai.query(sys.argv[1])
        finally:
            ai.close()
    else:
        main()
