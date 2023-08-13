import requests
import feedparser
from feedgen.feed import FeedGenerator
from flask import Flask, request, make_response, render_template
from cacheout import LFUCache

cache = LFUCache()


def get_twitter_embed(url):
    api = 'https://publish.twitter.com/oembed'
    req = requests.get(api, data={
        'url': url,
    })
    if req.status_code == 200:
        return req.json()['html']
    else:
        print("embed_api error")
        return 'embed_api error'


def main(user_id):
    RSS_API = 'https://rss.jeffro.io/twitter/user/{}/'.format(user_id)
    req = requests.get(RSS_API)
    items = []
    if req.status_code == 200:
        feed = feedparser.parse(req.text)
        for entry in feed['entries']:
            title = entry['title']
            link = entry['link']
            # description = entry['description']
            pubDate = entry['published']
            if cache.get(link):
                # print("Cache hit")
                embed = cache.get(link)
            else:
                embed = get_twitter_embed(link)
                cache.set(link, embed)
            items.append({
                'title': title,
                'link': link,
                'description': embed,
                'pubDate': pubDate,
            })

        # replace description in feed
        fg = FeedGenerator()
        fg.title(feed['feed']['title'])
        fg.link(href=feed['feed']['link'], rel='alternate')

        fg.description(feed['feed']['description'])
        fg.link(href=feed['feed']['link'], rel='alternate')
        fg.image(url=feed['feed']['image']['href'],
                 title=feed['feed']['image']['title'],
                 link=feed['feed']['image']['link'])

        for item in items:
            fe = fg.add_entry()
            fe.title(item['title'])
            fe.link(href=item['link'])
            fe.description(item['description'])
            fe.pubDate(item['pubDate'])

        # fg.rss_file('{}.rss'.format(user_id))
        return str(fg.rss_str(pretty=True), encoding='utf-8')
    else:
        print("RSS_API error")
        print(req.text)
        print(user_id)
        print(req.status_code)


app = Flask(__name__)


@app.route('/<user_id>/')
def index(user_id):
    if user_id == 'favicon.ico':
        return '404'
    rss_str = main(user_id)
    response = make_response(rss_str)
    response.headers.set('Content-Type', 'application/xml')
    return response


if __name__ == '__main__':
    app.run()

