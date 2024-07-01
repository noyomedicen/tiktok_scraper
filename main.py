import asyncio
from playwright.async_api import async_playwright
import os
import aiohttp
import aiofiles
import pandas as pd
from datetime import datetime

# Lista de nombres de usuario de TikTok
#usernames = ["interbancogt","banruralgt","bancoindustrial","gytcontinental","bam.guatemala","bantrabgt","bacgt","bancopromericagt"]
usernames = ["bacgt","bancopromericagt"]

def convert_views(views_str):
    if 'K' in views_str:
        return int(float(views_str.replace('K', '')) * 1000)
    elif 'M' in views_str:
        return int(float(views_str.replace('M', '')) * 1000000)
    else:
        return int(views_str)

async def download_image(url, folder, filename):
    if not url.startswith('http'):
        print(f"Invalid image URL: {url}")
        return None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    async with aiofiles.open(os.path.join(folder, filename), 'wb') as f:
                        await f.write(image_data)
                    return filename
                else:
                    print(f"Error downloading image: {response.status}")
                    return None
    except Exception as e:
        print(f"Exception occurred while downloading image: {e}")
        return None

async def run(playwright, username):
    browser = await playwright.chromium.launch(headless=False)
    page = await browser.new_page()
    await page.goto(f'https://www.tiktok.com/@{username}')

    print(f"Página de {username} cargada correctamente. Obteniendo contenido...")

    for _ in range(30):
        await page.mouse.wheel(0, 2000)
        await page.wait_for_timeout(3000)

    await page.wait_for_selector('a[href*="/video/"]', timeout=60000)

    all_links_elements = await page.query_selector_all('a[href*="/video/"]')

    today = datetime.today().strftime('%Y-%m-%d')
    folder_name = username
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    video_data = []
    image_counter = 1
    for link in all_links_elements:
        href = await link.get_attribute('href')
        if href and href.startswith('https://www.tiktok.com/'):
            parent = await link.query_selector('xpath=ancestor::div[contains(@class, "DivContainer")]')
            if parent:
                views_element = await parent.query_selector('strong[data-e2e="video-views"]')
                picture_element = await parent.query_selector('picture img')
                if views_element and picture_element:
                    views_text = await views_element.inner_text()
                    views_number = convert_views(views_text)
                    image_url = await picture_element.get_attribute('src')
                    image_filename = f"{today}_{image_counter}.jpg"
                    image_id = await download_image(image_url, folder_name, image_filename)
                    if not image_id:
                        image_id = "Sin id"
                    video_data.append((href, views_number, image_id, f"{today}_{image_counter}"))
                    image_counter += 1

    video_data = list(set(video_data))

    print(f"Se encontraron {len(video_data)} videos únicos para {username}:")
    for link, views, image_id, id_post in video_data:
        print(f"{link} - {views} - {image_id} - {id_post}")

    video_filename = os.path.join(folder_name, f'{username}_post_{today}.xlsx')
    df_videos = pd.DataFrame(video_data, columns=['Video Links', 'Views', 'image_id', 'id_post'])
    df_videos['id_perfil'] = username
    df_videos.to_excel(video_filename, index=False)
    print(f'Los enlaces de video, sus vistas y los nombres de las imágenes se han guardado en el archivo {video_filename}.')

    followers_element = await page.query_selector('strong[data-e2e="followers-count"]')
    following_element = await page.query_selector('strong[data-e2e="following-count"]')
    likes_element = await page.query_selector('strong[data-e2e="likes-count"]')
    bio_element = await page.query_selector('h2[data-e2e="user-bio"]')
    profile_image_element = await page.query_selector('img[class*="ImgAvatar"]')

    followers = convert_views(await followers_element.inner_text()) if followers_element else 'N/A'
    following = convert_views(await following_element.inner_text()) if following_element else 'N/A'
    likes = convert_views(await likes_element.inner_text()) if likes_element else 'N/A'
    bio = await bio_element.inner_text() if bio_element else 'N/A'
    profile_image_url = await profile_image_element.get_attribute('src') if profile_image_element else None

    profile_image_filename = f"imagen_cover.jpg"
    if profile_image_url:
        await download_image(profile_image_url, folder_name, profile_image_filename)

    profile_filename = os.path.join(folder_name, f'{username}_perfil_{today}.xlsx')
    df_profile = pd.DataFrame([{
        'Followers': followers, 
        'Following': following, 
        'Likes': likes, 
        'Bio': bio, 
        'Profile Image': profile_image_filename,
        'id_perfil': username
    }])
    df_profile.to_excel(profile_filename, index=False)
    print(f'La información del perfil se ha guardado en el archivo {profile_filename}.')

    await browser.close()

async def main():
    async with async_playwright() as playwright:
        tasks = [run(playwright, username) for username in usernames]
        await asyncio.gather(*tasks)

asyncio.run(main())
