import requests
from bs4 import BeautifulSoup
import json

# 1) URL ya con todos los filtros aplicados en la query string:
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
    """Convierte 'S/. 4,000,000' → 'S/. 4,000,000.00'"""
    try:
        num = float(txt.replace('S/.','').replace(',','').strip())
    except:
        num = 0
    return f"S/. {num:,.2f}"

def main():
    # 2) Petición GET
    r = requests.get(URL)
    soup = BeautifulSoup(r.text, 'html.parser')

    # 3) Localiza la tabla y todas sus filas válidas
    table = soup.select_one('table.Data')
    trs = table.select('tr:not(.More)')

    rows = []
    for idx, tr in enumerate(trs, start=1):
        tds = tr.find_all('td')
        if len(tds) < 10:
            continue
        code, name = tds[1].get_text(strip=True).split(':',1)
        rows.append({
            'ítem': idx,
            'código': code.strip(),
            'nombre': name.strip(),
            'PIA': format_soles(tds[2].get_text()),
            'PIM': format_soles(tds[3].get_text()),
            'Certificación': format_soles(tds[4].get_text()),
            'Compromiso Anual': format_soles(tds[5].get_text()),
            'Compromiso Mensual': format_soles(tds[6].get_text()),
            'Devengado': format_soles(tds[7].get_text()),
            'Girado': format_soles(tds[8].get_text()),
            'Avance': tds[9].get_text(strip=True) + '%'
        })

    # 4) Volcar a data.json
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
