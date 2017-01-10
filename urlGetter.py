from core import scrapertools

def getStreamcloudVideoUrl(pageUrl):

    
    headers = [['User-Agent','Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14']]
    data = scrapertools.cache_page( pageUrl , headers=headers )

    from servers import streamcloud
    urls = streamcloud.get_video_url(pageUrl)

    for url in urls:
        return url[1]