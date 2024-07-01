import pandas as pd
from playwright.sync_api import sync_playwright
from datetime import datetime

# Función para parsear la fecha
def parse_date(pub_date_text):
    try:
        # Intentar parsear la fecha en formato MM-DD
        pub_date = datetime.strptime(pub_date_text, "%m-%d")
        # Asumimos el año actual si solo se proporciona mes y día
        pub_date = pub_date.replace(year=datetime.now().year)
    except ValueError:
        try:
            # Intentar parsear la fecha en formato YYYY-MM-DD
            pub_date = datetime.strptime(pub_date_text, "%Y-%m-%d")
        except ValueError:
            return 'N/A'
    
    # Convertir la fecha al formato DD/MM/AA
    return pub_date.strftime("%d/%m/%y")

# Extender las métricas
def convert_metrics(metric_str):
    """
    Convierte las métricas abreviadas en un número extendido.
    """
    if 'K' in metric_str:
        return int(float(metric_str.replace('K', '')) * 1000)
    elif 'M' in metric_str:
        return int(float(metric_str.replace('M', '')) * 1000000)
    else:
        try:
            return int(metric_str)
        except ValueError:
            return 'N/A'

# Función para extraer métricas de video
def get_video_metrics(video_urls):
    data = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()

        for url in video_urls:
            video_data = {"Video URL": url}
            try:
                page.goto(url)
                page.wait_for_selector('h1')  # Wait for the page to load

                # Extracting video metrics (e.g., views, likes, comments, shares)
                video_title = page.query_selector('h1')
                video_data["Title"] = video_title.inner_text() if video_title else 'N/A'

                likes = page.query_selector('strong[data-e2e="like-count"]')
                video_data["Likes"] = convert_metrics(likes.inner_text()) if likes else 'N/A'

                comments = page.query_selector('strong[data-e2e="comment-count"]')
                video_data["Comments"] = convert_metrics(comments.inner_text()) if comments else 'N/A'

                shares = page.query_selector('strong[data-e2e="share-count"]')
                video_data["Shares"] = convert_metrics(shares.inner_text()) if shares else 'N/A'

                saves = page.query_selector('strong[data-e2e="undefined-count"]')
                video_data["Saves"] = convert_metrics(saves.inner_text()) if saves else 'N/A'

                # Extracting publication date
                pub_date_element = page.query_selector('span[data-e2e="browser-nickname"]')
                if pub_date_element:
                    pub_date_text = pub_date_element.inner_text().split("·")[-1].strip()
                    video_data["Publication Date"] = parse_date(pub_date_text)
                else:
                    video_data["Publication Date"] = 'N/A'

                # Extracting audio label
                audio_label_element = page.query_selector('h4[data-e2e="browse-music"] div.css-pvx3oa-DivMusicText')
                video_data["Audio Label"] = audio_label_element.inner_text() if audio_label_element else 'N/A'
                
                print(f"Video URL: {url}")
                print(f"Title: {video_data['Title']}")
                print(f"Publication Date: {video_data['Publication Date']}")
                print(f"Likes: {video_data['Likes']}")
                print(f"Comments: {video_data['Comments']}")
                print(f"Shares: {video_data['Shares']}")
                print(f"Saves: {video_data['Saves']}")
                print(f"Audio Label: {video_data['Audio Label']}")
                print("-" * 40)

            except Exception as e:
                video_data["Error"] = str(e)
                print(f"Error al obtener datos del video {url}: {e}")

            data.append(video_data)

        browser.close()
    return data

# Leer el archivo Excel
archivo_entrada = 'C:\\Users\\arnol\\Desktop\\Tiktok_Scraper\\general_post_2024-06-28.xlsx'
df = pd.read_excel(archivo_entrada)

# Extraer métricas para cada video
video_urls = df['Video Links'].tolist()
metrics_data = get_video_metrics(video_urls)

# Convertir los datos extraídos en un DataFrame y combinarlo con el original
metrics_df = pd.DataFrame(metrics_data)
df = df.merge(metrics_df, left_on='Video Links', right_on='Video URL', how='left').drop(columns=['Video URL'])

# Guardar el DataFrame actualizado en un nuevo archivo Excel
archivo_salida = 'C:\\Users\\arnol\\Desktop\\Tiktok_Scraper\\general_post_2024-06-28_updated.xlsx'
df.to_excel(archivo_salida, index=False)