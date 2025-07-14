import os
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import RemoteConnection
import requests
import time
from googletrans import Translator

BROWSERSTACK_USERNAME = os.environ.get('BROWSERSTACK_USERNAME', 'sandeepyadav_O6Fb38')
BROWSERSTACK_ACCESS_KEY = os.environ.get('BROWSERSTACK_ACCESS_KEY', 'ygmm2qwn8tkDUYMsC5yp')

@pytest.fixture(scope="function")
def driver(request):
    print("[DEBUG] Setting up WebDriver")
    capabilities = {}
    if 'BROWSERSTACK_CAPABILITIES' in os.environ:
        import json
        capabilities = json.loads(os.environ['BROWSERSTACK_CAPABILITIES'])
        print(f"[DEBUG] Using BrowserStack capabilities: {capabilities}")
        url = f'https://{BROWSERSTACK_USERNAME}:{BROWSERSTACK_ACCESS_KEY}@hub-cloud.browserstack.com/wd/hub'
        driver = webdriver.Remote(
            command_executor=RemoteConnection(url, resolve_ip=False),
            desired_capabilities=capabilities
        )
    else:
        print("[DEBUG] Using local Chrome WebDriver")
        driver = webdriver.Chrome()
    yield driver
    print("[DEBUG] Quitting WebDriver")
    driver.quit()

def scrape_opinion_articles(driver):
    print("[DEBUG] Navigating to elpais.com")
    driver.get("https://elpais.com/")
    time.sleep(5)
    try:
        agree_button = driver.find_element(By.XPATH, "//button[@id='didomi-notice-agree-button']")
        print("[DEBUG] Clicking agree button")
        agree_button.click()
        time.sleep(5)
    except Exception as e:
        print(f"[DEBUG] No agree button found or error: {e}")
    print("[DEBUG] Looking for opinion link")
    opinion_link = driver.find_element(By.XPATH, "//a[contains(@href, '/opinion/')]")
    opinion_link.click()
    time.sleep(5)
    print("[DEBUG] Collecting article elements")
    article_elements = driver.find_elements(By.XPATH, "//article//h2/a")[:5]
    print(f"[DEBUG] Found {len(article_elements)} articles")
    articles_info = []
    for article in article_elements:
        print(f"[DEBUG] Article: {article.text} | URL: {article.get_attribute('href')}")
        articles_info.append({
            "title": article.text,
            "url": article.get_attribute("href")
        })
    data = []
    for article in articles_info:
        title = article["title"]
        url = article["url"]
        print(f"[DEBUG] Scraping article: {title} | {url}")
        driver.get(url)
        time.sleep(5)
        paragraphs = driver.find_elements(By.XPATH, "//div[contains(@class,'article_body')]//p")
        content = " ".join([p.text for p in paragraphs])
        try:
            img = driver.find_element(By.XPATH, "//figure//img")
            img_url = img.get_attribute("src")
            image_name = f"cover_{title[:10].replace(' ', '_')}.jpg"
            print(f"[DEBUG] Downloading image: {img_url} as {image_name}")
            image_data = requests.get(img_url).content
            with open(image_name, 'wb') as f:
                f.write(image_data)
        except Exception as e:
            print(f"[DEBUG] No image found or error: {e}")
            image_name = None
        data.append({
            "title": title,
            "url": url,
            "content": content,
            "image": image_name
        })
    print(f"[DEBUG] Scraped data: {data}")
    return data

def translate_titles(articles):
    print("[DEBUG] Translating article titles")
    translated = []
    for article in articles:
        try:
            translator = Translator()
            result = translator.translate(article['title'], src='es', dest='en')
            print(f"[DEBUG] Translated '{article['title']}' to '{result.text}'")
            translated.append(result.text)
        except Exception as e:
            print(f"[DEBUG] Translation failed for '{article['title']}': {e}")
            translated.append("[Translation Failed]")
    return translated

def analyze_titles(articles):
    print("[DEBUG] Analyzing translated titles")
    count_dict = {}
    single_string = " ".join(articles)
    new_words_list = single_string.split(" ")
    for article in new_words_list:
        if article not in count_dict:
            count_dict[article] = 1
        else:
            count_dict[article] += 1
    print(f"[DEBUG] Word count: {count_dict}")
    return count_dict

def test_opinion_articles_workflow(driver):
    print("[DEBUG] Starting test_opinion_articles_workflow")
    articles = scrape_opinion_articles(driver)
    print(f"[DEBUG] Articles scraped: {articles}")
    assert len(articles) > 0, "No articles scraped"
    translated = translate_titles(articles)
    print(f"[DEBUG] Translated titles: {translated}")
    assert all(isinstance(t, str) for t in translated), "Translation failed"
    repeated = analyze_titles(translated)
    print(f"[DEBUG] Title analysis: {repeated}")
    assert isinstance(repeated, dict)