import time                           # ← nuevo
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

URL   = "https://apps5.mineco.gob.pe/transparencia/Navegador/default.aspx"
FRAME = "frame0"
WAIT  = 12

# ───────── utilidades ─────────
def enter_frame(driver):
    driver.switch_to.default_content()
    WebDriverWait(driver, WAIT).until(
        EC.frame_to_be_available_and_switch_to_it((By.NAME, FRAME))
    )

def js_click(driver, element):
    driver.execute_script("arguments[0].scrollIntoView(true);", element)
    driver.execute_script("arguments[0].click();", element)
    enter_frame(driver)

# 🔸 1) helper ultrarrápido para botones
def fast_click(driver, by, value, fallback_wait=WAIT):
    try:
        el = WebDriverWait(driver, 1).until(
            EC.element_to_be_clickable((by, value))
        )
    except Exception:
        el = WebDriverWait(driver, fallback_wait).until(
            EC.element_to_be_clickable((by, value))
        )
    js_click(driver, el)

# 🔸 2) TOTAL sin espera
def click_total_fast(driver):
    try:
        total = driver.find_element(
            By.XPATH, "//input[@name='grp1' and starts-with(@aria-label,'TOTAL')]"
        )
        js_click(driver, total)
    except:
        pass

# ───────── formato a soles ─────────
def a_soles(txt):
    """Convierte '4,000,000' → 'S/. 4,000,000.00'."""
    try:
        n = float(txt.replace(',', '').replace(' ', '').replace('S/.', '').replace('S/', ''))
    except:
        n = 0
    return f"S/. {n:,.2f}"

# ───────── flujo principal ─────────
def main():
    opts = webdriver.ChromeOptions()
    opts.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=opts)
    driver.maximize_window()
    driver.get(URL)
    enter_frame(driver)

    # 1) Sólo Proyectos
    Select(WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((By.ID, "ctl00_CPH1_DrpActProy"))
    )).select_by_visible_text("Sólo Proyectos")
    enter_frame(driver)

    click_total_fast(driver)                                    # TOTAL raíz
    fast_click(driver, By.ID, "ctl00_CPH1_BtnTipoGobierno")     # Tipo de Gobierno
    fast_click(driver, By.XPATH,
        "//input[@name='grp1' and contains(@aria-label,'GOBIERNOS LOCALES')]")
    click_total_fast(driver)

    fast_click(driver, By.ID, "ctl00_CPH1_BtnSubTipoGobierno")  # Subtipo
    fast_click(driver, By.XPATH,
        "//input[@name='grp1' and contains(@aria-label,'MUNICIPALIDADES')]")
    click_total_fast(driver)

    fast_click(driver, By.ID, "ctl00_CPH1_BtnDepartamento")     # Departamento
    fast_click(driver, By.XPATH,
        "//input[@name='grp1' and contains(@aria-label,'MOQUEGUA')]")
    click_total_fast(driver)

    fast_click(driver, By.ID, "ctl00_CPH1_BtnMunicipalidad")    # Municipalidad
    fast_click(driver, By.XPATH,
        "//input[@name='grp1' and contains(@aria-label,'MUNICIPALIDAD DISTRITAL DE TORATA')]")
    click_total_fast(driver)

    fast_click(driver, By.ID, "ctl00_CPH1_BtnProdProy")         # ProdProy

    # ─── localizamos la tabla real
    tabla = WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table.Data"))
    )

    # ─── expandir todos los "More..." hasta cargar toda la tabla
    while True:
        try:
            more = tabla.find_element(By.CSS_SELECTOR, "tr.More td a")
            driver.execute_script("arguments[0].scrollIntoView(true);", more)
            more.click()
            WebDriverWait(driver, WAIT).until(EC.staleness_of(more))
            tabla = driver.find_element(By.CSS_SELECTOR, "table.Data")
        except:
            break

    filas = tabla.find_elements(By.TAG_NAME, "tr")
    validas = [r for r in filas if r.get_attribute("class") != "More"]
    print(f"✅ Tabla cargada con {len(validas)} filas válidas")

    # ───────── extracción y formato ─────────
    print("ítem\tCódigo Único de Inversión\tNombre de la Inversión\t"
          "PIA\tPIM\tCertificación\tCompromiso Anual\tCompromiso Mensual\t"
          "Devengado\tGirado\tAvance")
    idx = 1
    for row in validas:
        tds = row.find_elements(By.TAG_NAME, "td")
        if len(tds) < 10:
            continue

        # separar código y nombre
        raw = tds[1].text.strip()
        code, name = raw.split(":", 1)
        code = code.strip()
        name = name.strip()

        pia                = a_soles(tds[2].text.strip())
        pim                = a_soles(tds[3].text.strip())
        certificacion      = a_soles(tds[4].text.strip())
        compromiso_anual   = a_soles(tds[5].text.strip())
        compromiso_mensual = a_soles(tds[6].text.strip())
        devengado          = a_soles(tds[7].text.strip())
        girado             = a_soles(tds[8].text.strip())
        avance             = tds[9].text.strip() + "%"

        # impresión tabulada
        print(f"{idx}\t{code}\t{name}\t"
              f"{pia}\t{pim}\t{certificacion}\t{compromiso_anual}\t"
              f"{compromiso_mensual}\t{devengado}\t{girado}\t{avance}")
        idx += 1

if __name__ == "__main__":
    main()