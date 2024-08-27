import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

url = "https://curve.fi/#/ethereum/pools?sortBy=tvl"
pool_url = "https://curve.fi/#/ethereum/pools/steth/deposit"


def get_pool_list(url):
    import data_file

    start_point = len(data_file.data)

    options = webdriver.ChromeOptions()
    # 창 숨기는 옵션 추가
    options.add_argument("headless")
    driver = webdriver.Chrome(
        options=options, service=Service(ChromeDriverManager().install())
    )
    driver.get(url)
    # If "sc-5a736361-0" class is not found, it means that the page is not fully loaded yet.
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, "sc-5a736361-0"))
    )
    list_of_pool = driver.find_elements(
        by=By.XPATH, value="//div[contains(@class, 'sc-799c1889-0 dkCmum')]"
    )

    data = data_file.data

    for idx in tqdm.tqdm(range(start_point, len(list_of_pool))):
        pool = list_of_pool[idx]
        # Click new tab
        print(pool.text)
        pool.click()
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "tv-lightweight-charts"))
            )
        except Exception:
            pass
        pool_address = ""
        token_address = ""

        for _ in range(10):
            try:
                pool_token_address = (
                    driver.find_element(
                        by=By.XPATH,
                        value='//span[text()="Pool / Token"]/following-sibling::span',
                    )
                    .find_element(
                        by=By.XPATH,
                        value='//a[@class="sc-3754ab78-0 iWStLV sc-4e644a1c-4 IElwW"]',
                    )
                    .get_attribute("href")
                    .split("/")[-1]
                )
                pool_address = pool_token_address
                token_address = pool_token_address
            except Exception:
                try:
                    contracts = driver.find_element(
                        by=By.XPATH,
                        value="//span[text(" ')="Token"]/following-sibling::span',
                    ).find_elements(
                        by=By.XPATH,
                        value='//a[@class="sc-3754ab78-0 iWStLV sc-4e644a1c-4 '
                        'IElwW"]',
                    )
                    pool_address = contracts[0].get_attribute("href").split("/")[-1]
                    token_address = contracts[1].get_attribute("href").split("/")[-1]
                except Exception:
                    pass

            if pool_address and token_address:
                break

        print(pool_address, token_address)
        data[pool_address] = {"LP_TOKEN": token_address}
        driver.back()
        driver.back()
        WebDriverWait(driver, 100).until(
            EC.presence_of_element_located((By.CLASS_NAME, "sc-5a736361-0"))
        )
        list_of_pool = driver.find_elements(
            by=By.XPATH, value="//div[contains(@class, 'sc-799c1889-0 dkCmum')]"
        )

        with open("data_file.py", "w") as py_file:
            py_file.write("data = " + repr(data))


if __name__ == "__main__":
    get_pool_list(url)
