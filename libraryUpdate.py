# -*- coding: utf-8 -*-
#------------------------------------------------------------
#---------------------------------------------------------------------------


import xbmc
import xbmcgui
import xbmcaddon

import os
import re
import sys
import urlparse
import operator

from domain import pathutil
from domain import jsonutil
from domain import notificationsutil

from core import scrapertools
from core.item import Item
from core import servertools
from core import scraper
from platformcode import xbmc_library

DEFAULT_HEADERS = []
DEFAULT_HEADERS.append( ["User-Agent","Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; es-ES; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12"] )
DEFAULT_HEADERS.append( ["Referer","http://www.pordede.com"] )

PLUGIN_PATH_DATA = xbmc.translatePath("special://home/userdata/addon_data/service.kodiorganizer")
LIBRARY_PATH = pathutil.join(PLUGIN_PATH_DATA, "library")
FOLDER_MOVIES = "Films"
FOLDER_TVSHOWS = "TVShows"
MOVIES_PATH = pathutil.join(LIBRARY_PATH, FOLDER_MOVIES)
TVSHOWS_PATH = pathutil.join(LIBRARY_PATH, FOLDER_TVSHOWS)

SPECIAL_MOVIES_PATH = "special://home/userdata/addon_data/service.kodiorganizer/library/" + FOLDER_MOVIES
SPECIAL_TVSHOWS_PATH = "special://home/userdata/addon_data/service.kodiorganizer/library/" + FOLDER_TVSHOWS

settings = xbmcaddon.Addon(id="service.kodiorganizer")

def main():

    notificationsutil.writelog("Pordede organizer Manual Run...")

    runUpdate = xbmcgui.Dialog().yesno("Kodi Organizer","¿Quieres actualizar tu biblioteca con los favoritos de Pordede")

    if(runUpdate):
        notificationsutil.show("Actualizando tu biblioteca online")
        notificationsutil.writelog("Actualizando tu biblioteca online")
        createLibraryFolders()
        xbmc_library.clean()
        
        if login() is None:
            xbmcgui.Dialog().ok("Kodi Organizer", "Introduce tus credenciales de pordede.com en los settings del Addon")
            return

        notificationsutil.show("Actualizando peliculas...")

        processFilms()

        notificationsutil.show("Actualizando series...")
        
        processTVShows()

        notificationsutil.show("Actualizacion finalizada")
    else:
        notificationsutil.writelog("Actualizacion cancelada")

def login():
    url = "http://www.pordede.com/site/login"
    pordedeUsername = settings.getSetting("pordedeUsername")
    pordedePassword = settings.getSetting("pordedePassword")

    if settings is None or pordedeUsername == "" or pordedePassword == "":
        return None

    post = "LoginForm[username]=" + pordedeUsername  + "&LoginForm[password]=" +  pordedePassword
    headers = DEFAULT_HEADERS[:]

    data = scrapertools.cache_page(url,headers=headers,post=post)

    notificationsutil.writelog("Logueado en Pordede.com")

    return True

def processFilms():

    favoriteFilms = getFavorites("pelis")

    for favoriteFilm in favoriteFilms:

        notificationsutil.writelog("ORIGINAL NAME " + favoriteFilm.originalName)

        if not movieIsAlreadySaved(favoriteFilm):
            processFilm(favoriteFilm)
        #else:
            #Comprobar si el enlace está ok
            #si no lo está borrarla y procesarla de nuevo

def processFilm(favoriteFilm):
    
    streamCloudUrl = None

    originalName = favoriteFilm.originalName

    dialog = xbmcgui.DialogProgressBG()
    dialog.create("Kodi Organizer", "Guardando " + favoriteFilm.title + "...")

    links = getLinks(favoriteFilm)

    dialog.update(25)

    if len(links) == 0:
        notificationsutil.show("No hay enlaces para " + favoriteFilm.title)
        return None

    founded = False

    for link in links:
        
        if(founded == True):
            break
        
        serverLinks = getServerLinks(link)

        dialog.update(75)

        for serverLink in serverLinks:

            if(founded == True):
                break

            streamCloudUrl = getStreamcloudUrl(serverLink.url)

            if streamCloudUrl is not None:
                dialog.update(85)
                favoriteFilm.url = "plugin://service.kodiorganizer/?" + streamCloudUrl
                founded = True

    favoriteFilm.contentTitle = originalName

    if streamCloudUrl is not None:
        saveFilmIntoLibrary(favoriteFilm)
        updateKodiLibrary(SPECIAL_MOVIES_PATH)
    else:
        notificationsutil.show("No hay enlaces para " + favoriteFilm.title)


    dialog.update(100)
    dialog.close()

def processTVShows():

    favoriteTVShows = getFavorites("series")

    for favoriteTVShow in favoriteTVShows:

        originalName = favoriteTVShow.originalName

        episodes = getTVShowEpisodes(favoriteTVShow)

        dialog = xbmcgui.DialogProgressBG()
        dialog.create("Kodi Organizer", "Guardando " + favoriteTVShow.title + "...")

        episodesCount = 0

        episodesToSave = []

        for episode in episodes:

            if episodeIsAlreadySaved(originalName, episode):
                continue

            streamCloudUrl = None

            episodesCount = float(episodesCount + 1)

            percent = int(((episodesCount / len(episodes)) * 100))

            dialog.update(percent, message=favoriteTVShow.title + ": " + episode.title)

            links = getLinks(episode)

            founded = False

            for link in links:

                if(founded == True):
                    break

                serverLinks = getServerLinks(link)

                for serverLink in serverLinks:

                    if founded == True:
                        break

                    streamCloudUrl = getStreamcloudUrl(serverLink.url)
                    
                    if streamCloudUrl is not None:
                        episode.url = "plugin://service.kodiorganizer/?" + streamCloudUrl
                        founded = True

            if streamCloudUrl is not None:
                episodesToSave.append(episode)
            else:
                notificationsutil.show("No hay enlaces para " + episode.title)

        favoriteTVShow.contentTitle = originalName

        saveTVShowIntoLibrary(favoriteTVShow, episodesToSave)

        updateKodiLibrary(SPECIAL_TVSHOWS_PATH)

        dialog.close()

def getFavorites(videoType):
    # Descarga la pagina
    headers = DEFAULT_HEADERS[:]
    #headers.append(["Referer",item.extra])
    headers.append(["X-Requested-With","XMLHttpRequest"])
    data = scrapertools.cache_page("http://www.pordede.com/" + videoType + "/favorite",headers=headers)

    # Extrae las entradas (carpetas)
    json_object = jsonutil.load(data)
    data = json_object["html"]
    filmsItem = Item(channel="pordede", action="peliculas", title="Favoritas", url="http://www.pordede.com/"+ videoType + "/favorite")
    itemList = parse_mixed_results(filmsItem,data)

    return itemList

def getTVShowEpisodes(tvShow):
    itemlist = []
    headers = DEFAULT_HEADERS[:]
    data = scrapertools.cache_page(tvShow.url, headers=headers)

    patrontemporada = '<div class="checkSeason"[^>]+>([^<]+)<div class="right" onclick="controller.checkSeason(.*?)\s+</div></div>'
    matchestemporadas = re.compile(patrontemporada,re.DOTALL).findall(data)

    tvShowId = scrapertools.find_single_match(data,'<div id="layout4" class="itemProfile modelContainer" data-model="serie" data-id="(\d+)"')

    for nombre_temporada,bloque_episodios in matchestemporadas:
        patron  = '<span class="title defaultPopup" href="([^"]+)"><span class="number">([^<]+)</span>([^<]+)</span>(\s*</div>\s*<span[^>]*><span[^>]*>[^<]*</span><span[^>]*>[^<]*</span></span><div[^>]*><button[^>]*><span[^>]*>[^<]*</span><span[^>]*>[^<]*</span></button><div class="action([^"]*)" data-action="seen">)?'
        matches = re.compile(patron,re.DOTALL).findall(bloque_episodios)

        for scrapedurl,numero,scrapedtitle,info,visto in matches:
            title = nombre_temporada.replace("Temporada ", "").replace("Extras", "Extras 0")+"x"+numero+" "+scrapertools.htmlclean(scrapedtitle)
            thumbnail = tvShow.thumbnail
            fanart= tvShow.fanart
            plot = ""
            epid = scrapertools.find_single_match(scrapedurl,"id/(\d+)")
            url = "http://www.pordede.com/links/viewepisode/id/"+epid
            itemlist.append( Item(channel=tvShow.channel, action="findvideos" , title=title , url=url, thumbnail=thumbnail, plot=plot, fulltitle=title, fanart= fanart, show=tvShow.show))

    return itemlist

def parse_mixed_results(item,data):
    patron  = '<a class="defaultLink extended" href="([^"]+)"[^<]+'
    patron += '<div class="coverMini     shadow tiptip" title="([^"]+)"[^<]+'
    patron += '<img class="centeredPic.*?src="([^"]+)"'
    patron += '[^<]+<img[^<]+<div class="extra-info">'
    patron += '<span class="year">([^<]+)</span>'
    patron += '<span class="value"><i class="icon-star"></i>([^<]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    itemlist = []

    for scrapedurl,scrapedtitle,scrapedthumbnail,scrapedyear,scrapedvalue in matches:

        originalName = scrapedurl.split('/')[2]

        m = re.search(r'\d+$', originalName)

        if m is not None:
            numOfNumbers = len(m.group(0))

            originalName = originalName[:-(numOfNumbers+1)]

        title = scrapertools.htmlclean(scrapedtitle)
        if scrapedyear != '':
            title += " ("+scrapedyear+")"
        fulltitle = title
        if scrapedvalue != '':
            title += " ("+scrapedvalue+")"
        thumbnail = urlparse.urljoin(item.url,scrapedthumbnail)
        fanart = thumbnail.replace("mediathumb","mediabigcover")
        plot = ""
        #http://www.pordede.com/peli/the-lego-movie
        #http://www.pordede.com/links/view/slug/the-lego-movie/what/peli?popup=1

        if "/peli/" in scrapedurl or "/docu/" in scrapedurl:

            #sectionStr = "peli" if "/peli/" in scrapedurl else "docu"
            if "/peli/" in scrapedurl:
                sectionStr = "peli"
            else:
                sectionStr = "docu"

            referer = urlparse.urljoin(item.url,scrapedurl)
            url = referer.replace("/{0}/".format(sectionStr),"/links/view/slug/")+"/what/{0}".format(sectionStr)

            itemlist.append( Item(channel=item.channel, action="findvideos" , title=title , extra=referer, url=url, thumbnail=thumbnail, plot=plot, fulltitle=fulltitle, fanart=fanart,
                                  contentTitle=scrapedtitle, originalName=originalName, contentType="movie", context=["buscar_trailer"]))
        else:
            referer = item.url
            url = urlparse.urljoin(item.url,scrapedurl)
            itemlist.append( Item(channel=item.channel, action="episodios" , title=title , extra=referer, url=url, thumbnail=thumbnail, plot=plot, fulltitle=fulltitle, show=title, fanart=fanart,
                                  contentTitle=scrapedtitle, originalName=originalName, contentType="tvshow", context=["buscar_trailer"]))

    return itemlist

def getLinks(item):
    headers = DEFAULT_HEADERS[:]
    data = scrapertools.cache_page(item.url,headers=headers)
    itemlist = []

    sesion = scrapertools.find_single_match(data,'SESS = "([^"]+)";')

    patron  = '<a target="_blank" class="a aporteLink(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)

    for match in matches:
        idiomas = re.compile('<div class="flag([^"]+)">([^<]+)</div>',re.DOTALL).findall(match)
        if len(idiomas) == 1:
            idioma = (idiomas[0][0].replace("&nbsp;","").strip() + " " + idiomas[0][1].replace("&nbsp;","").strip()).strip()

            if idioma == "spanish":
                calidad_video = scrapertools.find_single_match(match,'<div class="linkInfo quality"><i class="icon-facetime-video"></i>([^<]+)</div>')

                if "1080" in calidad_video:
                    calidad_video = 1
                elif "Micro" in calidad_video:
                    calidad_video = 2
                elif "720" in calidad_video:
                    calidad_video = 3
                elif "RIP" in calidad_video:
                    calidad_video = 4
                else:
                    calidad_video = 99

                url = urlparse.urljoin( item.url , scrapertools.find_single_match(match,'href="([^"]+)"') )
                itemlist.append( Item(channel=item.channel, action="play" , title=item.title , url=url, thumbnail=item.thumbnail, fanart= item.fanart, plot=item.plot, extra=sesion+"|"+item.url, fulltitle=item.fulltitle, videoQuality=calidad_video))

    itemlist.sort(key=operator.attrgetter('videoQuality'))

    return itemlist

def getServerLinks(item):

    headers = DEFAULT_HEADERS[:]
    headers.append( ["Referer" , item.extra.split("|")[1] ])

    data = scrapertools.cache_page(item.url,post="_s="+item.extra.split("|")[0],headers=headers)

    url = scrapertools.find_single_match(data,'<p class="nicetry links">\s+<a href="([^"]+)" target="_blank"')
    url = urlparse.urljoin(item.url,url)

    headers = DEFAULT_HEADERS[:]
    headers.append( ["Referer" , item.url ])

    media_url = scrapertools.downloadpage(url,headers=headers,header_to_get="location",follow_redirects=False)

    itemlist = servertools.find_video_items(data=media_url)

    itemsToReturn = []

    for videoitem in itemlist:
        if "http://streamcloud" in videoitem.url:
            videoitem.title = item.title
            videoitem.fulltitle = item.fulltitle
            videoitem.thumbnail = item.thumbnail
            videoitem.channel = item.channel
            itemsToReturn.append(videoitem)

    return itemsToReturn

def getStreamcloudUrl(pageUrl):

    
    headers = [['User-Agent','Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14']]
    data = scrapertools.cache_page( pageUrl , headers=headers )

    if test_video_exists(pageUrl) == False:
        return None
    else:
        return pageUrl

def test_video_exists( page_url ):

    data = scrapertools.cache_page( url = page_url )
    if "<h1>File Not Found</h1>" in data or "<h1>Archivo no encontrado</h1>" in data:
        return False
    else:
        return True

def movieIsAlreadySaved(item):
    path = pathutil.join(MOVIES_PATH, ("%s" % (item.originalName)).strip())

    return pathutil.exists(path);

def episodeIsAlreadySaved(tvShowName, item):
    path = pathutil.join(TVSHOWS_PATH, tvShowName, ("%s" % (item.title.replace(' ', '-'))).strip())

    notificationsutil.writelog("TV PATH: " + path)

    return pathutil.exists(path);

def createLibraryFolders():
    if not pathutil.exists(PLUGIN_PATH_DATA):
        pathutil.mkdir(PLUGIN_PATH_DATA)
    if not pathutil.exists(LIBRARY_PATH):
        pathutil.mkdir(LIBRARY_PATH)

    if not pathutil.exists(MOVIES_PATH):
        if pathutil.mkdir(MOVIES_PATH):
            xbmc_library.establecer_contenido(FOLDER_MOVIES)

    if not pathutil.exists(TVSHOWS_PATH):
        if pathutil.mkdir(TVSHOWS_PATH):
            xbmc_library.establecer_contenido(TVSHOWS_PATH)

def saveFilmIntoLibrary(item):
    path = ""

    base_name = pathutil.validate(item.contentTitle).lower()

    path = pathutil.join(MOVIES_PATH, ("%s" % (base_name)).strip())

    if not pathutil.exists(path):
        pathutil.mkdir(path)
        createStrmFile(base_name, path, item)
        createNfoFile(base_name, path, item)

def saveTVShowIntoLibrary(tvShow, episodes):

    path = ""

    base_name = pathutil.validate(tvShow.contentTitle).lower()

    path = pathutil.join(TVSHOWS_PATH, ("%s" % (base_name)).strip())

    if not pathutil.exists(path):
        pathutil.mkdir(path)
    saveEpisodesIntoLibrary(base_name, episodes)

def saveEpisodesIntoLibrary(tbShowName, episodes):

    for episode in episodes:

        base_name = pathutil.validate(episode.title.replace(' ', '-')).lower()

        path = pathutil.join(TVSHOWS_PATH, tbShowName, ("%s" % (base_name)).strip())

        if not pathutil.exists(path):
            pathutil.mkdir(path)
            createStrmFile(base_name, path, episode)

def createNfoFile(base_name, path, item):
    nfo_path = pathutil.join(path, "%s.nfo" % (base_name))
    nfo_exists = pathutil.exists(nfo_path)

    if not nfo_exists:
        if item.infoLabels['tmdb_id']:
            head_nfo = "https://www.themoviedb.org/movie/%s\n" % item.infoLabels['tmdb_id']
            item_nfo = Item(title=item.contentTitle, channel="biblioteca", action='findvideos',
                            library_playcounts={"%s" % (base_name): 0}, infoLabels=item.infoLabels,
                            library_urls={})
            json = item_nfo.tojson()

            if pathutil.writefile(nfo_path, head_nfo + json):
                xbmc_library.update(FOLDER_MOVIES, pathutil.basename(path) + "/")

def createStrmFile(base_name, path, item):
    strm_path = pathutil.join(path, "%s.strm" % base_name)
    strm_exists = pathutil.exists(strm_path)
    if not strm_exists:
        pathutil.writefile(strm_path, item.url)

def updateKodiLibrary(contentType):
        payload = {"jsonrpc": "2.0", "method": "VideoLibrary.Scan", "params": {"directory": contentType}, "id": 1}
        data = xbmc_library.get_data(payload)
