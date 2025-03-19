import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import html
from urllib.parse import quote

# url top 250
url = "https://www.imdb.com/chart/top/?ref_=nv_mv_250"

# browser simulator
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "es-MX,en;q=0.9",
}

# get
response = requests.get(url, headers=headers)


# Extract from IMDb
if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")

    script_tag = soup.find("script", id="__NEXT_DATA__")

    if script_tag:
        data = json.loads(script_tag.string)

        movies = data["props"]["pageProps"]["pageData"]["chartTitles"]["edges"]

        # the lists
        original_titles = []
        alt_titles = []
        years = []
        ratings = []
        durations = []
        certificates = []
        genres_list = []
        plots = []
        urls = []

        for movie in movies:
            movie_data = movie["node"]

            # titles
            original_title = html.unescape(movie_data["originalTitleText"]["text"])
            alt_title = html.unescape(movie_data["titleText"]["text"])
            original_titles.append(original_title)
            alt_titles.append(alt_title)

            # year
            year = movie_data.get("releaseYear", {}).get("year", "Desconocido")
            years.append(year)

            # url
            imdb_url = f"https://www.imdb.com/title/{movie_data['id']}/"
            urls.append(imdb_url)

            # rating
            rating = movie_data.get("ratingsSummary", {}).get("aggregateRating", "N/A")
            ratings.append(rating)

            # duration
            duration_seconds = movie_data.get("runtime", {}).get("seconds", None)
            duration_minutes = round(duration_seconds / 60) if duration_seconds else "Desconocido"
            durations.append(duration_minutes)

            # certificate
            certificate_data = movie_data.get("certificate")
            certificate = certificate_data["rating"] if isinstance(certificate_data, dict) else "Desconocido"
            #certificate = movie_data.get("certificate", {}).get("rating", "Desconocido")
            certificates.append(certificate)

            # genre(s)
            genres = [genre["genre"]["text"] for genre in movie_data.get("titleGenres", {}).get("genres", [])]
            genres_list.append(", ".join(genres) if genres else "Desconocido")

            # summary
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


    else:
        print("No se encontró la estructura JSON en la página")

else:
    print(f"Error al acceder a la página: {response.status_code}")



# Extract from Justwatch:
# searching movie title and get the "movie profile"
# movie profile url function
def movie_profile_url(movie_title, movie_year):
    movie_title_url = quote(movie_title)

    # querying the movie title
    search_url = f"https://www.justwatch.com/mx/buscar?q={movie_title_url}"
    response = requests.get(search_url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        # searching for the correct movie:
        
        # query result,  movie container
        results = soup.find_all("div", class_="title-list-row__row")


        for result in results:
            # Two divs with the same class, the 2 second is needed
            columns = result.find_all("div", class_="title-list-row__column")
            if len(columns) > 1:
                column = columns[1]
            else:
                column = None
            
            if column:
                # <a> tag is the container of the validation data
                link = column.find("a", class_="title-list-row__column-header")

                if link and "href" in link.attrs:
                    slot_container = link.find("span", class_="slot-container")

                    if slot_container:
                        span_year = slot_container.find("span", class_="header-year")
                    # extract justwatch year
                        if span_year:
                            justwatch_year = span_year.text.strip().replace("(", "").replace(")", "")

                            # compare movie_year with justwatch_year
                            if justwatch_year.isdigit() and int(justwatch_year) == int(movie_year):
                                return "https://www.justwatch.com" + link["href"]

    return None



# get the movie platform(s)
def get_platform(movie_title, movie_year):
    movie_url = movie_profile_url(movie_title, movie_year)

    if movie_url:
        response = requests.get(movie_url, headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")

            section = soup.find("section", class_="spinning-texts")
            if not section:
                return "Ninguna Plataforma"

            article = section.find("article")
            if not article:
                return "Ninguna Plataforma"

            paragraph = article.find("p")
            if not paragraph:
                return "Ningúna Plataforma"

            text = paragraph.text

            start = text.find("streaming en")
            if start == -1:
                return "Ninguna Plataforma"

            start += len("streaming en")
            end = text.find(".", start)

            if end == -1:
                return "Ninguna plataforma"

            platforms_text = text[start:end].strip()

            platforms_text = platforms_text.replace("o forma gratuita con anuncios en", ",")
            
            platforms_list = [p.strip() for p in platforms_text.split(",") if "Channel" not in p and "Ads" not in p and "Premium" not in p 
                              and "gratuita" not in p and "Nuestro Cine" not in p and "Amazon Video" not in p and "Microsoft Store" not in p
                             and "cannel" not in p]

            return ", ".join(platforms_list) if platforms_list else "Ninguna Plataforma"

    return "Ninguna Plataforma"


# Add platform column to the DF
imdb_df["Plataforma"] = imdb_df.apply(lambda row: get_platform(row["Título Original"], row["Año"]), axis=1)

# save the csv
imdb_df.to_csv("data/imdb_top250.csv")