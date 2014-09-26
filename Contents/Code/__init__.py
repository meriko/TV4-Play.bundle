from datetime import datetime

LoggedIn = SharedCodeService.tv4play.LoggedIn
Login    = SharedCodeService.tv4play.Login

TITLE  = 'TV4 Play'
PREFIX = '/video/tv4play'

BASE_URL = 'http://www.tv4play.se'

RE_VIDEO_ID = '(?<=video_id=)[0-9]+'

HTTP_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/536.26.17 (KHTML, like Gecko) Version/6.0.2 Safari/536.26.17"

API_BASE_URL   = 'http://webapi.tv4play.se/play/'
CATEGORIES_URL = API_BASE_URL + 'categories'
CHANNELS_URL   = API_BASE_URL + 'video_assets?platform=web&is_channel=true'
MOVIES_URL     = API_BASE_URL + 'movie_assets?platform=web&start=%s&rows=%s'

API_VIDEO_BASE_URL = 'http://premium.tv4play.se/api/web/asset/'
API_VIDEO_URL      = API_VIDEO_BASE_URL + '%s/play'

TEMPLATE_VIDEO_URL = 'http://www.tv4play.se/%s/%s?video_id=%s'

ITEMS_PER_PAGE = 25

DISCLAIMER_NOTE = unicode("Vissa program är skyddade med DRM(Digital Rights Management). Dessa kan för närvarande ej spelas upp.")
PREMIUM_PREVIEW_NOTE = unicode("Notera att du ej kan spela upp de program som endast är tillgängliga för Premium.")

NO_PROGRAMS_FOUND_HEADER  = "Inga program funna"
NO_PROGRAMS_FOUND_MESSAGE = unicode("Kunde inte hitta några program. ") + DISCLAIMER_NOTE
SERVER_MESSAGE            = unicode("Kunde ej få kontakt med TV4 servern")


####################################################################################################
def Start():
    # Set the default ObjectContainer attributes
    ObjectContainer.title1 = TITLE
    
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
    
    if Prefs['premium'] and Prefs['email'] and Prefs['password']:
        if Login():
            oc.header = "Inloggad"
            oc.message = unicode("Du är nu inloggad")
        else:
            oc.header = "Inloggningen misslyckades"
            oc.message = unicode("Felaktigt användarnamn eller lösenord?")
            return oc
            
    elif Prefs['premium']:
        oc.header = "Information saknas"
        oc.message = unicode("Användarnamn och/eller lösenord saknas.")
        return oc

    elif not Prefs['onlyfree']:
        oc.header = unicode("Alla program")
        oc.message = PREMIUM_PREVIEW_NOTE
    else:
        oc.header = "Gratis"
        oc.message = unicode("Visar endast program som är gratis.")
         
    oc.message = oc.message + ' ' + DISCLAIMER_NOTE + unicode(" Starta om för att inställningarna skall börja gälla.")
    
    return oc

###################################################################################################
def GetProgramsURL(category = ''):
    if category is None:
        category = ''

    url = API_BASE_URL + 'programs?per_page=1000&page=1&category=%s' % category
    
    if Prefs['onlyfree'] and not Prefs['premium']:
        url = url + '&is_premium=false'

    return url
    
###################################################################################################
def GetVideosURL(id, episodes, page = 1):
    url = API_BASE_URL + 'video_assets?is_live=false&page=%s&platform=web&node_nids=%s&per_page=%s' % (page, id, ITEMS_PER_PAGE)

    if episodes:
        url = url + '&type=episode'
    else:
        url = url + '&type=clip'
        
    if Prefs['onlyfree'] and not Prefs['premium']:
        url = url + '&is_premium=false'
        
    return url

####################################################################################################
@handler(PREFIX, TITLE)
def MainMenu():
    oc = ObjectContainer(no_cache = True)

    title = 'Alla program'
    oc.add(
        DirectoryObject(
            key = Callback(TV4Shows, title = title), 
            title = title
        )
    )

    oc_categories = TV4Categories()
    
    for object in oc_categories.objects:
        oc.add(object)

    oc.add(
        PrefsObject(
            title = unicode('Inställningar'),
            summary = unicode('Logga in för att använda Premium\r\n\r\nDu kan även välja att visa alla program för att se vad Premium innebär.\r\n\r\n' + DISCLAIMER_NOTE)
        )
    )

    return oc

####################################################################################################
@route(PREFIX + '/TV4Categories')
def TV4Categories():
    oc = ObjectContainer()

    categories = JSON.ObjectFromURL(CATEGORIES_URL)

    for category in categories:
        oc.add(
            DirectoryObject(
                key = Callback(TV4Shows, title = category["name"], categoryId = unicode(category["nid"])),
                title = unicode(category["name"])
            )
        )

    if Prefs['premium'] or not Prefs['onlyfree']:
        oc.add(
            DirectoryObject(
                key = Callback(TV4Movies),
                title = 'Filmer'
            )
        )

    oc.objects.sort(key=lambda obj: obj.title)
    return oc

####################################################################################################
@route(PREFIX + '/TV4Shows', offset = int)
def TV4Shows(title, categoryId = '', offset = 0):
    oc = ObjectContainer(title2 = unicode(title))
    
    programs = JSON.ObjectFromURL(GetProgramsURL(categoryId))

    for program in programs['results']:
        oc.add(
            DirectoryObject(
                key =
                    Callback(
                        TV4ShowChoice,
                        showName = program["name"],
                        showId = unicode(program["nid"]),
                        art = program["logo"] if 'logo' in program else None,
                        thumb = program["program_image"],
                        summary = program["description"]
                    ),
                title = unicode(program["name"]),
                summary = unicode(program["description"]),
                thumb = program["program_image"],
                art = program["logo"] if 'logo' in program else None
            )
        )

    if len(oc) < 1:
        oc.header  = NO_PROGRAMS_FOUND_HEADER
        oc.message = SERVER_MESSAGE
        
        return oc
    
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
                            title = title,
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

    showId = String.Quote(showId)
    
    episodes = JSON.ObjectFromURL(GetVideosURL(id = showId, episodes = True))
    clips    = JSON.ObjectFromURL(GetVideosURL(id = showId, episodes = False))

    if episodes['total_hits'] > 0 and clips['total_hits'] > 0:
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
        
        episode_oc = TV4Videos(
            showName = showName,
            showId = showId,
            art = art,
            episodeReq = True
        )
        
        for object in episode_oc.objects:
            oc.add(object)

    elif episodes['total_hits'] > 0 or clips['total_hits'] > 0:
        if clips['total_hits'] > 0:
            showName = showName + " - Klipp"
        
        return TV4Videos(
                showName = showName,
                showId = showId,
                art = art,
                episodeReq = episodes['total_hits'] > 0
        )

    if len(oc) < 1:  
        oc.header  = NO_PROGRAMS_FOUND_HEADER
        oc.message = NO_PROGRAMS_FOUND_MESSAGE

    return oc

####################################################################################################
@route(PREFIX + '/TV4Videos', episodeReq = bool, page = int)
def TV4Videos(showName, showId, art, episodeReq, page = 1):
    showName = unicode(showName)

    oc = ObjectContainer(title2 = showName)
    
    videos = JSON.ObjectFromURL(GetVideosURL(id = showId, episodes = episodeReq, page = page))
    
    for video in videos['results']:
        if 'is_drm_protected' in video:
            if video['is_drm_protected']:
                continue
                
        if Prefs['onlyfree'] and not Prefs['premium'] and video['availability']['availability_group_free'] == '0':
            continue
                
        url = TEMPLATE_VIDEO_URL % ('program', showId, str(video['id']))
        title = unicode(video['title'])
        summary = unicode(video['description'])
        thumb = video['image']
        art = video['program']['logo']
        duration = int(video['duration']) * 1000
        originally_available_at = Datetime.ParseDate(video['broadcast_date_time'].split('T')[0]).date()
        show = showName
        
        oc.add(
            EpisodeObject(
                url = url,
                title = title,
                summary = summary,
                thumb = thumb,
                art = art,
                duration = duration,
                originally_available_at = originally_available_at,
                show = show
            )
        )

    if len(oc) < 1:
        oc.header  = NO_PROGRAMS_FOUND_HEADER
        
        if page == 1:
            oc.message = NO_PROGRAMS_FOUND_MESSAGE
        else:
            oc.message = unicode('Inga fler program funna')
        
    elif len(oc) >= ITEMS_PER_PAGE:
        oc.add(
            NextPageObject(
                key =
                    Callback(
                        TV4Videos,
                        showName = showName,
                        showId = showId,
                        art = art,
                        episodeReq = episodeReq,
                        page = page + 1
                    ),
                title = "Fler ..."
            )
        )

    return oc

