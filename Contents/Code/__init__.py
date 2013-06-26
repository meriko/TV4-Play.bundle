# -*- coding: utf-8 -*-
import re
import urllib2
import datetime

PLUGIN_TITLE = 'TV4 Play'
PLUGIN_PREFIX = '/video/tv4play'

BASE_URL   = 'http://www.tv4play.se'  

REG_EXP_ID = '(?<=video_id=)[0-9]+'

HTTP_USER_AGENT   = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/536.26.17 (KHTML, like Gecko) Version/6.0.2 Safari/536.26.17"
STREAM_USER_AGENT = "AppleCoreMedia/1.0.0.11G63 (Macintosh; U; Intel Mac OS X 10_7_5; en_us)"

CATEGORIES_URL   = 'http://api.tv4play.se/video/categories/list'
PROGRAMS_URL     = 'http://api.tv4play.se/video/program_formats/list.json?sorttype=name&premium_filter=free&category=%s'
CLIPS_URL        = 'http://api.tv4play.se/video/tv4play/programs/search.json?premium=false&includedrm=wvm&video_types=clips&livepublished=false&sorttype=date&start=%s&rows=%s&categoryids=%s&' 
EPISODES_URL     = 'http://api.tv4play.se/video/tv4play/programs/search.json?premium=false&includedrm=wvm&video_types=programs&livepublished=false&sorttype=date&start=%s&rows=%s&categoryids=%s&'

# Default artwork and icon(s)
PLUGIN_ARTWORK      = 'art-default.jpg'
PLUGIN_ICON_DEFAULT = 'icon-default.png'
PLUGIN_ICON_MORE    = 'icon-more.png'

ART   = "art-default.jpg"
THUMB = 'icon-default.png'

ITEMS_PER_PAGE = 25

####################################################################################################
def Start():
	Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
	Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, PLUGIN_TITLE, PLUGIN_ICON_DEFAULT, PLUGIN_ARTWORK)

	DirectoryObject.art        = R(ART)
	DirectoryObject.thumb      = R(THUMB)
	ObjectContainer.art        = R(ART)
	ObjectContainer.user_agent = STREAM_USER_AGENT
	ObjectContainer.view_group = "List"
	EpisodeObject.art          = R(ART)
	EpisodeObject.thumb        = R(THUMB)
	TVShowObject.art           = R(ART)
	TVShowObject.thumb         = R(THUMB)

	# Set the default cache time
	HTTP.CacheTime             = 300
	HTTP.Headers['User-agent'] = HTTP_USER_AGENT

####################################################################################################
def MainMenu():
	oc = ObjectContainer()
	
	# Add all programs
	oc.add(
		DirectoryObject(
			key = Callback(TV4Shows, categoryName = "Alla program", categoryId = " "), 
			title = "Alla program"
		)
	)
	
	# Add categories
	categories = JSON.ObjectFromURL(CATEGORIES_URL)
	for category in categories:
		oc.add(
			DirectoryObject(
				key = Callback(TV4Shows, categoryName = category["name"], categoryId = category["id"]),
				title = unicode(category["name"]),
				thumb = None
			)
		)

	# Add preference for video resolution
	oc.add(PrefsObject(title = u"Inställningar ..."))

	return oc

####################################################################################################
@route('/video/tv4play/TV4Shows')
def TV4Shows(categoryName, categoryId):
	oc         = ObjectContainer(title2 = unicode(categoryName))
	categoryId = urllib2.quote(categoryId)
	programs   = JSON.ObjectFromURL(PROGRAMS_URL % categoryId)

	for program in programs:
		oc.add(
			DirectoryObject( 
				key = 
					Callback(TV4ShowChoice, 
						showName = program["name"], 
						showId = program["id"], 
						art = getImgUrl(program["largeimage_highres"]),
						thumb = getImgUrl(program["image"]),
						summary = program["text"]
					), 
				title = unicode(program["name"]),
				summary = unicode(program["text"]), 
				thumb = getImgUrl(program["image"]),
				art = getImgUrl(program["largeimage_highres"])
			)
		)

	return oc

####################################################################################################
@route('/video/tv4play/TV4Shows/TV4ShowChoice')
def TV4ShowChoice(showName, showId, art, thumb, summary):
	oc = ObjectContainer(title2 = unicode(showName))
		
	showId   = urllib2.quote(showId)
	episodes = JSON.ObjectFromURL(EPISODES_URL % (0, 0, showId))
	clips    = JSON.ObjectFromURL(CLIPS_URL % (0, 0, showId))
		
	if episodes['total_hits'] > 0 and clips['total_hits'] > 0: 
		oc.add(
			DirectoryObject(key = 
								Callback(TV4Videos, 
									showName = showName, 
									showId = showId, 
									art = art,
									episodeReq = True
								), 
							title = "Hela program",
							thumb = thumb,
							summary = unicode(summary),
							art = art
			)
		)
		      	  	
		oc.add(
			DirectoryObject(
							key = 
								Callback(TV4Videos, 
									showName = showName, 
									showId = showId, 
									art = art,
									episodeReq = False
								), 
							title = "Klipp",
							thumb = thumb,
							summary = unicode(summary),
							art = art
			)
		)
		      
	elif episodes['total_hits'] > 0 or clips['total_hits'] > 0:
		return TV4Videos(
				showName = showName, 
				showId = showId, 
				art = art,
				episodeReq = episodes['total_hits'] > 0
		)
			  
	return oc

####################################################################################################
@route('/video/tv4play/TV4Shows/TV4Videos', episodeReq = bool, offset = int)
def TV4Videos(showName, showId, art, episodeReq, offset = 0):
	oc = ObjectContainer(title2 = unicode(showName))
	oc.view_group = "InfoList"

	if episodeReq: 
		videos = JSON.ObjectFromURL(EPISODES_URL % (offset, ITEMS_PER_PAGE, showId))
	else:
		videos = JSON.ObjectFromURL(CLIPS_URL % (offset, ITEMS_PER_PAGE, showId))

	# Add videos from JSON info
	for video in videos['results']:
		url = BASE_URL + "/program/" + "%s?video_id=%s" % (showId, str(video['vmanprogid']))
    			    	
		try:
			publishdate = str(video['publishdate'])
			year        = int(publishdate[0:4])
			month       = int(publishdate[4:6])
			day         = int(publishdate[6:8])
			airdate     = datetime.date(year, month, day)
		except:
			airdate = None
  		  
		if video['lead'] != None:
			description = video['lead']
		else:
			description = ""  
  		  
		try:
			episode = int(re.search('Del ([0-9]+)', video['name']).group(0))
		except:
			episode = None 		  
  		  
		if video['availability']['human'] != None:
			availabilty = video['availability']['human']
		else:
			availabilty = ""		 	 		  

		if Prefs['qualitypreference'] == "Automatisk":
			pass
		elif Prefs['qualitypreference'] == "Normal (576p)":
			url = url + "?resolution=576"
		elif Prefs['qualitypreference'] == "Mellan (432p)":
			url = url + "?resolution=432"
		else:
			url = url + "?resolution=360"

		if episodeReq:
			oc.add(
				EpisodeObject(
					url = url,
					title = unicode(video['name']),
					index = episode,
					summary = unicode(description + " " + availabilty),
            		show = unicode(showName),
					thumb = video['originalimage'],
					art = art,
					originally_available_at = airdate
				)
			)		
		else:
			oc.add(
				VideoClipObject(
					url = url,
					title = unicode(video['name']),
					summary = unicode(description + " " + availabilty),
					thumb = video['originalimage'],
					art = art,
					originally_available_at = airdate
				)
			)	    

	if offset + ITEMS_PER_PAGE < videos['total_hits']:
		nextPage = (offset / ITEMS_PER_PAGE) + 2
		lastPage = (videos['total_hits'] / ITEMS_PER_PAGE) + 1
		oc.add(
			NextPageObject(
				key = 
					Callback(TV4Videos,
						showName = showName, 
						showId = showId, 
						art = art,
						episodeReq = episodeReq,
						offset = offset + ITEMS_PER_PAGE
					), 
				title = "Fler ...",
				summary = "Vidare till sida " + str(nextPage) + " av " + str(lastPage),
				thumb = R(PLUGIN_ICON_MORE),
				art = art
			)
		)	

	return oc

####################################################################################################
def getImgUrl(url):
  if '.jpg' in url:
    return url[url.rfind("http") : url.rfind(".jpg") + 4]
  elif '.png' in url: 
    return url[url.rfind("http") : url.rfind(".png") + 4]
  else:
    return url[url.rfind("http") :]