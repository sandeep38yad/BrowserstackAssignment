from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.safari.options import Options as SafariOptions
import requests
import time
from googletrans import Translator
from concurrent.futures import ThreadPoolExecutor


BROWSERSTACK_USERNAME = 'sandeepyadav_O6Fb38'
BROWSERSTACK_ACCESS_KEY = 'ygmm2qwn8tkDUYMsC5yp'


def scrape_opinion_articles(driver):
    print("[INFO] Navigating to El País homepage...")
    driver.get("https://elpais.com/")
    time.sleep(5)

    try:
        print("[INFO] Trying to close cookie popup...")
        agree_button = driver.find_element(By.XPATH, "//button[@id='didomi-notice-agree-button']")
        agree_button.click()
        time.sleep(5)
        print("[INFO] Popup closed.")
    except Exception as e:
        print(f"[WARNING] Popup not found or couldn't be closed: {e}")

    print("[INFO] Navigating to Opinión section...")
    opinion_link = driver.find_element(By.XPATH, "//a[contains(@href, '/opinion/')]")
    opinion_link.click()
    time.sleep(5)

    print("[INFO] Fetching top 5 articles...")
    article_elements = driver.find_elements(By.XPATH, "//article//h2/a")[:5]
    articles_info = []
    for article in article_elements:
        articles_info.append({
            "title": article.text,
            "url": article.get_attribute("href")
        })

    data = []

    for index, article in enumerate(articles_info, 1):
        try:
            title = article["title"]
            url = article["url"]
            print(f"\n[INFO] Processing Article {index}: {title}")
            driver.get(url)
            time.sleep(5)

            paragraphs = driver.find_elements(By.XPATH, "//div[contains(@class,'article_body')]//p")
            content = " ".join([p.text for p in paragraphs])
            # print(f"[INFO] Extracted content length: {len(content)} characters")

            try:
                img = driver.find_element(By.XPATH, "//figure//img")
                img_url = img.get_attribute("src")
                image_name = f"cover_{title[:10].replace(' ', '_')}.jpg"
                image_data = requests.get(img_url).content
                with open(image_name, 'wb') as f:
                    f.write(image_data)
                print(f"[INFO] Cover image saved as: {image_name}")
            except Exception as e:
                print(f"[WARNING] No image found for article '{title}': {e}")
                image_name = None

            data.append({
                "title": title,
                "url": url,
                "content": content,
                "image": image_name
            })

        except Exception as e:
            print(f"[ERROR] Failed to process article {index}: {e}")

    return data



def translate_titles(articles):
    print("\n[INFO] Translating article titles to English using GoogleTranslate...")
    data = []
    for article in articles:
        try:
            translator = Translator()
            result = translator.translate(article['title'], src='es', dest='en')
            print(f"'{article['title']}' -> '{result.text}'")
            data.append(result.text)

        except Exception as e:
            print(f"[ERROR] Translation failed for: {article['title']}, Error: {e}")

    return data



def analyze_titles(articles):
   print("\n[INFO] Analyzing translated titles for repeated words...")
   count_dict = {}
   single_string = " ".join(articles)
   new_words_list = single_string.split(" ")
   for article in new_words_list:
       if article not in count_dict.keys():
            count_dict[article] = 1
       else:
           count_dict[article] += 1

   for word in count_dict.keys():
       if count_dict[word] > 2:
           print(f"[INFO] Word '{word}' is repeated {count_dict[word]} times.")

   if(max(count_dict.values()) < 3):
       print("No words are repeated more than twice.")

   return count_dict



def run_on_browserstack(capabilities):
    print(f"\n[INFO] Running on BrowserStack with capabilities: {capabilities}")
    url = f'https://{BROWSERSTACK_USERNAME}:{BROWSERSTACK_ACCESS_KEY}@hub-cloud.browserstack.com/wd/hub'
    driver = None
    test_passed = False

    try:
        print(f"[INFO] Connecting to BrowserStack at {url}")

        if 'browser' in capabilities:
            if capabilities['browser'] == 'Chrome':
                options = webdriver.ChromeOptions()
            elif capabilities['browser'] == 'Firefox':
                options = webdriver.FirefoxOptions()
            elif capabilities['browser'] == 'Safari':
                options = webdriver.SafariOptions()
            else:
                options = webdriver.ChromeOptions()
        else:
            options = webdriver.ChromeOptions()

        for key, value in capabilities.items():
            options.set_capability(key, value)

        options.set_capability('name',
                               f"El País Article Test - {capabilities.get('browser', capabilities.get('device', 'Unknown'))}")
        options.set_capability('build', 'Article Analysis 1.0')

        driver = webdriver.Remote(
            command_executor=url,
            options=options
        )

        print(f"[INFO] Successfully connected to BrowserStack with session ID: {driver.session_id}")

        articles = scrape_opinion_articles(driver)
        if not articles:
            print("[ERROR] No articles were scraped")
            return

        translated_titles = translate_titles(articles)
        if not translated_titles:
            print("[ERROR] No translations were generated")
            return

        for i, article in enumerate(articles):
            if i < len(translated_titles):
                print(f"Title (ES): {article['title']}")
                print(f"Title (EN): {translated_titles[i]}")

        repeated = analyze_titles(translated_titles)
        print("Repeated Words:", repeated)

        test_passed = True

    except Exception as e:
        print(f"[ERROR] Failed during BrowserStack session: {e}")
        test_passed = False
    finally:
        if driver:
            try:
                if test_passed:
                    print("[INFO] Marking test as PASSED")
                    driver.execute_script(
                        'browserstack_executor: {"action": "setSessionStatus", "arguments": {"status":"passed", "reason": "All tasks completed successfully!"}}')
                else:
                    print("[INFO] Marking test as FAILED")
                    driver.execute_script(
                        'browserstack_executor: {"action": "setSessionStatus", "arguments": {"status":"failed", "reason": "Test encountered errors during execution"}}')
            except Exception as e:
                print(f"[WARNING] Could not set test status: {e}")

            driver.quit()
            print("[INFO] BrowserStack session closed")


def run_parallel_tests():
    capabilities_list = [
        {'browser': 'Chrome', 'browser_version': 'latest', 'os': 'Windows', 'os_version': '11'},
        {'browser': 'Firefox', 'browser_version': 'latest', 'os': 'Windows', 'os_version': '10'},
        {'browser': 'Safari', 'browser_version': 'latest', 'os': 'OS X', 'os_version': 'Monterey'},
        {'device': 'Samsung Galaxy S22', 'realMobile': 'true', 'os_version': '12.0'},
        {'device': 'iPhone 14', 'realMobile': 'true', 'os_version': '16'}
    ]

    print("[INFO] Starting parallel tests on BrowserStack...")
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(run_on_browserstack, capability) for capability in capabilities_list]

        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"[ERROR] Test execution failed: {e}")

    print("[INFO] All BrowserStack tests completed")


def run_locally():
   print("[INFO] Running tests locally using ChromeDriver...")
   driver = webdriver.Chrome()
   articles = scrape_opinion_articles(driver)
   articles = translate_titles(articles)

   repeated = analyze_titles(articles)
   print("Words Count:", repeated)
   driver.quit()




if __name__ == "__main__":

   run_locally()
   # run_parallel_tests()



