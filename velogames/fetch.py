import urllib2
from StringIO import StringIO
from collections import namedtuple

from lxml import etree as et

BASE_URL = 'http://www.velogames.com/vuelta-a-espana/2014/'

def update(application):
    """ Update local data. """
    stage = application.stage + 1
    print("Checking stage {stage}".format(stage=stage))
    while is_scored(stage) and parse_teams(application.teams, stage):
        print("Updated stage {stage}".format(stage=stage))
        application.stage = stage
        stage += 1
    print("Done")

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

class Team:
    def __init__(self, tid, name, directeur, riders, dy_pts,
                 dy_lg, dy_ov, cu_pts, cu_lg, cu_ov, stage):
        self.tid = tid
        self.name = name
        self.directeur = directeur
        self.riders = riders
        self.dy_pts = dy_pts
        self.dy_lg = dy_lg
        self.dy_ov = dy_ov
        self.cu_pts = cu_pts
        self.cu_lg = cu_lg
        self.cu_ov = cu_ov
        self.stage = stage

    def __repr__(self):
        return str((self.tid,
               self.name,
               self.directeur,
               self.riders,
               self.dy_pts,
               self.dy_lg,
               self.dy_ov,
               self.cu_pts,
               self.cu_lg,
               self.cu_ov,
               self.stage,
           ))


def get_teams(league):
    """ Get list of teams in a league. """
    url = 'leaguescores.php?league={league}'.format(league=league)
    root = download(url)
    rows = root.xpath("//table//tr")[1:]
    teams = []
    for row in rows:
        a = row.xpath("./td[1]/a")[0]
        tid =  a.attrib['href'][19:]
        team = Team(
            tid, #team id
            row[1][0].text, #team name
            row[2].text, #directeur,
            None, # rider ids
            [], # daily points,
            [], # daily league position,
            [], # daily overall position,
            [], # cumulative points
            [], # cumulative league position
            [], # cumulative overall position
            0)
        teams.append(team)
    return teams

def is_scored(stage):
    """ Check whether stage has been scored yet. """
    try:
        root = download('teamscore.php?ga=13&st={stage}'.format(stage=stage))
        cell = int(root.xpath("//table//tr[2]/td[last()]").pop().text)
    except Exception as e:
        return False
    return cell > 0

def parse_teams(teams, stage):
    """ Update each team and calculate team rankings. """
    # iterate over team members
    for team in teams:
        tid = team.tid

        try:
            riders, dy_pts, cu_pts, dy_ov, cu_ov = parse_team(team.tid, stage)
        except Exception as e:
            return False
        
        # @TODO quick hack because I missed the first stage
        if stage == 1:
            cu_pts, cu_ov = dy_pts, dy_ov

        team.riders = riders
        # adding new values
        if team.stage < stage:
            team.stage = stage
            team.dy_pts.append(dy_pts)
            team.cu_pts.append(cu_pts)
            team.dy_lg.append(0)
            team.cu_lg.append(0)
            team.dy_ov.append(dy_ov)
            team.cu_ov.append(cu_ov)
        # updating values
        else:
            team.dy_pts[stage-1] = dy_pts
            team.cu_pts[stage-1] = cu_pts
            team.dy_ov[stage-1] = dy_ov
            team.cu_ov[stage-1] = cu_ov

    # Calculate daily league standings
    teams.sort(key=lambda x: x.dy_pts[stage-1], reverse=True)
    rank = count = 0
    score = -1
    for team in teams:
        # update league rank (different from shown rank due to
        # equal points ranking)
        count += 1
        if team.dy_pts[stage-1] != score:
            score = team.dy_pts[stage-1]
            rank = count
        team.dy_lg[stage-1] = rank

    # Calculate cumulative league standings
    teams.sort(key=lambda x: x.cu_pts[stage-1], reverse=True)
    rank = count = 0
    score = -1
    for team in teams:
        # update league rank (different from shown rank due to
        # equal points ranking)
        count += 1
        if team.cu_pts[stage-1] != score:
            score = team.cu_pts[stage-1]
            rank = count
        team.cu_lg[stage-1] = rank

    return True


def parse_team(team, stage):
    root = download("teamroster.php?tid={team}&ga=13&st={stage}".format(team=team, stage=stage))


    try:
        # Extract info from page (top right table with scores)
        info_cells = root.xpath("//div[@id='home_post_cont']//div[@class='cat-posts-trending']//div[@class='cat_post_inner']/div[position()>4]/div[position()=2]//a")
        cu_points, cu_overall, dy_points, dy_overall = map(lambda cell: int(cell.text), info_cells)

        rider_urls = root.xpath("//table[position()=1]//a")
        riders = tuple(map(lambda a: a.attrib['href'][-8:], rider_urls))

        return (
            riders,
            dy_points,
            cu_points,
            dy_overall,
            cu_overall,
        )
    except:
        return (
            tuple([0]*9),
            0,
            0,
            0,
            0,
            0
        )

