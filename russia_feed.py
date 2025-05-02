import requests
from bs4 import BeautifulSoup
import datetime
import xml.etree.ElementTree as ET

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

# Extract Russia-specific articles (just from the Spotlight page)
articles_found = 0
seen_titles = set()

# 🛠️ Updated selector: a[data-testid="link"]
for teaser in soup.select('a[data-testid="link"]'):
    title = teaser.get_text(strip=True)
    href = teaser.get("href")

    if not title or not href or title in seen_titles:
        continue

    seen_titles.add(title)
    full_url = href if href.startswith("http") else "https://www.nytimes.com" + href

    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = title
    ET.SubElement(item, "link").text = full_url
    ET.SubElement(item, "description").text = f"NYTimes article on Russia: {title}"
    ET.SubElement(item, "pubDate").text = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

    articles_found += 1
    if articles_found >= 10:
        break

# Write output
with open("russia.xml", "wb") as f:
    ET.ElementTree(rss).write(f, encoding="utf-8", xml_declaration=True)

print(f"✅ RSS feed created with {articles_found} Russia-specific articles.")
