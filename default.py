# -*- coding: utf-8 -*-
#------------------------------------------------------------
#---------------------------------------------------------------------------

import os
import sys
import xbmc
import xbmcplugin
import xbmcgui

import libraryUpdate
import urlGetter

if len(sys.argv) > 1:
    url = sys.argv[2][1:]
    url = urlGetter.getStreamcloudVideoUrl(url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path=url))
else:
    libraryUpdate.main()
