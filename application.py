import cgi
import os

from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

COLOR_LIST = ( "#0F4FA8", "#FFCA00", "#FF6200" )

class Schedule(db.Model):
    user = db.UserProperty()
    name = db.StringProperty()
    date = db.DateTimeProperty(auto_now_add=True)

class ScheduleItem(db.Model):
    schedule = db.ReferenceProperty(Schedule)
    name = db.StringProperty()
    time_weight = db.FloatProperty()
    ordinal = db.IntegerProperty()
    def get_color(self):
        return COLOR_LIST[self.ordinal % COLOR_LIST.length()]

class HomePage(webapp.RequestHandler):
    def get(self):
        template_values = {
            'schedules' : Schedule.all().run(),
            'is_loggedin' : users.get_current_user() is not None,
            'login_link' : users.create_login_url(self.request.uri),
            'logout_link' : users.create_logout_url(self.request.uri),
        }        
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

def GetSchedule(schedule_key):
    user = users.get_current_user()
    if not user:
        return None
    schedule = Schedule.get(db.Key(schedule_key))
    if schedule.user != user:
        return None
    return schedule

class ViewSchedule(webapp.RequestHandler):
#    @login_required
    def get(self, schedule_key):
        schedule = GetSchedule(schedule_key)
        if schedule is None:
            self.redirect('/')
            return
        items = schedule.scheduleitem_set
        template_values = {
            'schedule' : schedule,
            'items' : items,
        }        
        path = os.path.join(os.path.dirname(__file__), 'schedule.html')
        self.response.out.write(template.render(path, template_values))

class AddSchedule(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if not user:
            self.redirect('/')
            return            
        new_schedule = Schedule()
        new_schedule.user = user
        new_schedule.name = self.request.get('name')
        new_schedule.put()
        self.redirect('/schedule/' + str(new_schedule.key()))

class AddScheduleItem(webapp.RequestHandler):
    def post(self, schedule_key):
        schedule = GetSchedule(schedule_key)
        if schedule is None:
            self.redirect('/')
            return
        last_item = schedule.scheduleitem_set.order('ordinal').get()
        new_item = ScheduleItem()
        new_item.schedule = schedule
        new_item.name = self.request.get('name')
        new_item.time_weight = 1.0
        new_item.ordinal = 0 if last_item is None else last_item.ordinal + 1
        new_item.put()
        self.redirect('/schedule/' + str(schedule.key()))
        
class EditScheduleItem(webapp.RequestHandler):
    def get(self, schedule_key, item_key, action):
        item = ScheduleItem.get(db.Key(item_key))
        if item.schedule.user != users.get_current_user():
            self.redirect('/')
            return
        if action == 'more':
            item.time_weight *= 1.1
            item.put()
        elif action == 'less':
            item.time_weight *= .9
            item.put()
        elif action == 'remove':
            item.delete()
        else:
            raise Exception('Unknown mode')
        self.redirect('/schedule/' + str(item.schedule.key()))
        
application = webapp.WSGIApplication(
                                     [('/', HomePage),
                                      ('/add_schedule', AddSchedule),
                                      ('/schedule/(.*)/add', AddScheduleItem),
                                      ('/schedule/(.*)/(.*)/(more|less|remove)', EditScheduleItem),
                                      ('/schedule/(.*)', ViewSchedule)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()