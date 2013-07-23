TITLE  = 'TV4 Play'
PREFIX = '/video/tv4play'

BASE_URL = 'http://www.tv4play.se'  

RE_VIDEO_ID = '(?<=video_id=)[0-9]+'

HTTP_USER_AGENT   = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/536.26.17 (KHTML, like Gecko) Version/6.0.2 Safari/536.26.17"

CATEGORIES_URL   = 'http://api.tv4play.se/video/categories/list'
PROGRAMS_URL     = 'http://api.tv4play.se/video/program_formats/list.json?sorttype=name&premium_filter=free&category=%s'
CLIPS_URL        = 'http://api.tv4play.se/video/tv4play/programs/search.json?premium=false&includedrm=wvm&video_types=clips&livepublished=false&sorttype=date&start=%s&rows=%s&categoryids=%s&' 
EPISODES_URL     = 'http://api.tv4play.se/video/tv4play/programs/search.json?premium=false&includedrm=wvm&video_types=programs&livepublished=false&sorttype=date&start=%s&rows=%s&categoryids=%s&'

# Default artwork and icon(s)
ART   = "art-default.jpg"
THUMB = 'icon-default.png'

ITEMS_PER_PAGE = 25

NO_PROGRAMS_FOUND_HEADER  = "Inga program funna"
NO_PROGRAMS_FOUND_MESSAGE = unicode("Kunde ej hitta några program. Var god försök senare")

####################################################################################################
def Start():
    # Set the default ObjectContainer attributes
    ObjectContainer.title1 = TITLE
    ObjectContainer.art    = R(ART)

    # Set the default cache time
    HTTP.CacheTime             = 300
    HTTP.Headers['User-agent'] = HTTP_USER_AGENT

####################################################################################################
@handler(PREFIX, TITLE, thumb = THUMB, art = ART)
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
                key = Callback(TV4Shows, categoryName = category["name"], categoryId = unicode(category["id"])),
                title = unicode(category["name"]),
                thumb = None
            )
        )

    return oc

####################################################################################################
@route(PREFIX + '/TV4Shows')
def TV4Shows(categoryName, categoryId):
    oc         = ObjectContainer(title2 = unicode(categoryName))
    categoryId = String.Quote(categoryId)
    
    try:
        programs = JSON.ObjectFromURL(PROGRAMS_URL % categoryId)

        for program in programs:
            oc.add(
                DirectoryObject( 
                    key = 
                        Callback(
                    	    TV4ShowChoice, 
                            showName = program["name"], 
                            showId = unicode(program["id"]), 
                            art = GetImgURL(program["largeimage_highres"]),
                            thumb = GetImgURL(program["image"]),
                            summary = program["text"]
                        ), 
                    title = unicode(program["name"]),
                    summary = unicode(program["text"]), 
                    thumb = GetImgURL(program["image"]),
                    art = GetImgURL(program["largeimage_highres"])
                )
            )
    
    except:
        oc.header  = NO_PROGRAMS_FOUND_HEADER
        oc.message = unicode("Kunde ej få kontakt med TV4 servern")

    return oc

####################################################################################################
@route(PREFIX + '/TV4ShowChoice')
def TV4ShowChoice(showName, showId, art, thumb, summary):
    oc = ObjectContainer(title2 = unicode(showName))
        
    showId   = String.Quote(showId)
    episodes = JSON.ObjectFromURL(EPISODES_URL % (0, 0, showId))
    clips    = JSON.ObjectFromURL(CLIPS_URL % (0, 0, showId))
        
    if episodes['total_hits'] > 0 and clips['total_hits'] > 0: 
        oc.add(
            DirectoryObject(
            	key = 
            		Callback(
                        TV4Videos, 
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
                	Callback(
                		TV4Videos, 
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
        
    else:
        oc.header  = NO_PROGRAMS_FOUND_HEADER
        oc.message = NO_PROGRAMS_FOUND_MESSAGE 
              
    return oc

####################################################################################################
@route(PREFIX + '/TV4Videos', episodeReq = bool, offset = int)
def TV4Videos(showName, showId, art, episodeReq, offset = 0):
    oc = ObjectContainer(title2 = unicode(showName))

    if episodeReq: 
        videos = JSON.ObjectFromURL(EPISODES_URL % (offset, ITEMS_PER_PAGE, showId))
    else:
        videos = JSON.ObjectFromURL(CLIPS_URL % (offset, ITEMS_PER_PAGE, showId))

    # Add videos from JSON info
    for video in videos['results']:
        url = BASE_URL + "/program/" + "%s?video_id=%s" % (showId, str(video['vmanprogid']))
                        
        if True:
            publishdate = str(video['publishdate'])
            year        = publishdate[0:4]
            month       = publishdate[4:6]
            day         = publishdate[6:8]
            airdate     = Datetime.ParseDate(year + '-' + month + '-' + day)
        else:
            airdate = None
          
        if video['lead'] != None:
            description = video['lead']
        else:
            description = ""  
          
        try:
            episode = int(Regex('.* *Del *([0-9]+) *.*', Regex.IGNORECASE).search(video['name']).groups()[0])
        except:
            episode = None        
          
        if video['availability']['human'] != None:
            availabilty = video['availability']['human']
        else:
            availabilty = ""                      

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
                    Callback(
                    	TV4Videos,
                        showName = showName, 
                        showId = showId, 
                        art = art,
                        episodeReq = episodeReq,
                        offset = offset + ITEMS_PER_PAGE
                    ), 
                title = "Fler ...",
                summary = "Vidare till sida " + str(nextPage) + " av " + str(lastPage),
                art = art
            )
        )   

    if len(oc) < 1:
        oc.header  = NO_PROGRAMS_FOUND_HEADER
        oc.message = NO_PROGRAMS_FOUND_MESSAGE

    return oc

####################################################################################################
def GetImgURL(url):
    if '.jpg' in url:
        return url[url.rfind("http") : url.rfind(".jpg") + 4]
    elif '.png' in url: 
        return url[url.rfind("http") : url.rfind(".png") + 4]
    else:
        return url[url.rfind("http") :]
