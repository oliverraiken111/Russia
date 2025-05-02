import requests
from bs4 import BeautifulSoup
import datetime
import xml.etree.ElementTree as ET
import json

# NYTimes Russia Spotlight section
url = "https://www.nytimes.com/spotlight/russia"
headers = {"User-Agent": "Mozilla/5.0"}

response = requests.get(url, headers=headers)
response.raise_for_status()
soup = BeautifulSoup(response.text, "html.parser")

# Set up RSS feed
ET.register_namespace('media', 'http://search.yahoo.com/mrss/')
rss = ET.Element('rss', {"version": "2.0", "xmlns:media": "http://search.yahoo.com/mrss/"})
channel = ET.SubElement(rss, 'channel')
ET.SubElement(channel, 'title').text = "NYTimes Russia News"
ET.SubElement(channel, 'link').text = url
ET.SubElement(channel, 'description').text = "Latest news on Russia from The New York Times"
ET.SubElement(channel, 'lastBuildDate').text = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

# Extract Russia-specific articles
articles_found = 0
seen_titles = set()

for teaser in soup.select('a.css-1l4spti'):  # article links (may vary slightly over time)
    title = teaser.get_text(strip=True)
    href = teaser.get("href")

    if not title or not href or title in seen_titles:
        continue

    seen_titles.add(title)
    full_url = href if href.startswith("http") else "https://www.nytimes.com" + href

    # Fetch article page to extract pubDate
    pub_date = datetime.datetime.utcnow()  # fallback if not found
    try:
        article_resp = requests.get(full_url, headers=headers)
        article_resp.raise_for_status()
        article_soup = BeautifulSoup(article_resp.text, "html.parser")

        json_ld_tag = article_soup.find("script", type="application/ld+json")
        if json_ld_tag:
            json_ld = json.loads(json_ld_tag.string)
            if isinstance(json_ld, list):
                json_ld = json_ld[0]
            date_str = json_ld.get("datePublished")
            if date_str:
                pub_date = datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        else:
            # Fallback: look for <time> tag
            time_tag = article_soup.find("time")
            if time_tag and time_tag.has_attr("datetime"):
                pub_date = datetime.datetime.fromisoformat(time_tag["datetime"].replace("Z", "+00:00"))

    except Exception as e:
        print(f"⚠️ Failed to extract pubDate for '{title}': {e}")

    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = title
    ET.SubElement(item, "link").text = full_url
    ET.SubElement(item, "description").text = f"NYTimes article on Russia: {title}"
    ET.SubElement(item, "pubDate").text = pub_date.strftime("%a, %d %b %Y %H:%M:%S GMT")

    articles_found += 1
    if articles_found >= 10:
        break

# Write output
with open("russia.xml", "wb") as f:
    ET.ElementTree(rss).write(f, encoding="utf-8", xml_declaration=True)

print(f"✅ RSS feed created with {articles_found} Russia-specific articles.")
