import pickle

from functools import partial

import tornado
from tornado.web import HTTPError
from tornado import ioloop

from fetch import (
    update,
    get_teams,
)

LEAGUE = 6162917

def update_cache(application, *args, **kwargs):
    ret = update(application, *args, **kwargs)
    try:
        with open("team_cache.pickle", "wb") as tc:
            pickle.dump((application.teams, application.teams[0].stage), tc)
    except Exception as e:
        pass
    

class Application(tornado.web.Application):
    def __init__(self, **settings):
        self.stage = 0
        handlers = [
            (r'/league/(?P<method>daily|cumulative)/(?P<var>points|league|overall)', LeagueHandler),
            (r'/league/status', StatusHandler)
        ]
        tornado.web.Application.__init__(self, handlers, **settings)

        # fetch data at interval
        main_loop = tornado.ioloop.IOLoop.instance()
        callback = partial(update_cache, self)
        # Set updates to run every 22 minutes.
        scheduler = tornado.ioloop.PeriodicCallback(callback, 1000*60*22, io_loop=main_loop)
        scheduler.start()
        # Initialize data
        try:
            with open("team_cache.pickle", "rb") as tc:
                self.teams, self.stage = pickle.load(tc)
        except Exception as e:
            self.teams = get_teams(LEAGUE)
            try:
                with open("team_cache.pickle", "wb") as tc:
                    pickle.dump((self.teams, 0), tc)
            except Exception as e:
                pass

        update_cache(self)

def escape_csv(input):
    input = str(input)
    if '"' in input:
        input = '"' + input.replace('"', '""') + '"'
    if ',' in input:
        input = '"' + input + '"'
    return input

class LeagueHandler(tornado.web.RequestHandler):
    """ Handler for league scores. """
    def get(self, method, var):
        """ Write csvs with data from league. """
        mapping = {
            "daily": "dy",
            "cumulative": "cu",
            "points": "pts",
            "league": "lg",
            "overall": "ov",
        }

        header = '"Team ID","Team Name",Directeur,'
        for day in range(application.stage):
            header += "Day {day},".format(day=day+1)

        self.write(header+"\n")

        # no udpates yet
        if not application.stage:
            return

        attr = mapping[method] + "_" + mapping[var]

        rows = []
        for team in application.teams:
            rows.append([team.tid, team.name, team.directeur] + \
                  getattr(team, attr))

        csv = "\n".join(
            map(lambda row: ",".join(
                map(lambda x: escape_csv(x), row)),
                rows))

        self.write(csv+"\n")
        self.set_header("Content-Type", 'text/csv; charset="utf-8"')

class StatusHandler(tornado.web.RequestHandler):
    """ Print for stage results. """
    def get(self):
        """ Get latest results. """
        self.write("Results after stage {stage}<br />\n".format(stage=application.stage))
        for row in application.teams:
            self.write(" ".join((row.name, row.directeur, str(row.cu_pts[-1]))) + "</br>\n")


application = Application()

if __name__ == "__main__":
    application.listen(8080)
    tornado.ioloop.IOLoop.instance().start()
