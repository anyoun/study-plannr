import cgi
import os
import logging
import re

from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from time import sleep
from datetime import time

class Schedule(db.Model):
    user = db.UserProperty()
    name = db.StringProperty()
    date = db.DateTimeProperty(auto_now_add=True)

class ScheduleItem(db.Model):
    schedule = db.ReferenceProperty(Schedule)
    name = db.StringProperty()
    time_weight = db.FloatProperty()
    ordinal = db.IntegerProperty()
     
#COLOR_LIST = [ '#0F4FA8', '#FFCA00', '#FF6200' ]
COLOR_LIST = ['rgb(228,26,28)', 'rgb(55,126,184)', 'rgb(77,175,74)', 'rgb(152,78,163)', 'rgb(255,127,0)', 'rgb(255,255,51)', 'rgb(166,86,40)', 'rgb(247,129,191)', 'rgb(153,153,153)']
class CalculatedScheduleItem:
    def __init__(self, scheduleItem):
        self.key = scheduleItem.key
        self.name = scheduleItem.name
        self.ordinal = scheduleItem.ordinal
    def get_color(self):
        return COLOR_LIST[self.ordinal % len(COLOR_LIST)]

def time_diff(x, y):
    return 3600*(x.hour-y.hour) + 60*(x.minute-y.minute) + x.second-y.second
def add_time(t, delta_seconds):
    total_seconds = time_diff(t, time(0)) + delta_seconds
    td_hours = total_seconds // 3600
    td_minutes = (total_seconds // 60) % 60
    td_seconds = total_seconds % 60
    logging.info("Seconds: %s", total_seconds)
    logging.info("%s %s %s", td_hours,td_minutes,td_seconds)
    return time(td_hours, td_minutes, td_seconds)
def multi_duration(td, factor):
    return td * factor
    #total = td.seconds + td.days * 24 * 3600
    #return timedelta(seconds = total * factor)
def round_time_15min(t):
    if t.minute > 53:
        return time(t.hour + 1, 0, 0)
    elif t.minute > 37:
        return time(t.hour, 30, 0)
    elif t.minute > 7:
        return time(t.hour, 15, 0)
    else:
        return time(t.hour, 0, 0)
def round_time_5min(t):
    if t.minute > 57:
        return time(t.hour + 1, 0, 0)
    else:
        return time(t.hour, t.minute // 5 * 5, 0)

class HomePage(webapp.RequestHandler):
    def get(self):
        has_user = users.get_current_user() is not None
        template_values = {
            'schedules' : Schedule.all(),
            'is_loggedin' : has_user,
            'login_link' : users.create_login_url(self.request.uri),
            'logout_link' : users.create_logout_url(self.request.uri),
            'user_name' : users.get_current_user().nickname() if has_user else None,
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
        calc_items = []
        total_weight = sum(i.time_weight for i in items)
        start_time = time(9,0,0)
        end_time = time(17,0,0)
        total_duration = time_diff(end_time, start_time)
        current_time = start_time
        for i in items:
            ci = CalculatedScheduleItem(i)
            ci.pct = 100.0 * i.time_weight / total_weight
            ci.start_time = current_time
            duration = multi_duration(total_duration, ci.pct/100.0)
            ci.end_time = round_time_5min(add_time(ci.start_time, duration))
            current_time = ci.end_time
            ci.ordinal = i.ordinal
            calc_items.append(ci)
        calc_items[-1].end_time = end_time
        current_time = end_time
        
        has_user = users.get_current_user() is not None
        template_values = {
            'schedule' : schedule,
            'items' : calc_items,
            'end_time' : current_time,
            'is_loggedin' : has_user,
            'login_link' : users.create_login_url(self.request.uri),
            'logout_link' : users.create_logout_url(self.request.uri),
            'user_name' : users.get_current_user().nickname() if has_user else None,
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
        last_item = schedule.scheduleitem_set.order('-ordinal').get()
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

class RenameSchedule(webapp.RequestHandler):
    def post(self, schedule_key):
        schedule = GetSchedule(schedule_key)
        if schedule.user != users.get_current_user():
            self.redirect('/')
            return
        schedule.name = self.request.get("value")
        schedule.put()
        sleep(1)
        self.response.out.write(schedule.name)

class RenameScheduleItem(webapp.RequestHandler):
    def post(self, schedule_key):
        schedule = GetSchedule(schedule_key)
        item_key = re.match('subject-name-(.*)', self.request.get("id")).group(1)
        item = ScheduleItem.get(db.Key(item_key))
        if item.schedule.user != users.get_current_user():
            self.redirect('/')
            return
        item.name = self.request.get("value")
        item.put()
        sleep(1)
        self.response.out.write(item.name)
        
class RemoveSchedule(webapp.RequestHandler):
    def post(self, schedule_key):
        schedule = GetSchedule(schedule_key)
        if schedule.user != users.get_current_user():
            self.redirect('/')
            return
        schedule.delete()
        self.redirect('/')

        
application = webapp.WSGIApplication(
                                     [('/', HomePage),
                                      ('/add_schedule', AddSchedule),
                                      ('/schedule/(.*)/add', AddScheduleItem),
                                      ('/schedule/(.*)/(.*)/(more|less|remove)', EditScheduleItem),
                                      ('/schedule/(.*)/rename-item', RenameScheduleItem),
                                      ('/schedule/(.*)/rename', RenameSchedule),
                                      ('/schedule/(.*)/remove', RemoveSchedule),
                                      ('/schedule/(.*)', ViewSchedule)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()