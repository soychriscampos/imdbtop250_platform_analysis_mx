# Scraping IMDb y JustWatch - Documentación Técnica

## IMDb (Top 250 Extraction)

**Fuente:** https://www.imdb.com/chart/top/

**Estructura objetivo:** JSON embedido en `<script id="__NEXT_DATA__">`.

**Campos extraídos desde el JSON**
- `originalTitleText.text` -> Título original de la película.
- `titleText.text` -> Título alternativo.
- `releaseYear.year` -> Año de estreno.
- `ratingsSummary.aggregationRating` -> Calificación IMDb.
- `certificate.rating` -> Duración en segundos (se convierte a minutos).
- `certificate.rating` -> Clasificación (A, B, C, etc)
- `titleGenres.genres[].text` -> Lista de géneros.
- `plot.plotText.plainText` -> Sinopsis de la película.
- `id` -> ID de IMDb para generar la URL del perfil: `https://www.imdb.com/title/{id}/`.

---

## JustWatch (Búsqueda de la Película)

**Fuente:** `https://www.justwatch.com/mx/buscar?q={movie_title}`

**Scrapping en la página de búsqueda**
- `<div class="title-list-row__row>"` -> Contenedor principal de cada resultado de búsqueda.
- Dentro de este div:
  - Segundo `<div class="title-list-row__column">` -> Contiene el enlace correcto al perfil.
  - `<a class="title-list-row__column-header">` -> Contiene el enlace a la página de la película.
  - `<span class="header-year>"` -> Año de la película para validar coincidencia con IMDb.

## JustWatch (Perfil de la película - Plataformas)
**Fuente:** Perfil individual de la película (ejemplo: `https://www.justwatch.com/mx/pelicula/cadena-perpetua`)

**Scraping dentro del perfil**
- `<section class="spinning-texts>"` -> Sección que contiene la información sobre disponibilidad.
- `<article>` -> Contiene el párrafor principal con la descripción de disponibilidad.
- `<p>` -> Texto tipo: Actualmente, usted es capaz de ver "X película" streaming en Netflix, Disney+, HBO Max.


**Lógica aplicada:**
- Se extrae la cadena entre **"streaming en"** y el primer punto **"."**.
- Se separan las plataformas por comas.

**Filtrado posterior:**
- Se excluyen las siguientes menciones:
    - `"Channel"`
    - `"Ads"`
    - `"Premium"`
    - `"gratuita"`
    - `"Microsoft Store"`
    - `"Amazon Video"`
    - `"Nuestro Cine"`
- También se reemplaza:
    - `"o forma gratuita con anuncios en"` -> se transforma en `,` para dividir correctamente las plataformas.
 
**Resultado final:**
- Se retorna la lista limpia de plataformas (o "Ninguna Plataforma" si no se encuentra nada).

