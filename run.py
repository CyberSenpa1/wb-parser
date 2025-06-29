from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import csv
import time
import pandas as pd

search_keyword = str(input("Введите название товара для поиска: "))
scroll = int(input("Введите количество прокруток страницы (рекомендуется 10): "))
kartochki = int(input("Введите количество карточек для парсинга: "))


options = Options()
options.add_argument("--headless")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
driver = webdriver.Chrome(options=options)

driver.get(f"https://www.wildberries.ru/catalog/0/search.aspx?search={search_keyword}")

# Автоматическая прокрутка страницы для подгрузки большего числа товаров
scroll_times = scroll  # Количество прокруток (можно увеличить)
for _ in range(scroll_times):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)  # Ждём подгрузки новых товаров

try:
    # Ждём появления карточек товаров (до 5 секунд)
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CLASS_NAME, "product-card__wrapper"))
    )
    soup = BeautifulSoup(driver.page_source, "html.parser")
    items = soup.find_all("div", class_="product-card__wrapper")
    products = []
    driver2 = webdriver.Chrome(options=options)  # создаём один раз
    if items:
        print(f"Найдено карточек: {len(items)}")
        for item in items[:kartochki]:  # ограничим до n карточек для примера
            # Ссылка
            link_tag = item.find("a", class_="product-card__link")
            link = link_tag["href"] if link_tag and link_tag.has_attr("href") else "Нет данных"
            if link and not link.startswith("http"):
                link = "https://www.wildberries.ru" + link
            # Название
            name_tag = item.find("span", class_="product-card__name")
            product_name = name_tag.text.strip() if name_tag else "Нет данных"
            # Бренд
            brand_tag = item.find("span", class_="product-card__brand")
            brand = brand_tag.text.strip() if brand_tag else "Нет данных"
            # Цена
            price_tag = item.find("ins", class_="price__lower-price")
            price = price_tag.text.strip() if price_tag else "Нет данных"
            # Продавец (парсим страницу товара)
            seller = "Нет данных"
            if link != "Нет данных":
                try:
                    driver2.get(link)
                    time.sleep(2)
                    # Прокрутка страницы товара вниз для подгрузки блока продавца
                    driver2.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    soup2 = BeautifulSoup(driver2.page_source, "html.parser")
                    # 1-я попытка поиска
                    seller_tag = soup2.find("span", class_="seller-info__name")
                    if not seller_tag:
                        seller_tag = soup2.find("div", class_="seller-info__name")
                    if not seller_tag:
                        seller_block = soup2.find("div", class_="product-page__seller")
                        if seller_block:
                            seller_tag = seller_block.find("span") or seller_block.find("div")
                    if not seller_tag:
                        for tag in soup2.find_all(['span', 'div', 'a']):
                            if tag.text and ("продавец" in tag.text.lower() or "продает" in tag.text.lower()):
                                seller_tag = tag
                                break
                    # 2-я попытка после доп. задержки
                    if not seller_tag:
                        time.sleep(2)
                        soup2 = BeautifulSoup(driver2.page_source, "html.parser")
                        seller_tag = soup2.find("span", class_="seller-info__name")
                        if not seller_tag:
                            seller_tag = soup2.find("div", class_="seller-info__name")
                        if not seller_tag:
                            seller_block = soup2.find("div", class_="product-page__seller")
                            if seller_block:
                                seller_tag = seller_block.find("span") or seller_block.find("div")
                        if not seller_tag:
                            for tag in soup2.find_all(['span', 'div', 'a']):
                                if tag.text and ("продавец" in tag.text.lower() or "продает" in tag.text.lower()):
                                    seller_tag = tag
                                    break
                    if seller_tag:
                        seller = seller_tag.text.strip()
                    time.sleep(1)
                except Exception:
                    seller = "Нет данных"
            print(f"Название: {product_name}\nБренд: {brand}\nЦена: {price}\nСсылка: {link}\nПродавец: {seller}\n{'-'*40}")
            products.append([product_name, brand, price, link, seller])
        # Сохраняем в CSV
        with open("products.csv", "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Название", "Бренд", "Цена", "Ссылка", "Продавец"])
            writer.writerows(products)
        # Сохраняем в Excel
        df = pd.DataFrame(products, columns=["Название", "Бренд", "Цена", "Ссылка", "Продавец"])
        df.to_excel("products.xlsx", index=False)
        print("Данные сохранены в products.csv и products.xlsx")
    else:
        print("Элементы не найдены")
except Exception as e:
    print("Ошибка:", e)
finally:
    driver.quit()
    driver2.quit()