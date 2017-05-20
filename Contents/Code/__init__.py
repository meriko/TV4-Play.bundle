LoggedIn = SharedCodeService.tv4play.LoggedIn
Login    = SharedCodeService.tv4play.Login

TITLE  = 'TV4 Play'
PREFIX = '/video/tv4play'

BASE_URL = 'http://www.tv4play.se'

RE_VIDEO_ID = '(?<=video_id=)[0-9]+'

HTTP_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/536.26.17 (KHTML, like Gecko) Version/6.0.2 Safari/536.26.17"

API_BASE_URL   = 'http://webapi.tv4play.se'
CATEGORIES_URL = API_BASE_URL + '/play/categories'
MOVIES_URL     = API_BASE_URL + '/play/movie_assets?platform=web&start=%s&rows=%s'

TEMPLATE_VIDEO_URL = 'http://www.tv4play.se/%s/%s?video_id=%s'

ITEMS_PER_PAGE = 25

DISCLAIMER_NOTE = unicode("Vissa program är skyddade med DRM(Digital Rights Management). Dessa kan för närvarande ej spelas upp.")
PREMIUM_PREVIEW_NOTE = unicode("Notera att du ej kan spela upp de program som endast är tillgängliga för Premium.")

NO_PROGRAMS_FOUND_HEADER  = "Inga program funna"
NO_PROGRAMS_FOUND_MESSAGE = unicode("Kunde inte hitta några program. ") + DISCLAIMER_NOTE
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

RE_TIME = Regex('([0-9]+:[0-9]+)')

####################################################################################################
def Start():
    # Set the default ObjectContainer attributes
    ObjectContainer.title1 = TITLE
    
    # Set the default cache time
    HTTP.CacheTime             = 300
    HTTP.Headers['User-agent'] = HTTP_USER_AGENT

###################################################################################################
def ValidatePrefs():
    pass

####################################################################################################
@handler(PREFIX, TITLE)
def MainMenu():
    oc = ObjectContainer(no_cache = True)

    title = 'Mest sedda programmen'
    oc.add(
        DirectoryObject(
            key = Callback(TV4MostWatched, title = title),
            title = title
        )
    )
    
    title = 'Senaste veckans TV'
    oc.add(
        DirectoryObject(
            key = Callback(TV4Catchup, title = title),
            title = title
        )
    )

    title = unicode('Livesändningar')
    oc.add(
        DirectoryObject(
            key = Callback(TV4Live, title = title),
            title = title
        )
    )

    title = 'Kategorier'
    oc.add(
        DirectoryObject(
            key = Callback(TV4Categories, title = title),
            title = title
        )
    )
        
    title = 'Alla program'
    oc.add(
        DirectoryObject(
            key = Callback(TV4Shows, title = title), 
            title = title
        )
    )

    title = unicode('Sök')
    oc.add(
        InputDirectoryObject(
            key = Callback(Search, title = title),
            title  = title,
            prompt = title
        )
    )    

    return oc

###################################################################################################
@route(PREFIX + '/TV4MostWatched', episodes = bool)
def TV4MostWatched(title, episodes = True):
    oc = ObjectContainer(title2 = unicode(title))

    if episodes:
        oc.add(
            DirectoryObject(
                key =
                    Callback(
                        TV4MostWatched,
                        title      = title + " - Klipp",
                        episodes   = False
                    ),
                title = "Klipp"
            )
        )
    
    videos = JSON.ObjectFromURL(GetMostWatchedURL(episodes = episodes))
    oc = Videos(oc, videos)
    
    if len(oc) < 1:
        oc.header  = NO_PROGRAMS_FOUND_HEADER
        oc.message = NO_PROGRAMS_FOUND_MESSAGE
        
    return oc
    
####################################################################################################
@route(PREFIX + '/TV4Catchup')
def TV4Catchup(title):
    oc = ObjectContainer(title2 = unicode(title))

    now = Datetime.Now()
    for i in range (0, 7):
        startDate = now - Datetime.Delta(days = i)
        if i == 0:
            title = unicode('Idag')
        elif i == 1:
            title = unicode('Igår')
        else:
            title = DAYS[startDate.weekday()]

        endDate = dateToString(startDate + Datetime.Delta(days = 1))
        startDate = dateToString(startDate)
        oc.add(
            DirectoryObject(
                key = Callback(TV4ListingVideos, startDate = startDate, endDate = endDate),
                title = title
            )
        )
    
    return oc 

def dateToString(date):
    month = str(date.month)
    if len(month) <= 1:
        month = '0' + month
        
    day = str(date.day)
    if len(day) <= 1:
        day = '0' + day
            
    return '%s-%s-%s' % (date.year, month, day)

####################################################################################################
@route(PREFIX + '/TV4ListingVideos', startDate = str, endDate = str, episodeReq = bool, page = int)
def TV4ListingVideos(startDate, endDate, episodeReq = True, page = 1):
    title = startDate
    if not episodeReq:
        title = title + " - Klipp"
    url = GetListingsURL(startDate, endDate, episodeReq, page)

    oc = ObjectContainer(title2 = unicode(title))

    if episodeReq and page == 1:
        oc.add(
            DirectoryObject(
                key =
                    Callback(
                        TV4ListingVideos, 
                        startDate  = startDate,
                        endDate    = endDate,
                        episodeReq = False,
                        page       = 1
                    ),
                title = "Klipp"
                )
            )
    
    videos = JSON.ObjectFromURL(url)

    oc = Videos(oc, videos)

    if len(oc) < 1:
        oc.header  = NO_PROGRAMS_FOUND_HEADER
        oc.message = NO_PROGRAMS_FOUND_MESSAGE

    elif len(oc) >= ITEMS_PER_PAGE:
        oc.add(
            NextPageObject(
                key =
                    Callback(
                        TV4ListingVideos, 
                        startDate  = startDate,
                        endDate    = endDate,
                        episodeReq = episodeReq,
                        page       = page + 1
                    ),
                title = "Fler ..."
            )
        )

    return oc

####################################################################################################
@route(PREFIX + '/TV4Live')
def TV4Live(title):
    oc = ObjectContainer(title2 = unicode(title))
    
    tomorrow = Datetime.Now() + Datetime.Delta(days = 2) # Must set 2 due to a bug in TV4 server?
    end_date = "%04i%02i%02i" % (tomorrow.year, tomorrow.month, tomorrow.day)

    # Fetch all broadcasts up till tomorrow
    videos = JSON.ObjectFromURL(GetLiveURL(end_date), cacheTime = 0)
    oc = Videos(oc, videos)
    
    if len(oc) < 1:
        oc.header  = NO_PROGRAMS_FOUND_HEADER
        oc.message = unicode('Inga livesändningar tillgängliga för tillfället')

    return oc

####################################################################################################
@route(PREFIX + '/TV4Categories')
def TV4Categories(title):
    oc = ObjectContainer(title2 = unicode(title))

    categories = JSON.ObjectFromURL(CATEGORIES_URL)

    for category in categories:
        oc.add(
            DirectoryObject(
                key = Callback(TV4Shows, title = category["name"], categoryId = unicode(category["nid"])),
                title = unicode(category["name"])
            )
        )

    title = 'Filmer'
    oc.add(
        DirectoryObject(
            key = Callback(TV4Movies, title = title),
            title = title
        )
    )

    oc.objects.sort(key=lambda obj: obj.title)
    
    return oc

####################################################################################################
@route(PREFIX + '/TV4Shows', query = list, page = int)
def TV4Shows(title, categoryId = '', query = '', page = 1):
    oc = ObjectContainer(title2 = unicode(title))
    
    programs = JSON.ObjectFromURL(GetProgramsURL(page, categoryId, query))
    oc = Programs(oc, programs)

    if len(oc) < 1:
        oc.header  = NO_PROGRAMS_FOUND_HEADER
        oc.message = SERVER_MESSAGE
        
        return oc

    elif len(oc) >= ITEMS_PER_PAGE:
        oc.add(
            NextPageObject(
                key =
                    Callback(
                        TV4Shows,
                        title = title,
                        categoryId = categoryId,
                        query = query,
                        page = page + 1
                    ),
                title = "Fler ..."
            )
        )
        
    return oc
    
####################################################################################################
@route(PREFIX + '/TV4ShowChoice')
def TV4ShowChoice(title, showId, art, thumb, summary):
    title = unicode(title)
    oc = ObjectContainer(title2 = title)
    showId = String.Quote(showId)
    
    episodes = JSON.ObjectFromURL(GetShowVideosURL(episodes = True, id = showId))
    clips    = JSON.ObjectFromURL(GetShowVideosURL(episodes = False, id = showId))

    if episodes['total_hits'] > 0 and clips['total_hits'] > 0:
        oc.add(
            DirectoryObject(
                key =
                    Callback(
                        TV4ShowVideos, 
                        title = title, 
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
        
        episode_oc = TV4ShowVideos(
            title = title,
            showId = showId,
            art = art,
            episodeReq = True
        )
        
        for object in episode_oc.objects:
            oc.add(object)

    elif episodes['total_hits'] > 0 or clips['total_hits'] > 0:
        if clips['total_hits'] > 0:
            title = title + " - Klipp"
        
        return TV4ShowVideos(
                title = title,
                showId = showId,
                art = art,
                episodeReq = episodes['total_hits'] > 0
        )

    if len(oc) < 1:  
        oc.header  = NO_PROGRAMS_FOUND_HEADER
        oc.message = NO_PROGRAMS_FOUND_MESSAGE

    return oc

####################################################################################################
@route(PREFIX + '/TV4ShowVideos', episodeReq = bool, query = list, page = int)
def TV4ShowVideos(title, showId, art, episodeReq, query = '', page = 1):
    oc = ObjectContainer(title2 = unicode(title))
    
    videos = JSON.ObjectFromURL(GetShowVideosURL(episodes = episodeReq, id = showId, query = query, page = page))
    oc = Videos(oc, videos)
    
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
                        TV4ShowVideos,
                        title = title,
                        showId = showId,
                        art = art,
                        episodeReq = episodeReq,
                        query = query,
                        page = page + 1
                    ),
                title = "Fler ..."
            )
        )

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
def TV4Movies(title, offset = 0):
    oc = ObjectContainer(title2 = unicode(title))
    
    totalNoMovies = JSON.ObjectFromURL(MOVIES_URL % (0, 0))['total_hits']
    moviesLeft = totalNoMovies - offset
    maxPages = moviesLeft // ITEMS_PER_PAGE

    if moviesLeft % ITEMS_PER_PAGE != 0:
        maxPages = maxPages + 1

    for page in range(maxPages):
        movies = JSON.ObjectFromURL(MOVIES_URL % (offset, ITEMS_PER_PAGE))
        
        for movie in movies['results']:
            if 'is_drm_protected' in movie:
                if movie['is_drm_protected']:
                    continue
            
            try:
                genres = [movie['genre']] if movie['genre'] else []
            except:
                genres = []

            try:
                for sub in movie['sub_genres']:
                    genres.append(sub)
            except:
                pass

            try:
                duration = int(movie['length']) * 60 * 1000
            except:
                duration = None

            try:
                year = int(movie['production_year'])
            except:
                year = None

            try:
                directors = [movie['director']] if movie['director'] else []
            except:
                directors = []

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

            source_title = movie['content_source']

            countries = []
            if 'production_countries' in movie and movie['production_countries']:
                for country in movie['production_countries']:
                    countries.append(country)

            oc.add(
                MovieObject(
                    url = TEMPLATE_VIDEO_URL % ('film', movie['id'], movie['id']),
                    title = movie['title'],
                    genres = genres,
                    summary = summary,
                    duration = duration,
                    original_title = movie['original_title'],
                    year = year,
                    directors = directors,
                    thumb = thumb,
                    art = art,
                    source_title = source_title,
                    countries = countries
                )
            )

            if len(oc) >= ITEMS_PER_PAGE:
                break

        offset = offset + ITEMS_PER_PAGE

        if len(oc) >= ITEMS_PER_PAGE:
            oc.add(
                NextPageObject(
                    key =
                        Callback(
                            TV4Movies,
                            offset = offset
                        ),
                    title = "Fler ...",
                    art = art
                )
            )
            break

    if len(oc) < 1:
        oc.header  = NO_PROGRAMS_FOUND_HEADER
        oc.message = NO_PROGRAMS_FOUND_MESSAGE

    return oc

####################################################################################################
@route(PREFIX + '/Search')
def Search(query, title):
    oc = ObjectContainer(title1=TITLE, title2=unicode(title + " '%s'" % query))

    unquotedQuery = query
    query = String.Quote(query)
    
    for episodeReq in [False, True]:
        videos_oc = TV4ShowVideos(
            title = unicode(title),
            showId = '',
            art = None,
            episodeReq = episodeReq,
            query = query
        )
        
        if len(videos_oc) > 0:
            if episodeReq:
                title = 'Hela avsnitt'
            else:
                title = 'Klipp'

            hits = JSON.ObjectFromURL(GetShowVideosURL(episodes = episodeReq, query = query))
            title = title + "(%i)" % hits['total_hits']

            oc.add(
                DirectoryObject(
                    key = 
                        Callback(
                            TV4ShowVideos,
                            title = title,
                            showId = '',
                            art = None,
                            episodeReq = episodeReq,
                            query = query
                        ),
                    title = title
                )
            )

    programs_oc = TV4Shows(title = unicode(title), query = query)

    for object in programs_oc.objects:
        oc.add(object)

    if len(oc) < 1:
        oc.header  = unicode("Sökresultat")
        oc.message = unicode("Kunde ej hitta något för '%s'" % unquotedQuery)
        
    return oc

####################################################################################################
def Videos(oc, videos):
    for video in videos['results']:
        if 'is_drm_protected' in video:
            if video['is_drm_protected']:
                continue
        
        video_is_premium_only = video['availability']['availability_group_free'] == '0' or not video['availability']['availability_group_free']
        
        if video_is_premium_only:
            continue
                
        url = TEMPLATE_VIDEO_URL % ('program', String.Quote(video['program_nid']), str(video['id']))
        title = unicode(video['title'])
        summary = unicode(video['description'])
        thumb = video['image']
        art = video['program']['logo'] if 'logo' in video['program'] else None
        duration = int(video['duration']) * 1000
        originally_available_at = Datetime.ParseDate(video['broadcast_date_time'].split('T')[0]).date()
        show = unicode(video['program']['name'])

        if video['is_live']:
            if originally_available_at > Datetime.Now().date():
                tomorrow = (Datetime.Now() + Datetime.Delta(days = 1)).date()

                if originally_available_at == tomorrow:
                    title = 'Imorgon: ' + title
                else:
                    title = '%s: ' % originally_available_at + title
            else:
                title = '%s ' % (RE_TIME.search(video['broadcast_date_time']).groups()[0]) + title
        
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

    return oc

###################################################################################################
def Programs(oc, programs):
    for program in programs['results']:
        oc.add(
            DirectoryObject(
                key =
                    Callback(
                        TV4ShowChoice,
                        title = program["name"],
                        showId = unicode(program["nid"]),
                        art = program["logo"] if 'logo' in program else None,
                        thumb = program["program_image"] if 'program_image' in program else None,
                        summary = program["description"]
                    ),
                title = unicode(program["name"]),
                summary = unicode(program["description"]),
                thumb = program["program_image"] if 'program_image' in program else None,
                art = program["logo"] if 'logo' in program else None
            )
        )
    
    return oc

###################################################################################################
def GetProgramsURL(page, category = '', query = ''):
    if category is None:
        category = ''

    url = API_BASE_URL + '/play/programs?per_page=%s&page=%s&category=%s' % (ITEMS_PER_PAGE, page, String.Quote(category))
    
    if query:
        url = url + '&q=%s' % query
    
    url = url + '&is_premium=false'

    return url
    
###################################################################################################
def GetShowVideosURL(episodes, id = '', query = '', page = 1):
    if id is None:
        id = ''
    
    url = API_BASE_URL + '/play/video_assets?is_live=false&page=%s&platform=web&node_nids=%s&per_page=%s' % (page, id, ITEMS_PER_PAGE)
    
    if query:
        url = url + '&q=%s' % query

    if episodes:
        url = url + '&type=episode'
    else:
        url = url + '&type=clip'
        
    url = url + '&is_premium=false'
        
    return url

###################################################################################################
def GetMostWatchedURL(episodes = True):
    url = API_BASE_URL + '/play/video_assets/most_viewed?page=1&is_live=false&sort=broadcast_date_time&platform=web&per_page=%s&sort_order=desc' % ITEMS_PER_PAGE
 
    if episodes:
        url = url + '&type=episode'
    else:
        url = url + '&type=clip'
    
    url = url + '&is_premium=false'
        
    return url
    
###################################################################################################
def GetListingsURL(startDate, endDate, episodeReq, page):

    typeReq = "episode" if episodeReq else "clip"

    url = API_BASE_URL + '/play/video_assets?is_live=false&platform=web&sort=broadcast_date_time&sort_order=desc&page=%s&per_page=%s&type=%s&broadcast_from=%s&broadcast_to=%s' % (page, ITEMS_PER_PAGE, typeReq, startDate.replace("-", ""), endDate.replace("-", ""))
    url = url + '&is_premium=false'
        
    return url
    
###################################################################################################
def GetVideosURL(vman_ids):
    url = API_BASE_URL + '/play/video_assets?id=%s' % vman_ids
    url = url + '&is_premium=false'
        
    return url

###################################################################################################
def GetLiveURL(end_date = 'NOW'):
    # Note: The hardcoded start date, 19991231 -> We don't have to worry about day shift(s).
    #       Also, there exists a broadcast started in 2011 which broadcasts the latest news
    #       via rolling texts
    url = API_BASE_URL + '/play/video_assets?broadcast_to=%s&broadcast_from=19991231&is_live=true&platform=web&per_page=%s' % (end_date, ITEMS_PER_PAGE)
    
    return url

