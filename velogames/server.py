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

class Application(tornado.web.Application):
    def __init__(self, **settings):
        self.stage = 0
        handlers = [
            (r'/league/(?P<method>daily|cumulative)/(?P<var>points|league|overall)', LeagueHandler),
        ]
        tornado.web.Application.__init__(self, handlers, **settings)

        # fetch data at interval
        main_loop = tornado.ioloop.IOLoop.instance()
        callback = partial(update, self)
        # Set updates to run every 22 minutes.
        scheduler = tornado.ioloop.PeriodicCallback(callback, 1000*60*22, io_loop=main_loop)
        scheduler.start()
        # Initialize data
        self.teams = get_teams(LEAGUE)
        update(self)


class LeagueHandler(tornado.web.RequestHandler):
    """ Handler for league scores. """

    def get(self, method, var):
        """ Write home page. """
        print application.teams

        header = '"Team Name",Directeur,tid,'
        for day in range(application.stage):
            header += "day {day}".format(day=day+1)

        # no udpates yet
        if not application.stage:
            self.write(header+"\n")
            return

        rows = []
        for team in application.teams:
            pass

        csv = "\n".join(
            map(lambda row: ",".join(
                map(lambda x: str(x).replace('"', '""'), row)),
                rows))
        self.write(csv+"\n")
        self.set_header("Content-Type", 'text/csv; charset="utf-8"')


application = Application()

if __name__ == "__main__":
    application.listen(8080)
    tornado.ioloop.IOLoop.instance().start()
