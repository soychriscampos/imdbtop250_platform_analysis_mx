import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import html
from urllib.parse import quote

def extract_imdb():
    url = "https://www.imdb.com/chart/top/?ref_=nv_mv_250"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "es-MX,en;q=0.9",
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        script_tag = soup.find("script", id="__NEXT_DATA__")

        if script_tag:
            data = json.loads(script_tag.string)
            movies = data["props"]["pageProps"]["pageData"]["chartTitles"]["edges"]

            original_titles, alt_titles, years, ratings, durations, certificates, genres_list, plots, urls = ([] for _ in range(9))

            for movie in movies:
                movie_data = movie["node"]

                original_titles.append(html.unescape(movie_data["originalTitleText"]["text"]))
                alt_titles.append(html.unescape(movie_data["titleText"]["text"]))
                years.append(movie_data.get("releaseYear", {}).get("year", "Desconocido"))
                urls.append(f"https://www.imdb.com/title/{movie_data['id']}/")
                ratings.append(movie_data.get("ratingsSummary", {}).get("aggregateRating", "N/A"))

                duration_seconds = movie_data.get("runtime", {}).get("seconds", None)
                durations.append(round(duration_seconds / 60) if duration_seconds else "Desconocido")

                certificate_data = movie_data.get("certificate")
                certificates.append(certificate_data["rating"] if isinstance(certificate_data, dict) else "Desconocido")

                genres = [genre["genre"]["text"] for genre in movie_data.get("titleGenres", {}).get("genres", [])]
                genres_list.append(", ".join(genres) if genres else "Desconocido")

                plot = movie_data.get("plot", {}).get("plotText", {}).get("plainText", "Sin sinopsis disponible")
                plots.append(plot)

            imdb_df = pd.DataFrame({
                "Título Original": original_titles,
                "Título Alternativo": alt_titles,
                "Año": years,
                "Calificación": ratings,
                "Duración (min)": durations,
                "Clasificación": certificates,
                "Género": genres_list,
                "Sinopsis": plots,
                "URL": urls
            })
            return imdb_df

    print("Error al acceder a IMDb o no se encontró la estructura JSON")
    return pd.DataFrame()


def movie_profile_url(movie_title, movie_year, headers):
    movie_title_url = quote(movie_title)
    search_url = f"https://www.justwatch.com/mx/buscar?q={movie_title_url}"
    response = requests.get(search_url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.find_all("div", class_="title-list-row__row")

        for result in results:
            columns = result.find_all("div", class_="title-list-row__column")
            if len(columns) > 1:
                column = columns[1]
                link = column.find("a", class_="title-list-row__column-header")
                if link and "href" in link.attrs:
                    slot_container = link.find("span", class_="slot-container")
                    if slot_container:
                        span_year = slot_container.find("span", class_="header-year")
                        if span_year:
                            justwatch_year = span_year.text.strip().replace("(", "").replace(")", "")
                            if justwatch_year.isdigit() and int(justwatch_year) == int(movie_year):
                                return "https://www.justwatch.com" + link["href"]
    return None


def get_platform(movie_title, movie_year, headers):
    movie_url = movie_profile_url(movie_title, movie_year, headers)
    if movie_url:
        response = requests.get(movie_url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            section = soup.find("section", class_="spinning-texts")
            if not section: return "Ninguna Plataforma"
            article = section.find("article")
            if not article: return "Ninguna Plataforma"
            paragraph = article.find("p")
            if not paragraph: return "Ninguna Plataforma"

            text = paragraph.text
            start = text.find("streaming en")
            if start == -1: return "Ninguna Plataforma"
            start += len("streaming en")
            end = text.find(".", start)
            if end == -1: return "Ninguna Plataforma"

            platforms_text = text[start:end].strip()
            platforms_text = platforms_text.replace("o forma gratuita con anuncios en", ",")
            platforms_list = [p.strip() for p in platforms_text.split(",") if "Channel" not in p and "Ads" not in p and "Premium" not in p and "gratuita" not in p and "Nuestro Cine" not in p and "Amazon Video" not in p and "Microsoft Store" not in p]
            return ", ".join(platforms_list) if platforms_list else "Ninguna Plataforma"
    return "Ninguna Plataforma"


def transform_add_platforms(imdb_df):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "es-MX,en;q=0.9",
    }
    imdb_df["Plataforma"] = imdb_df.apply(lambda row: get_platform(row["Título Original"], row["Año"], headers), axis=1)
    return imdb_df


def load_to_csv(imdb_df):
    imdb_df.to_csv("data/imdb_top250.csv", index=False)
    print("Datos guardados correctamente en /data/imdb_top250.csv")


if __name__ == "__main__":
    imdb_df = extract_imdb()
    imdb_df = transform_add_platforms(imdb_df)
    load_to_csv(imdb_df)