import csv
import time
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


BASE_URL   = "https://brawlify.com/ru/brawlers"
LIST_URL   = f"{BASE_URL}/rarity"
OUTPUT_CSV = "data/brawlers.csv"


def slugify(name: str) -> str:

    s = name.lower().replace(" ", "-")
    return re.sub(r"[’'″“]", "", s)

def scrape():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.binary_location = "/usr/bin/google-chrome"
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    print("📥 Загружаем список бойцов…")
    driver.get(LIST_URL)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.row div.card"))
        )
    except Exception as e:
        print("❌ Не удалось дождаться карточек:", e)
        driver.quit()
        return

    cards = driver.find_elements(By.CSS_SELECTOR, "div.row div.card a[href*='/brawlers/']")
    brawlers = []
    for a in cards:
        href = a.get_attribute("href")
        if href.endswith("/rarity"):
            continue
        try:
            img = a.find_element(By.TAG_NAME, "img")
            name = img.get_attribute("alt").strip()
        except:
            name = a.text.strip()
        brawlers.append((name, href))
    print(f"   Найдено {len(brawlers)} персонажей.")

    rows = []
    for name, url in brawlers:
        print(f"⏳ Парсим {name} — {url}")
        driver.get(url)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.table-striped"))
            )
        except:
            print(f"Таблица для {name} не нашлась, пропускаем.")
            continue

        soup = BeautifulSoup(driver.page_source, "lxml")
        table = soup.select_one("table.table-striped")
        stats = {"Name": name}
        for tr in table.find_all("tr"):
            cols = tr.find_all(["th","td"])
            if len(cols) >= 2:
                key = cols[0].get_text(strip=True).rstrip(":")
                val = cols[1].get_text(strip=True)
                stats[key] = val
        rows.append(stats)
        time.sleep(0.3)

    driver.quit()

    if not rows:
        print("❌ Не удалось собрать ни одной записи.")
        return

    fields = list(rows[0].keys())
    print(f"💾 Сохраняем {len(rows)} записей в {OUTPUT_CSV}…")
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print("✅ Готово! Откройте файл data/brawlers.csv")

if __name__ == "__main__":
    scrape()
