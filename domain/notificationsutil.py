import xbmc
import xbmcgui
import xbmcaddon

title = "Kodi Organizer"
addon = xbmcaddon.Addon("service.kodiorganizer")

def show(message, withSound=False):
	xbmcgui.Dialog().notification(title,message,time=4000,icon=xbmc.translatePath(addon.getAddonInfo('path') + "/icon.png"),sound=withSound)

def writelog(message):
        xbmc.log(message, xbmc.LOGNOTICE)