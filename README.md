# Filtro laboral

Automatización en Python que reúne ofertas de empleo desde feeds RSS y alertas de correo, las puntúa según un perfil que tú defines y te envía un resumen por correo dos veces al día. Sirve para cualquier tipo de trabajo: tú decides qué buscar, qué evitar y desde dónde. Se ejecuta sola en GitHub Actions, sin dejar ningún computador encendido.

> **Estado:** prototipo personal en desarrollo. Filtra y prioriza ofertas, pero no postula por ti y no reemplaza la revisión manual.

## Qué hace

1. Cada hora, un workflow de GitHub Actions ejecuta el script.
2. El script lee dos tipos de fuentes:
   - **Feeds RSS** listados en `fuentes.txt`.
   - **Alertas de empleo por correo** que llegan a una cuenta de Gmail dedicada al script (lectura por IMAP).
3. Descarta ofertas ya vistas y las que contienen palabras de exclusión.
4. Asigna un puntaje según cuántas palabras de tu perfil aparecen en cada oferta.
5. Después de las 8:00 y de las 20:00 (hora de Chile) envía un correo con las mejores ofertas acumuladas, ordenadas por puntaje.

```
RSS ──────────────┐
                  ├─► filtro + puntaje ─► pendientes ─► correo (mañana y noche)
alertas por correo┘
```

## Requisitos

- Una cuenta de GitHub (el repositorio donde corre el workflow conviene que sea privado).
- Una cuenta de Gmail **aparte** para el script, con verificación en dos pasos y una contraseña de aplicación.
- Python 3.12 si quieres probarlo en tu computador. Las dependencias están en `requirements.txt` (`feedparser` y `tzdata`).

## IMPORTANTE
para utilizar este script DEBES descargar todo lo que te proporciona este repositorio y luego crear un repositorio privado por tu cuenta con los archivos de este repo, mediante adquiera conocimientos y sepa desarrollar mas mi proyecto creare un archivo ejecutable con una interfaz. si a alguien le interesa ayudar con este proyecto personal favor de contactarme.

## Configuración paso a paso

### 1. Cuenta de correo del script
1. Crea una cuenta de Gmail nueva, solo para este proyecto.
2. Activa la verificación en dos pasos.
3. En la seguridad de esa cuenta, crea una **contraseña de aplicación** (16 letras). Cópiala en ese momento, porque no se vuelve a mostrar.

### 2. Secrets del repositorio
En el repositorio ve a **Settings → Secrets and variables → Actions → New repository secret** y crea estos tres. Los nombres deben ser idénticos:

| Nombre | Contenido |
|---|---|
| `GMAIL_BOT` | Dirección del correo del script |
| `GMAIL_BOT_PASSWORD` | Contraseña de aplicación, sin espacios |
| `GMAIL_USER` | Tu correo personal, donde recibes el resumen |

Nunca escribas estos valores dentro del código ni del workflow.

### 3. Tu perfil
Al inicio de `filtro_laboral.py` define qué buscas. Ejemplo para alguien que busca un cargo de analista de datos:

```python
BUSCAR = ["analista", "data", "datos"]
AFIN = ["python", "sql", "power bi", "excel", "automatización"]
EVITAR = ["senior", "gerente", "10 años"]
EVITAR_TITULO = ["ventas", "chofer"]
CIUDADES_OK = ["santiago"]
```

Cambia las listas por las de tu propio perfil. Más abajo se explica qué hace cada una.

### 4. Fuentes RSS
Edita `fuentes.txt`, una fuente por línea con el formato `nombre | url`. Las líneas vacías y las que empiezan con `#` se ignoran:

```
# nombre | url
Mi fuente | https://ejemplo.com/empleos.rss
```

Cada línea activa debe incluir el `|`, o el script se detiene con un error.

### 5. Alertas por correo
Muchos portales no ofrecen RSS ni permiten scrapear sus páginas, así que la forma segura de cubrirlos es mediante sus alertas de empleo:

- **Opción A:** al crear la alerta en el portal, escribe como destino el correo del script.
- **Opción B:** deja que la alerta llegue a tu correo personal y crea en Gmail un filtro que reenvíe al correo del script solo los mensajes de ese remitente (Configuración → Reenvío y correo POP/IMAP para registrar la dirección; luego un filtro con **Reenviarlo a**). No actives el reenvío de todo tu correo.

Agrega en `REMITENTES` un fragmento del remitente de cada portal (por ejemplo, `indeed.com`).

El script solo procesa mensajes **no leídos** de la bandeja de entrada del correo del script, y los marca como leídos al terminar. Si abres un correo desde esa cuenta, el script ya no lo verá.

### 6. Primera ejecución
En **Actions → (nombre del workflow) → Run workflow**. Si termina con un check verde y te llega un correo con asunto `Resultados de script:`, todo funciona. Revisa spam la primera vez.

## Personalización

| Variable | Para qué sirve |
|---|---|
| `BUSCAR` | Tipo de puesto que buscas. Una oferta del RSS debe contener alguna de estas palabras. Debe tener al menos una |
| `AFIN` | Palabras de tu perfil (habilidades, herramientas, áreas). Cada una que aparezca suma un punto. Una oferta del RSS sin ninguna no aparece en el resumen |
| `EVITAR` | Si aparece alguna en la oferta, se descarta (por ejemplo, niveles de cargo que no buscas) |
| `EVITAR_TITULO` | Igual que `EVITAR`, pero solo mira el título |
| `CIUDADES_OK` | Ciudades aceptadas para ofertas del RSS. Déjala vacía (`[]`) para no filtrar por ciudad |
| `REMITENTES` | Fragmentos de remitente de los correos de alerta que se leerán |
| `IGNORAR_LINK` | Textos de links que no son ofertas (desuscribirse, ayuda, etc.) |

Las ofertas que vienen de alertas por correo no necesitan contener una palabra de `BUSCAR`, porque la alerta del portal ya filtra por tema, y reciben al menos un punto.

## Horarios

- El workflow corre **cada hora** (`cron: "0 * * * *"`).
- El resumen se envía en la primera ejecución posterior a las 8:00 y a las 20:00, hora de Chile (`America/Santiago`). Para otra zona horaria u otros horarios, edita la función `turno_actual`.
- Cada correo incluye hasta 30 ofertas; las que sobran pasan al siguiente.
- Si el envío falla, las ofertas quedan guardadas y se reintentan en la siguiente ejecución.

## Archivos

| Archivo | Función |
|---|---|
| `filtro_laboral.py` | Script principal |
| `fuentes.txt` | Lista de feeds RSS |
| `requirements.txt` | Dependencias de Python |
| `.github/workflows/` | Workflow de GitHub Actions |
| `vistas.json` | Enlaces ya revisados (lo crea el workflow) |
| `pendientes.json` | Ofertas acumuladas aún no enviadas (lo crea el workflow) |
| `estado.json` | Último turno enviado (lo crea el workflow) |

## Prueba local

En PowerShell, dentro de la carpeta del proyecto:

```powershell
pip install -r requirements.txt
$env:GMAIL_BOT="correo-del-script@gmail.com"
$env:GMAIL_BOT_PASSWORD="contraseña-de-aplicacion"
$env:GMAIL_USER="tu-correo@gmail.com"
python filtro_laboral.py
```

Ten en cuenta que ejecutarlo localmente marca como leídos los correos que procese y crea los tres archivos `.json`. Bórralos antes de subir cambios al repositorio.

## Solución de problemas

| Síntoma | Causa probable |
|---|---|
| `AUTHENTICATIONFAILED` o `Invalid credentials` | La contraseña no es de aplicación, tiene espacios, o `GMAIL_BOT` no es la cuenta del script |
| `KeyError: 'GMAIL_BOT'` | Falta el secret o su nombre no coincide |
| No aparecen ofertas de correo | Los mensajes están leídos, en spam, o el remitente no está en `REMITENTES` |
| Un reenvío manual no aparece | El remitente pasa a ser tu propia dirección; el script debe aceptar `GMAIL_USER` como remitente |
| No llega ninguna oferta del RSS | Ninguna contiene palabras de `BUSCAR` y de `AFIN` a la vez, o el sitio bloquea la lectura automatizada |
| `ZoneInfoNotFoundError` en Windows | Falta `pip install tzdata` |
| Falla el último paso del workflow | El workflow necesita `permissions: contents: write` para guardar los `.json` |
| El correo llega a spam | Márcalo como "no es spam" y agrega el remitente a tus contactos |

## Limitaciones

- El filtrado es por **palabras clave**, no entiende el contexto de la oferta. Puede colar ofertas irrelevantes o dejar pasar alguna buena.
- No hace scraping de portales que lo prohíben. Solo usa RSS públicos y alertas que el propio portal envía al correo.
- El formato de los correos de alerta cambia según el portal y puede requerir ajustes en los filtros de links.
- No postula por ti. Cada postulación debe revisarse y enviarse a mano.

## Privacidad y seguridad

- Usa una cuenta de correo exclusiva para el script. Nunca le reenvíes todo tu correo personal.
- Las credenciales van solo en los secrets del repositorio.
- `vistas.json` y `pendientes.json` guardan enlaces de ofertas (los de alertas por correo pueden contener códigos de seguimiento). Por eso conviene que **el repositorio donde corre el workflow sea privado**.
- En repositorios públicos, GitHub desactiva los workflows programados tras 60 días sin actividad.

## Tecnologías

Python (`feedparser`, `imaplib`, `smtplib`, `re`, `json`, `zoneinfo`), GitHub Actions (YAML), Gmail IMAP/SMTP y feeds RSS.
