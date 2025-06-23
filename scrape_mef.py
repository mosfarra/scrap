# scrape_mef.py
import requests
from bs4 import BeautifulSoup
import json

# URL final ya con todos los filtros
URL = (
    "https://apps5.mineco.gob.pe/transparencia/Navegador/"
    "Navegar.aspx?y=2025&ap=Proyecto"
    "&ctl00$CPH1$DrpActProy=Solo+Proyectos"
    "&ctl00$CPH1$BtnTipoGobierno=GOBIERNOS+LOCALES"
    "&ctl00$CPH1$BtnSubTipoGobierno=MUNICIPALIDADES"
    "&ctl00$CPH1$BtnDepartamento=MOQUEGUA"
    "&ctl00$CPH1$BtnMunicipalidad=MUNICIPALIDAD+DISTRITAL+DE+TORATA"
    "&ctl00$CPH1$BtnProdProy=ProdProy"
)

def format_soles(txt):
    try:
        num = float(txt.replace('S/.','').replace(',', '').strip())
    except:
        num = 0
    return f"S/. {num:,.2f}"

def main():
    # 1) Hacer GET y parsear
    r = requests.get(URL)
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.select_one('table.Data')
    if not table:
        print("❌ No se encontró la tabla.Data")
        return

    filas = table.select('tr:not(.More)')
    salida = []

    for idx, tr in enumerate(filas, start=1):
        tds = tr.find_all('td')
        # si no hay suficientes columnas, saltamos
        if len(tds) < 10:
            continue

        raw = tds[1].get_text(strip=True)
        # parche: si no hay ':' en raw, saltamos esta fila
        if ':' not in raw:
            continue

        code, name = raw.split(':', 1)
        code = code.strip()
        name = name.strip()

        # añadimos el objeto formateado
        salida.append({
            'ítem': idx,
            'código': code,
            'nombre': name,
            'PIA': format_soles(tds[2].get_text()),
            'PIM': format_soles(tds[3].get_text()),
            'Certificación': format_soles(tds[4].get_text()),
            'Compromiso Anual': format_soles(tds[5].get_text()),
            'Compromiso Mensual': format_soles(tds[6].get_text()),
            'Devengado': format_soles(tds[7].get_text()),
            'Girado': format_soles(tds[8].get_text()),
            'Avance': tds[9].get_text(strip=True) + '%'
        })

    # 3) Volcar JSON
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)
    print(f"✅ data.json generado con {len(salida)} registros")

if __name__ == '__main__':
    main()
