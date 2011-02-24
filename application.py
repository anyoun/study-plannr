import cgi
import os

from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

class Schedule(db.Model):
    user = db.UserProperty()
    name = db.StringProperty()
    date = db.DateTimeProperty(auto_now_add=True)

class ScheduleItem(db.Model):
    schedule = db.ReferenceProperty(Schedule)
    name = db.StringProperty()
    time_weight = db.FloatProperty()
    ordinal = db.IntegerProperty()

class HomePage(webapp.RequestHandler):
    def get(self):
        schedules = Schedule.all()
        
        template_values = {
            'schedules' : schedules,
            'is_loggedin' : users.get_current_user() is not None,
            'login_link' : users.create_login_url(self.request.uri),
            'logout_link' : users.create_logout_url(self.request.uri),
        }
        
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

class AddSchedule(webapp.RequestHandler):
    def post(self):
        if not users.get_current_user():
            self.redirect('/')
            return
            
        new_schedule = Schedule()
        new_schedule.user = users.get_current_user()
        new_schedule.name = self.request.get('name')
        new_schedule.put()
        self.redirect('/schedule/' + str(new_schedule.key()))
        
class ViewSchedule(webapp.RequestHandler):
    def get(self, schedule_key):
        schedule = Schedule.get(db.Key(schedule_key))
        if schedule.user != users.get_current_user():
            self.redirect('/')
            return
            
        items = schedule.scheduleitem_set
        
        template_values = {
            'schedule' : schedule,
            'items' : items,
        }
        
        path = os.path.join(os.path.dirname(__file__), 'schedule.html')
        self.response.out.write(template.render(path, template_values))


application = webapp.WSGIApplication(
                                     [('/', HomePage),
                                      ('/add_schedule', AddSchedule),
                                      ('/schedule/(.*)', ViewSchedule)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()