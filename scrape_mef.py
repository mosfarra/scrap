import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

# URL y variables
URL   = "https://apps5.mineco.gob.pe/transparencia/Navegador/default.aspx"
FRAME = "frame0"
WAIT  = 12

def enter_frame(driver: WebDriver):
    driver.switch_to.default_content()
    WebDriverWait(driver, WAIT).until(
        EC.frame_to_be_available_and_switch_to_it((By.NAME, FRAME))
    )

def js_click(driver: WebDriver, element):
    driver.execute_script("arguments[0].scrollIntoView(true);", element)
    driver.execute_script("arguments[0].click();", element)
    enter_frame(driver)

def fast_click(driver: WebDriver, by, value, fallback_wait=WAIT):
    try:
        el = WebDriverWait(driver, 1).until(
            EC.element_to_be_clickable((by, value))
        )
    except:
        el = WebDriverWait(driver, fallback_wait).until(
            EC.element_to_be_clickable((by, value))
        )
    js_click(driver, el)

def click_total_fast(driver: WebDriver):
    try:
        total = driver.find_element(
            By.XPATH, "//input[@name='grp1' and starts-with(@aria-label,'TOTAL')]"
        )
        js_click(driver, total)
    except:
        pass

def a_soles(txt):
    try:
        n = float(txt.replace(',', '').replace(' ', '').replace('S/.','').replace('S/',''))
    except:
        n = 0
    return f"S/. {n:,.2f}"

def main():
    # 1) Conexión al contenedor Selenium
    caps = webdriver.DesiredCapabilities.CHROME.copy()
    driver = webdriver.Remote("http://localhost:4444/wd/hub", caps)
    driver.maximize_window()
    driver.get(URL)
    enter_frame(driver)

    # 2) Secuencia de clicks idéntica a tu script
    Select(WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((By.ID, "ctl00_CPH1_DrpActProy"))
    )).select_by_visible_text("Sólo Proyectos")
    enter_frame(driver)

    click_total_fast(driver)
    fast_click(driver, By.ID, "ctl00_CPH1_BtnTipoGobierno")
    fast_click(driver, By.XPATH,
        "//input[@name='grp1' and contains(@aria-label,'GOBIERNOS LOCALES')]")
    click_total_fast(driver)

    fast_click(driver, By.ID, "ctl00_CPH1_BtnSubTipoGobierno")
    fast_click(driver, By.XPATH,
        "//input[@name='grp1' and contains(@aria-label,'MUNICIPALIDADES')]")
    click_total_fast(driver)

    fast_click(driver, By.ID, "ctl00_CPH1_BtnDepartamento")
    fast_click(driver, By.XPATH,
        "//input[@name='grp1' and contains(@aria-label,'MOQUEGUA')]")
    click_total_fast(driver)

    fast_click(driver, By.ID, "ctl00_CPH1_BtnMunicipalidad")
    fast_click(driver, By.XPATH,
        "//input[@name='grp1' and contains(@aria-label,'MUNICIPALIDAD DISTRITAL DE TORATA')]")
    click_total_fast(driver)

    fast_click(driver, By.ID, "ctl00_CPH1_BtnProdProy")

    # 3) Expande todos los "More..."
    tabla = WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table.Data"))
    )
    while True:
        try:
            more = tabla.find_element(By.CSS_SELECTOR, "tr.More td a")
            driver.execute_script("arguments[0].scrollIntoView(true);", more)
            more.click()
            WebDriverWait(driver, WAIT).until(EC.staleness_of(more))
            tabla = driver.find_element(By.CSS_SELECTOR, "table.Data")
        except:
            break

    # 4) Extrae y formatea
    filas = tabla.find_elements(By.TAG_NAME, "tr")
    validas = [r for r in filas if r.get_attribute("class")!="More"]
    salida = []
    for idx, row in enumerate(validas, start=1):
        tds = row.find_elements(By.TAG_NAME, "td")
        if len(tds)<10: continue
        raw = tds[1].text.strip()
        code,name = raw.split(":",1)
        salida.append({
            "ítem": idx,
            "código": code.strip(),
            "nombre": name.strip(),
            "PIA": a_soles(tds[2].text),
            "PIM": a_soles(tds[3].text),
            "Certificación": a_soles(tds[4].text),
            "Compromiso Anual": a_soles(tds[5].text),
            "Compromiso Mensual": a_soles(tds[6].text),
            "Devengado": a_soles(tds[7].text),
            "Girado": a_soles(tds[8].text),
            "Avance": tds[9].text.strip()+"%"
        })
    driver.quit()

    # 5) Graba JSON
    with open("data.json","w",encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)

if __name__=="__main__":
    main()
