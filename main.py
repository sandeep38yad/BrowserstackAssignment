from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import RemoteConnection
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




