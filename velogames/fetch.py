import urllib2
from StringIO import StringIO

from lxml import etree as et

BASE_URL = 'http://www.velogames.com/criterium-du-dauphine/2014/'
LEAGUE = 6162917

def update(application, firsttime=False):
    """ Update local data. """
    print("Running update")
    if not parse_league(LEAGUE, application.teams):
        return
    updates = parse_league(LEAGUE, application.teams, application.stage)
    new_stage = parse_league(LEAGUE, application.teams, application.stage+1)
    while new_stage:
        application.stage += 1
        if firsttime:
            new_stage = parse_league(LEAGUE, application.teams, application.stage+1)
        else:
            break
    print("Done")
    return updates or new_stage

def download(url):
    """ Download a url and return the parse tree's root.
    
    @param url  url to be downloaded
    returns lxml.etree._Element
    """
    req = urllib2.urlopen(BASE_URL + url)
    html = StringIO(req.read())
    parser = et.HTMLParser()
    tree = et.parse(html, parser)
    return tree.getroot()

class Team(list):
    name = 0
    directeur = 1
    global_rank = 2
    rank = 3
    score = 4
    link = 5
    tid = 6
    riders = 7
    stages = 16

class StageException(Exception):
    pass

def parse_league(league, teams, stage=None):
    """ Parse an etree and update team standings. """
    url = 'leaguescores.php?league={league}'.format(league=league)
    # add stage parameters
    url += '&ga=13&st={stage}'.format(stage=stage) if stage else ""

    try:
        root = download(url)
    except Exception as e:
        # unable to download
        return False

    updates = False
    rows = root.xpath('//table//tr')
    # no results
    if not rows:
        return False
    rows.pop(0) # remove header

    if stage:
        stage_index = Team.stages+3*stage-3

    # iterate over team members
    for row in rows:
        link = row[1][0].attrib['href']
        # Team id
        tid = link[19:] 
        team = filter(lambda x: x[Team.tid] == tid, teams)
        team = team.pop(0) if team else None
        score = int(row[4].text) #score

        # first time we see team
        if not team:
            if stage:
                raise StageException("Teams must be introduced in overall parse.")
            teams.append(Team((
                row[1][0].text, #team name
                row[2].text, #director,
                0, # global rank
                0, # rank
                score,
                BASE_URL + link, #team link
                tid, #team id
                0, 0, 0, 0, 0, 0, 0, 0, 0, # riders
            )))
            updates = True
        # overall
        elif not stage:
            updates = updates or (team[Team.score] != score)
            team[Team.score] = score
        else:
            # add new slots for stage results
            if len(team) <= stage_index:
                team.extend((0,0,0))
            updates = updates or (team[stage_index] != score)
            team[stage_index] = score
            team[stage_index+1] = parse_team(team[Team.tid])

    # no changes, nothing to do
    if not updates:
        return False

    # Calculate rankings
    if not stage:
        teams.sort(key=lambda x: x[Team.score], reverse=True)
        rank = 0
        score = -1
        for team in teams:
            # update league rank (different from shown rank due to
            # equal points ranking)
            if team[Team.score] != score:
                score = team[Team.score]
                rank += 1
            team[Team.rank] = rank
            team[Team.global_rank] = parse_team(team[Team.tid])

    else:
        # sort by stage results
        stage_results = sorted(teams, key=lambda x: x[stage_index], reverse=True)
        rank = 0
        score = -1
        for team in stage_results:
            if team[stage_index] != score:
                score = team[stage_index]
                rank += 1
            team[stage_index+2] = rank

    return True

def parse_team(team, stage=None):
    # div.col-md-6:nth-child(2) > table:nth-child(1) > tbody:nth-child(1) > tr:nth-child(2) > td:nth-child(2)
    pass
        
