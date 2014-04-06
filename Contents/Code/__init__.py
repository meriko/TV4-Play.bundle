from datetime import datetime

TITLE  = 'TV4 Play(beta)'
PREFIX = '/video/tv4playbeta'

ART  = R('art-default.jpg')
ICON = R('icon-default.png')

BASE_URL = 'http://www.tv4play.se'

RE_VIDEO_ID = '(?<=video_id=)[0-9]+'

HTTP_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/536.26.17 (KHTML, like Gecko) Version/6.0.2 Safari/536.26.17"

LOGIN_URL   = 'https://www.tv4play.se/session/new?https='
SESSION_URL = 'https://www.tv4play.se/session'

API_BASE_URL     = 'http://webapi.tv4play.se'
CATEGORIES_URL   = API_BASE_URL + '/video/categories/list'
CHANNELS_URL     = API_BASE_URL + '/play/video_assets?platform=web&is_channel=true'
MOVIES_URL       = API_BASE_URL + '/play/movie_assets?platform=web&start=%s&rows=%s'

TEMPLATE_VIDEO_URL = 'http://www.tv4play.se/%s/%s?video_id=%s'

ITEMS_PER_PAGE = 25

DISCLAIMER_NOTE = unicode("Vissa program är skyddade med DRM(Digital Rights Management). Dessa kan för närvarande ej spelas upp.")
PREMIUM_PREVIEW_NOTE = unicode("Notera att du ej kan spela upp de program som endast är tillgängliga för Premium")

NO_PROGRAMS_FOUND_HEADER  = "Inga program funna"
NO_PROGRAMS_FOUND_MESSAGE = unicode("Kunde inte hitta några program.\r\n\r\n") + DISCLAIMER_NOTE
SERVER_MESSAGE            = unicode("Kunde ej få kontakt med TV4 servern")

DAYS = [
    unicode("Måndag"),
    unicode("Tisdag"),
    unicode("Onsdag"),
    unicode("Torsdag"),
    unicode("Fredag"),
    unicode("Lördag"),
    unicode("Söndag")
]

####################################################################################################
def Start():
    # Set the default ObjectContainer attributes
    ObjectContainer.title1 = TITLE
    ObjectContainer.art    = ART
    
    DirectoryObject.thumb = ICON

    # Set the default cache time
    HTTP.CacheTime             = 300
    HTTP.Headers['User-agent'] = HTTP_USER_AGENT
    
    # Try to login
    Login()

###################################################################################################
def ValidatePrefs():
    oc         = ObjectContainer(title2 = unicode("Inställningar"))
    oc.header  = ""
    oc.message = ""
    
    if PreferencesSetForLogin():
        if Login():
            oc.header = "Inloggad",
            oc.message = unicode("Du är nu inloggad")
        else:
            oc.header = "Inloggningen misslyckades"
            oc.message = unicode("Felaktigt användarnamn eller lösenord.")
            
    elif Prefs['premium']:
        oc.header = "Information saknas"
        oc.message = unicode("Användarnamn och/eller lösenord saknas.")

    elif not Prefs['onlyfree']:
        oc.header = unicode("Alla program")
        oc.message = PREMIUM_PREVIEW_NOTE

    if oc.message:
        oc.message = oc.message + "\r\n\r\n"
         
    oc.message = oc.message + DISCLAIMER_NOTE + unicode("\r\n\r\nStarta om för att inställningarna skall börja gälla")
    
    return oc

###################################################################################################
def GetProgramsURL(name = '', category = ''):
    url = API_BASE_URL + '/video/program_formats/list.json?sorttype=name&name=%s&category=%s' % (name, category)
    if Prefs['onlyfree'] and not Prefs['premium']:
        url = url + '&premium_filter=free'
    
    return url
    
###################################################################################################
def GetVideosURL(id = '', episodes = True, start = 0, rows = 0, text = ''):
    url = API_BASE_URL + '/video/tv4play/programs/search.json?livepublished=false&sorttype=date&start=%s&rows=%s&categoryids=%s&text=%s' % (start, rows, id, text)
    if episodes:
        url = url + '&video_types=programs'
    else:
        url = url + '&video_types=clips'
        
    if Prefs['onlyfree'] and not Prefs['premium']:
        url = url + '&premium=false'
        
    return url

###################################################################################################
def GetVideoURL(id):
    url = API_BASE_URL + '/video/tv4play/programs/search.json?vmanid=%s' % id
        
    if Prefs['onlyfree'] and not Prefs['premium']:
        url = url + '&premium=false'
        
    return url
    
###################################################################################################
def GetLiveURL():
    url = API_BASE_URL + '/video/tv4play/programs/search.json?livepublished=true&sorttype=date&order=asc'
        
    if Prefs['onlyfree'] and not Prefs['premium']:
        url = url + '&premium=false'
        
    return url
    
###################################################################################################
def GetMostWatchedURL():
    url = API_BASE_URL + '/video/tv4play/programs/most_viewed.json?video_types=programs'
        
    if Prefs['onlyfree'] and not Prefs['premium']:
        url = url + '&premium=false'
        
    return url
    
###################################################################################################
def GetListingsURL(date = ""):
    url = API_BASE_URL + '/tvdata/listings/TV4?date=%s' % date
        
    if Prefs['onlyfree'] and not Prefs['premium']:
        url = url + '&premium=false'
        
    return url

###################################################################################################
def PreferencesSetForLogin():
    return (Prefs['premium'] and Prefs['email'] and Prefs['password'])

###################################################################################################
def LoggedIn():
    if not PreferencesSetForLogin():
        return False
        
    response = HTTP.Request(SESSION_URL, cacheTime = 0)
    success  = response.strip().lower() == 'ok'
    
    if not success:
        Log.Warn("Login attempt failed!")
        
    return success     

###################################################################################################
def Login():        
    # Check that the user has entered all required parameters for Login
    if not PreferencesSetForLogin():
        return False

    # Check if we are already logged in ...
    if LoggedIn():
        return True

    # ... else make a new login attempt
    element = HTML.ElementFromURL(LOGIN_URL, cacheTime = 0)
    
    try:
        authenticity_token = element.xpath("//input[@id = 'authenticity_token']")[0]
    except:
        Log.Error("Could not retrieve authenticity token!")
        return False
        
    postData = {}
    postData['user_name']          = Prefs['email']
    postData['password']           = Prefs['password']
    postData['remember_me']        = 'true'
    postData['authenticity_token'] = authenticity_token
    postData['https']              = ''
    postData['my_page']            = 'true'
    
    response = HTTP.Request(SESSION_URL, values = postData, cacheTime = 0)
    
    return LoggedIn()   

####################################################################################################
@handler(PREFIX, TITLE, art = ART, thumb = ICON)
def MainMenu():
    oc = ObjectContainer(no_cache = True)

    oc.add(
        DirectoryObject(
            key = Callback(TV4MostWatched),
            title = unicode("Mest sedda programmen")
        )
    )
    
    oc.add(
        DirectoryObject(
            key = Callback(TV4Catchup),
            title = unicode("Senaste veckans TV")
        )
    )

    categories = JSON.ObjectFromURL(CATEGORIES_URL)

    for category in categories:
        oc.add(
            DirectoryObject(
                key = Callback(TV4Shows, categoryName = category["name"], categoryId = unicode(category["id"])),
                title = unicode(category["name"])
            )
        )

    if Prefs['premium'] or not Prefs['onlyfree']:
        oc.add(
            DirectoryObject(
                key = Callback(TV4Channels),
                title = 'Kanaler'
            )
        )
        
        oc.add(
            DirectoryObject(
                key = Callback(TV4Movies),
                title = 'Filmer'
            )
        )

    oc.add(
        DirectoryObject(
            key = Callback(TV4Shows, categoryName = "Alla program", categoryId = " "), 
            title = "Alla program"
        )
    )

    # Live RTMP only works on PHT
    if Client.Platform == 'Plex Home Theater':
        oc.add(
            DirectoryObject(
                key = Callback(TV4Live),
                title = unicode("Livesändningar")
            )
        )

    searchTitle = unicode("Sök")

    oc.add(
        InputDirectoryObject(
            key = Callback(Search, title = searchTitle),
            title  = searchTitle,
            prompt = searchTitle,
            thumb = ICON
        )
    )

    oc.add(
        PrefsObject(
            title = unicode('Inställningar'),
            summary = unicode('Logga in för att använda Premium\r\n\r\nDu kan även välja att visa alla program. ' + PREMIUM_PREVIEW_NOTE)
        )
    )

    return oc

####################################################################################################
@route(PREFIX + '/TV4Channels')
def TV4Channels():
    oc = ObjectContainer(title2 = 'Kanaler')
    
    channels = JSON.ObjectFromURL(CHANNELS_URL)
    for channel in channels['results']:
        thumb = channel['image']
        if not thumb.startswith('http'):
            thumb = API_BASE_URL + '/play' + thumb
        
        try:
            summary = channel['program']['channel']['about']
        except:
            try:
                summary = channel['description']
            except:
                summary = None
        
        if not Prefs['premium']:
           oc.add(
                DirectoryObject(
                    key = Callback(TV4PremiumRequired),
                    title = channel['title'],
                    thumb = thumb,
                    summary = summary
                )
            )
        else:
            oc.add(
                VideoClipObject(
                    url = TEMPLATE_VIDEO_URL % ('kanaler', channel['program_nid'].replace('live-', ''), channel['id']),
                    title = channel['title'],
                    thumb = thumb,
                    summary = summary
                )
            )
 
        
    return oc

####################################################################################################
@route(PREFIX + '/TV4Live')
def TV4Live():
    oc = ObjectContainer(title2 = unicode('Livesändningar'))
    
    broadcasts = JSON.ObjectFromURL(GetLiveURL())
    
    for video in broadcasts['results']:            
        url = TEMPLATE_VIDEO_URL % ('program', video['nid'], str(video['vmanprogid']))

        try:
            publishdate = str(video['ontime'])
            year        = publishdate[0:4]
            month       = publishdate[4:6]
            day         = publishdate[6:8]
            airdate     = Datetime.ParseDate(year + '-' + month + '-' + day)
        except:
            airdate = None

        if video['lead'] != None:
            description = video['lead']
        else:
            description = ""

        try:
            start_hour   = str(video['ontime'])[8:10]
            start_minute = str(video['ontime'])[10:12]
            start        = start_hour + ":" + start_minute + "\r\n\r\n"
        except:
            start = ""

        if video['availability']['human'] != None:
            availabilty = "\r\n\r\n" + video['availability']['human']
        else:
            availabilty = ""

        if not video['premium'] or LoggedIn():
            oc.add(
                VideoClipObject(
                    url = url,
                    title = unicode(video['name']),
                    summary = unicode(start + description + " " + availabilty),
                    thumb = video['originalimage'],
                    originally_available_at = airdate
                )
            )
        else:
            oc.add(
                DirectoryObject(
                    key = Callback(TV4PremiumRequired),
                    title = unicode(video['name']),
                    summary = unicode(start + description + " " + availabilty),
                    thumb = video['originalimage']
                )
            )
            
    return oc
    
####################################################################################################
@route(PREFIX + '/TV4MostWatched')
def TV4MostWatched():
    oc = TV4Videos(
            showName   = "",
            showId     = None,
            art        = None,
            episodeReq = True,
            url        = GetMostWatchedURL()
        )

    oc.title2 = 'Mest sedda programmen'
    
    return oc
    
####################################################################################################
@route(PREFIX + '/TV4Catchup')
def TV4Catchup():
    oc = ObjectContainer(title2 = unicode('Senaste veckans TV'))

    now = datetime.today()  #TODO Can't find a framework function for this?
    for i in range (0, 7):
        date = now - Datetime.Delta(days = i)
        
        if i == 0:
            title = unicode('Idag')
        elif i == 1:
            title = unicode('Igår')
        else:
            title = DAYS[date.weekday()]
        
        month = str(date.month)
        if len(month) <= 1:
            month = '0' + month
            
        day = str(date.day)
        if len(day) <= 1:
            day = '0' + day
            
        url = GetListingsURL('%s%s%s' % (date.year, month, day))
        dateString = '%s-%s-%s' % (date.year, month, day)
        
        oc.add(
            DirectoryObject(
                key = Callback(TV4ListingVideos, url = url, title = dateString),
                title = title
            )
        )
    
    return oc
    
####################################################################################################
@route(PREFIX + '/TV4ListingVideos')
def TV4ListingVideos(url, title):
    oc = ObjectContainer(title2 = title)
    
    videos = JSON.ObjectFromURL(url, cacheTime = 60)

    if not videos['channels']:
        oc.header  = NO_PROGRAMS_FOUND_HEADER
        oc.message = SERVER_MESSAGE
        
        return oc
        
    for video in videos['channels']['TV4']['entries']:
        try:
            objects = TV4Videos(
                        showName   = video['title'],
                        showId     = String.Quote(video['program']['nid']),
                        art        = None,
                        episodeReq = True,
                        url        = GetVideoURL(str(video['vman_id']))
            )
            
            object = objects.objects[0]
            
            try:
                [date, time] = video['start_time'].split("T")
                time = time[:time.split("+")[0].rfind(":")]
                
                object.title = time + " " + object.title
                object.summary = date + " " + time + "\r\n\r\n" + object.summary
            except:
                pass
                
            oc.add(
                object
            )
        except:
            continue
        
    if len(oc) < 1:
        oc.header  = NO_PROGRAMS_FOUND_HEADER
        oc.message = NO_PROGRAMS_FOUND_MESSAGE

    return oc
   
####################################################################################################
@route(PREFIX + '/TV4PremiumRequired')
def TV4PremiumRequired():
    oc         = ObjectContainer()
    oc.header  = unicode("Premium krävs")
    oc.message = unicode("För att spela upp detta program krävs ett Premium abonnemang.\r\nwww.tv4play.se/premium")
    
    return oc 

####################################################################################################
@route(PREFIX + '/TV4Movies', offset = int)
def TV4Movies(offset = 0):
    oc = ObjectContainer(title2 = 'Filmer')
    
    movies = JSON.ObjectFromURL(MOVIES_URL % (offset, ITEMS_PER_PAGE))
    for movie in movies['results']:
        try:
            genres = (movie['genre'])
        except:
            genres = None
            
        try:
            duration = int(movie['length']) * 60 * 1000
        except:
            duration = None
            
        try:
            year = int(movie['production_year'])
        except:
            year = None
            
        try:
            art = movie['image']
        except:
            art = None
            
        try:
            thumb = movie['poster_image']
            if not thumb.startswith('http'):
                thumb = API_BASE_URL + '/play' + thumb
        except:
            thumb = None
            
        summary = movie['synopsis']
        if not summary:
            summary = movie['description_short']
        
        if not Prefs['premium']:
            oc.add(
                DirectoryObject(
                    key = Callback(TV4PremiumRequired),
                    title = movie['title'],
                    summary = summary,
                    duration = duration,
                    thumb = thumb,
                    art = art
                )
            )
        else:
            oc.add(
                MovieObject(
                    url = TEMPLATE_VIDEO_URL % ('film', movie['id'], movie['id']),
                    title = movie['title'],
                    summary = summary,
                    duration = duration,
                    original_title = movie['original_title'],
                    year = year,
                    thumb = thumb,
                    art = art
                )
            )

        
    if offset + ITEMS_PER_PAGE < movies['total_hits']:
        nextPage = (offset / ITEMS_PER_PAGE) + 2
        lastPage = (movies['total_hits'] / ITEMS_PER_PAGE) + 1
        oc.add(
            NextPageObject(
                key =
                    Callback(
                        TV4Movies,
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
@route(PREFIX + '/TV4Shows', offset = int)
def TV4Shows(categoryName, categoryId, offset = 0):
    oc = ObjectContainer(title2 = unicode(categoryName))

    oc = GetTV4Shows(oc, GetProgramsURL(category = String.Quote(categoryId)))
    oc.title2 = unicode(categoryName)
    
    totalNoShows = len(oc)
    
    try:
        oc.objects = oc.objects[offset:offset + ITEMS_PER_PAGE]
        
        if offset + ITEMS_PER_PAGE < totalNoShows:
            nextPage = (offset / ITEMS_PER_PAGE) + 2
            lastPage = (totalNoShows / ITEMS_PER_PAGE) + 1
            oc.add(
                NextPageObject(
                    key =
                        Callback(
                            TV4Shows,
                            categoryName = categoryName,
                            categoryId = categoryId,
                            offset = offset + ITEMS_PER_PAGE
                        ),
                    title = "Fler ...",
                    summary = "Vidare till sida " + str(nextPage) + " av " + str(lastPage)
                )
            )
    except:
        oc.objects = oc.objects[offset:]
        
    return oc
    
####################################################################################################
@route(PREFIX + '/TV4ShowChoice')
def TV4ShowChoice(showName, showId, art, thumb, summary):
    oc = ObjectContainer(title2 = unicode(showName))

    showId   = String.Quote(showId)
    episodes = JSON.ObjectFromURL(GetVideosURL(id = showId, episodes = True))
    clips    = JSON.ObjectFromURL(GetVideosURL(id = showId, episodes = False))

    if clips['total_hits'] > 0:
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

    if episodes['total_hits'] > 0:
        episodeoc = TV4Videos(showName, showId, art, True)
        
        for object in episodeoc.objects:
            oc.add(object)

    if len(oc) < 1:  
        oc.header  = NO_PROGRAMS_FOUND_HEADER
        oc.message = NO_PROGRAMS_FOUND_MESSAGE

    return oc

####################################################################################################
@route(PREFIX + '/TV4Videos', episodeReq = bool, offset = int)
def TV4Videos(showName, showId, art, episodeReq, offset = 0, query = None, url = None):
    showName = unicode(showName)

    oc = ObjectContainer(title2 = showName)

    orgShowName = showName
        
    if query:
        if episodeReq:
            videosURL = GetVideosURL(episodes = True, start = offset, rows = ITEMS_PER_PAGE, text = String.Quote(query))
        else:
            videosURL = GetVideosURL(episodes = False, start = offset, rows = ITEMS_PER_PAGE, text = String.Quote(query))
    elif url:
        videosURL = url
    elif episodeReq:
        videosURL = GetVideosURL(id = showId, episodes = True, start = offset, rows = ITEMS_PER_PAGE)
    else:
        videosURL = GetVideosURL(id = showId, episodes = False, start = offset, rows = ITEMS_PER_PAGE)            

    videos = JSON.ObjectFromURL(videosURL)
    # Add videos from JSON info
    for video in videos['results']:
        if 'is_drm_protected' in video:
            if video['is_drm_protected']:
                continue
        
        if 'drm_formats' in video:
            if len(video['drm_formats']) > 0:
                continue
            
        if query or (url and not showId):
            showName = unicode(video['category'])
            showId   = String.Quote(video['nid'])        

        url = TEMPLATE_VIDEO_URL % ('program', showId, str(video['vmanprogid']))

        try:
            publishdate = str(video['publishdate'])
            year        = publishdate[0:4]
            month       = publishdate[4:6]
            day         = publishdate[6:8]
            airdate     = Datetime.ParseDate(year + '-' + month + '-' + day)
        except:
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
            availabilty = "\r\n\r\n" + video['availability']['human']
        else:
            availabilty = ""

        if not video['premium'] or LoggedIn():
            if episodeReq:
                oc.add(
                    EpisodeObject(
                        url = url,
                        title = unicode(video['name']),
                        index = episode,
                        summary = unicode(description + " " + availabilty),
                        show = showName,
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
        elif not Prefs['onlyfree']:
            oc.add(
                DirectoryObject(
                    key = Callback(TV4PremiumRequired),
                    title = unicode(video['name']),
                    summary = unicode(description + " " + availabilty),
                    thumb = video['originalimage'],
                    art = art,
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
                        showName = orgShowName,
                        showId = showId,
                        art = art,
                        episodeReq = episodeReq,
                        offset = offset + ITEMS_PER_PAGE,
                        query = query
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
def GetTV4Shows(oc, url):
    try:
        programs = JSON.ObjectFromURL(url)
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
        oc.message = SERVER_MESSAGE

    return oc

####################################################################################################
@route(PREFIX + '/Search')
def Search(query, title):
    oc = ObjectContainer(title2 = unicode(title))

    programQueryURL = GetProgramsURL(name = String.Quote(query))
    episodeQueryURL = GetVideosURL(episodes = True, text = String.Quote(query))
    clipQueryURL    = GetVideosURL(episodes = False, text = String.Quote(query))
    
    programs = JSON.ObjectFromURL(programQueryURL)
    episodes = JSON.ObjectFromURL(episodeQueryURL)
    clips    = JSON.ObjectFromURL(clipQueryURL)

    typeHits = 0
    if len(programs) > 0:
        typeHits = typeHits+1
    if episodes['total_hits'] > 0:
        typeHits = typeHits+1
    if clips['total_hits'] > 0:
        typeHits = typeHits+1

    if typeHits == 0:
        oc.header = unicode("Sökresultat"),
        oc.message = unicode("Kunde ej hitta något för '%s'" % query)
    else:
        if episodes['total_hits'] > 0:
            oc = ReturnSearchHits(episodeQueryURL, query, oc, "Hela Program", True, typeHits > 1)
        if clips['total_hits'] > 0:
            oc = ReturnSearchHits(clipQueryURL, query, oc, "Klipp", False, typeHits > 1)
        if len(programs) > 0:
            oc = GetTV4Shows(oc, programQueryURL)

    return oc

####################################################################################################
@route(PREFIX + '/ReturnSearchHits', episodeReq = bool, createDirectory = bool)
def ReturnSearchHits(url, query, result, directoryTitle, episodeReq, createDirectory = False):
    if createDirectory:
        result.add(
            DirectoryObject(
                key =
                    Callback(
                        ReturnSearchHits,
                        url = url,
                        query = query,
                        result = None,
                        directoryTitle = directoryTitle,
                        episodeReq = True
                    ),
                title = directoryTitle
            )
        )
        return result
    else:
        return TV4Videos(
                showName   = unicode("Sök") + " - " + unicode(directoryTitle),
                showId     = None,
                art        = None,
                episodeReq = episodeReq,
                query      = query
        )

####################################################################################################
def GetImgURL(url):
    if '.jpg' in url:
        return url[url.rfind("http") : url.rfind(".jpg") + 4]
    elif '.png' in url:
        return url[url.rfind("http") : url.rfind(".png") + 4]
    else:
        return url[url.rfind("http") :]

