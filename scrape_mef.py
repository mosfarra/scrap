# scrape_mef.py
import requests
from bs4 import BeautifulSoup
import json

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
        num = float(txt.replace('S/.','').replace(',','').strip())
    except:
        num = 0
    return f"S/. {num:,.2f}"

def main():
    print("🔍 Haciendo GET a:", URL)
    r = requests.get(URL)
    print(f"📄 HTML recibido ({len(r.text)} bytes)")

    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.select_one('table.Data')
    if not table:
        print("❌ NO se encontró <table class=\"Data\"> en el HTML.")
        return

    filas = table.select('tr:not(.More)')
    print(f"✅ Encontradas {len(filas)} filas totales (incluye cabeceras).")

    salida = []
    for idx, tr in enumerate(filas, start=1):
        tds = tr.find_all('td')
        if len(tds) < 10:
            print(f"  – Fila {idx} descartada (solo {len(tds)} celdas).")
            continue

        raw = tds[1].get_text(strip=True)
        if ':' not in raw:
            print(f"  – Fila {idx} descartada (no contiene ':'): “{raw}”")
            continue

        code, name = raw.split(':', 1)
        code = code.strip()
        name = name.strip()
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

    print(f"🔢 Filas válidas procesadas: {len(salida)}")
    print("💾 Escribiendo data.json…")
    with open('data.json','w',encoding='utf-8') as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)
    print("✔️ data.json actualizado correctamente")

if __name__=='__main__':
    main()
