import os, re, json, smtplib, ssl, datetime, imaplib, email
from email.message import EmailMessage
from html.parser import HTMLParser
from zoneinfo import ZoneInfo
import feedparser

BUSCAR = ["informatica", "practica", "practicante", "práctica", "practica profesional", "intern"]
AFIN = ["python", "sql", "power bi", "excel", "automatización", "datos",
        "ia", "machine learning", "power apps", "sharepoint", "api", "microsoft 365",
        "desarrollo", "full stack", "soporte", "informática", "ti", "analista", "software"]
EVITAR = ["senior", "sr", "jefe", "gerente", "5 años"]

REMITENTES = ["linkedin.com", "indeed.com", "laborum", "trabajando", "firstjob", "computrabajo"]
IGNORAR_LINK = ["unsubscribe", "desuscrib", "preferences", "preferencias", "privacy",
                "privacidad", "help", "ayuda", "settings", "configur", "terms", "terminos",
                "buscar empleos", "iniciar sesión", "inicia sesión", "postúlese", "postulese",
                "ver todos", "ver más", "cancelar", "anular", "darse de baja",
                "política", "politica", "cookies","postúlate", "postulate"]
IGNORAR_HREF = ["unsub", "optout", "preferences", "privacy", "settings"]
VER_OFERTA = ["ver oferta", "ver empleo", "ver más detalles"]

def contiene(palabra, texto):
    return re.search(rf"\b{re.escape(palabra)}\b", texto) is not None

def puntaje(texto, es_alerta=False):
    t = texto.lower()
    if not es_alerta and not any(contiene(k, t) for k in BUSCAR):
        return 0
    if any(contiene(k, t) for k in EVITAR):
        return 0
    base = sum(1 for k in AFIN if contiene(k, t))
    return max(base, 1) if es_alerta else base

def cargar(ruta, defecto):
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return defecto

def guardar(ruta, datos):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False)

def cargar_fuentes(ruta="fuentes.txt"):
    fuentes = []
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            nombre, url = [x.strip() for x in linea.split("|", 1)]
            fuentes.append((nombre, url))
    return fuentes

class Enlaces(HTMLParser):
    def __init__(self):
        super().__init__()
        self.enlaces = []
        self._href = None
        self._texto = []
        self._bloque = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._texto = []

    def handle_data(self, data):
        data = data.strip()
        if not data:
            return
        if self._href:
            self._texto.append(data)
        else:
            self._bloque.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href:
            texto = " ".join(self._texto)
            es_bloque = False
            if texto.lower() in VER_OFERTA:
                texto = " | ".join(self._bloque[-8:])
                self._bloque = []
                es_bloque = True
            self.enlaces.append((texto, self._href, es_bloque))
            self._href = None

def leer_correos():
    ofertas = []
    m = imaplib.IMAP4_SSL("imap.gmail.com")
    m.login(os.environ["GMAIL_BOT"], os.environ["GMAIL_BOT_PASSWORD"])
    m.select("INBOX")
    _, datos = m.search(None, "UNSEEN")
    for num in datos[0].split():
        try:
            _, raw = m.fetch(num, "(BODY.PEEK[])")
            msg = email.message_from_bytes(raw[0][1])
            remitente = msg.get("From", "").lower()
            if any(r in remitente for r in REMITENTES + [os.environ["GMAIL_USER"].lower()]):
                html = ""
                for parte in msg.walk():
                    if parte.get_content_type() == "text/html":
                        contenido = parte.get_payload(decode=True)
                        if contenido:
                            html += contenido.decode(
                                parte.get_content_charset() or "utf-8", errors="ignore")
                lector = Enlaces()
                lector.feed(html)
                titulos = set()
                for texto, href, es_bloque in lector.enlaces:
                    if len(texto) < 8 or not href.startswith("http"):
                        continue
                    if not es_bloque and any(x in texto.lower() for x in IGNORAR_LINK):
                        continue
                    if any(x in href.lower() for x in IGNORAR_HREF):
                        continue
                    if texto.lower() in titulos:
                        continue
                    titulos.add(texto.lower())
                    ofertas.append({"fuente": "Correo", "titulo": texto[:150], "link": href,
                                    "texto": texto, "alerta": not es_bloque})
            m.store(num, "+FLAGS", "\\Seen")
        except Exception as err:
            print("Correo omitido:", err)
    m.logout()
    return ofertas

def obtener_ofertas():
    ofertas = []
    for nombre, url in cargar_fuentes():
        for e in feedparser.parse(url).entries:
            ofertas.append({
                "fuente": nombre,
                "titulo": e.get("title", ""),
                "link": e.get("link", ""),
                "texto": e.get("title", "") + " " + e.get("summary", ""),
            })
    try:
        ofertas += leer_correos()
    except Exception as err:
        print("No se pudo leer el correo:", err)
    return ofertas

def enviar(cuerpo, turno):
    msg = EmailMessage()
    fecha = datetime.datetime.now(ZoneInfo("America/Santiago"))
    msg["Subject"] = f"Resultados de script: {turno} {fecha:%d-%m-%Y}"
    msg["From"] = os.environ["GMAIL_BOT"]
    msg["To"] = os.environ["GMAIL_USER"]
    msg.set_content(cuerpo)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as s:
        s.login(os.environ["GMAIL_BOT"], os.environ["GMAIL_BOT_PASSWORD"])
        s.send_message(msg)

def turno_actual():
    ahora = datetime.datetime.now(ZoneInfo("America/Santiago"))
    if 8 <= ahora.hour < 20:
        return f"{ahora.date()}-mañana", "mañana"
    if ahora.hour >= 20:
        return f"{ahora.date()}-noche", "noche"
    ayer = ahora.date() - datetime.timedelta(days=1)
    return f"{ayer}-noche", "noche"

def main():
    vistas = set(cargar("vistas.json", []))
    pendientes = cargar("pendientes.json", [])
    estado = cargar("estado.json", {})
    for o in obtener_ofertas():
        if o["link"] in vistas:
            continue
        vistas.add(o["link"])
        p = puntaje(o["texto"], o.get("alerta", False))
        if p > 0:
            pendientes.append({"p": p, "titulo": o["titulo"],
                               "fuente": o["fuente"], "link": o["link"]})
    guardar("vistas.json", list(vistas))
    guardar("pendientes.json", pendientes)
    slot, turno = turno_actual()
    if estado.get("ultimo") != slot:
        pendientes.sort(key=lambda x: x["p"], reverse=True)
        if pendientes:
            cuerpo = "\n\n".join(
                f"[{x['p']}] {x['titulo']} ({x['fuente']})\n{x['link']}"
                for x in pendientes[:25])
        else:
            cuerpo = "Sin ofertas nuevas que coincidan con tu perfil ;("
        enviar(cuerpo, turno)
        pendientes = []
        estado["ultimo"] = slot
        guardar("pendientes.json", pendientes)
        guardar("estado.json", estado)

if __name__ == "__main__":
    main()