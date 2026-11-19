# Radar de prácticas

Automatización en Python que revisa ofertas de práctica en distintas fuentes,
las filtra según mi perfil y me envía un resumen por correo cada mañana y cada noche.

## Cómo funciona
1. Cada hora, un workflow de GitHub Actions ejecuta el script.
2. El script lee las fuentes configuradas y puntúa cada oferta según palabras clave
   de mi perfil (Python, SQL, Power BI, automatización, etc.).
3. Descarta ofertas ya vistas y las que piden perfiles senior.
4. A las 8:00 y 20:00 (hora de Chile) envía por correo las mejores ofertas acumuladas.

## Tecnologías
Python, feedparser, smtplib, GitHub Actions.

## Configuración
Las credenciales se guardan como secrets del repositorio:
`GMAIL_BOT`, `GMAIL_BOT_PASSWORD` y `GMAIL_USER`.

## Estado
Prototipo personal en desarrollo. Las fuentes de ofertas se configuran en `FUENTES`.

## IMPORTANTE
Este script funciona usando Github Actions
Esta publicación es puramente para visualización del proyecto, se espera desarrollar un .exe a futuro
