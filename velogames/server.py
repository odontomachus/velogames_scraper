from functools import partial

import tornado
from tornado.web import HTTPError
from tornado import ioloop

from fetch import update


class Application(tornado.web.Application):
    def __init__(self, **settings):
        self.teams = []
        self.stage = 1
        handlers = [
            (r'/league', LeagueHandler),
        ]
        tornado.web.Application.__init__(self, handlers, **settings)

        # fetch data at interval
        main_loop = tornado.ioloop.IOLoop.instance()
        callback = partial(update, self)
        scheduler = tornado.ioloop.PeriodicCallback(callback, 1000*60*2, io_loop=main_loop)
        scheduler.start()
        # Initialize data
        update(self)


class LeagueHandler(tornado.web.RequestHandler):
    """ Handler for league scores. """
    def get(self):
        """ Write home page. """
        header = '"Team Name",Directeur,"Overall rank","League rank",'\
                 + 'Points,url,tid,'\
                 + '"Rider 1","Rider 2","Rider 3","Rider 4","Rider 5","Rider 6","Rider 7","Rider 8","Rider 9",' \
                 + "".join(['"Stage {stage} points","Stage {stage} overall rank","Stage {stage} league rank",'.format(stage=stage) for stage in range(1, application.stage+1)])
        self.write(header+"\n")

        csv = "\n".join(
            map(lambda row: ",".join(
                map(lambda x: str(x).replace('"', '""'), row[:-3])),
                application.teams))
        self.write(csv+"\n")
        self.set_header("Content-Type", 'text/csv; charset="utf-8"')


application = Application()

if __name__ == "__main__":
    application.listen(8080)
    tornado.ioloop.IOLoop.instance().start()
