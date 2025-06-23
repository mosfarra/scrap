# scrape_mef.py
import requests
from bs4 import BeautifulSoup
import json
import urllib.parse

BASE = "https://apps5.mineco.gob.pe/transparencia/Navegador/"
START = BASE + "default.aspx"

def extract_tokens(html):
    soup = BeautifulSoup(html, "html.parser")
    def val(name):
        i = soup.find("input", {"name": name})
        return i["value"] if i else ""
    return {
        "__VIEWSTATE":          val("__VIEWSTATE"),
        "__EVENTVALIDATION":    val("__EVENTVALIDATION"),
        "__VIEWSTATEGENERATOR": val("__VIEWSTATEGENERATOR"),
    }

def do_post(session, url, tokens, event_target, extras):
    payload = {
        "__EVENTTARGET":         event_target or "",
        "__EVENTARGUMENT":       "",
        "__VIEWSTATE":           tokens["__VIEWSTATE"],
        "__EVENTVALIDATION":     tokens["__EVENTVALIDATION"],
        "__VIEWSTATEGENERATOR":  tokens["__VIEWSTATEGENERATOR"],
    }
    payload.update(extras or {})
    r = session.post(url, data=payload)
    return r.text

def format_soles(txt):
    try:
        n = float(txt.replace("S/.", "").replace("S/", "")
                  .replace(",", "").strip())
    except:
        n = 0.0
    return f"S/. {n:,.2f}"

def main():
    sess = requests.Session()
    # 1) GET inicial
    r0 = sess.get(START)
    # 2) extraer src del iframe
    soup0 = BeautifulSoup(r0.text, "html.parser")
    frame = soup0.find("iframe", {"name": "frame0"})
    if not frame:
        print("❌ No encontré iframe frame0")
        return
    frame_url = urllib.parse.urljoin(START, frame["src"])

    # 3) GET del iframe para tokens
    html = sess.get(frame_url).text
    tokens = extract_tokens(html)

    # 4) Define la secuencia de pasos
    steps = [
        # Paso dropdown: Sólo Proyectos
        {
          "event": "ctl00$CPH1$DrpActProy",
          "extras": {"ctl00$CPH1$DrpActProy": "Sólo Proyectos"}
        },
        # Paso botón TipoGobierno y radio GOBIERNOS LOCALES
        { "event": "ctl00$CPH1$BtnTipoGobierno",
          "extras": {"ctl00$CPH1$grp1": "GOBIERNOS LOCALES"} },
        # Subtipo → MUNICIPALIDADES
        { "event": "ctl00$CPH1$BtnSubTipoGobierno",
          "extras": {"ctl00$CPH1$grp1": "MUNICIPALIDADES"} },
        # Departamento → MOQUEGUA
        { "event": "ctl00$CPH1$BtnDepartamento",
          "extras": {"ctl00$CPH1$grp1": "MOQUEGUA"} },
        # Municipalidad → TORATA
        { "event": "ctl00$CPH1$BtnMunicipalidad",
          "extras": {"ctl00$CPH1$grp1": "MUNICIPALIDAD DISTRITAL DE TORATA"} },
        # ProdProy
        { "event": "ctl00$CPH1$BtnProdProy", "extras": {} },
    ]

    # 5) Ejecutar cada postback
    for step in steps:
        html = do_post(sess, frame_url, tokens,
                       step["event"], step["extras"])
        tokens = extract_tokens(html)

    # 6) parsear la tabla final
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one("table.Data")
    if not table:
        print("❌ No encontré la tabla.Data tras los postbacks")
        return

    rows = []
    for idx, tr in enumerate(table.select("tr:not(.More)"), start=1):
        tds = tr.find_all("td")
        if len(tds) < 10:
            continue
        raw = tds[1].get_text(strip=True)
        code, name = raw.split(":", 1)
        rows.append({
            "ítem": idx,
            "código": code.strip(),
            "nombre": name.strip(),
            "PIA": format_soles(tds[2].get_text()),
            "PIM": format_soles(tds[3].get_text()),
            "Certificación": format_soles(tds[4].get_text()),
            "Compromiso Anual": format_soles(tds[5].get_text()),
            "Compromiso Mensual": format_soles(tds[6].get_text()),
            "Devengado": format_soles(tds[7].get_text()),
            "Girado": format_soles(tds[8].get_text()),
            "Avance": tds[9].get_text(strip=True) + "%",
        })

    # 7) volcamos a data.json
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    print(f"✅ Generados {len(rows)} registros en data.json")

if __name__ == "__main__":
    main()
