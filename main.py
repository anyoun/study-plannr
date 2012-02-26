import cgi
import os
import logging
import re

import json

from jinja2 import Template, Environment, FileSystemLoader
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app, login_required
from google.appengine.ext import db
from time import sleep
from datetime import time, datetime

class Schedule(db.Model):
    user = db.UserProperty()
    name = db.StringProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    start_time = db.TimeProperty(default=time(9,0,0))
    end_time = db.TimeProperty(default=time(17,0,0))
    enable_breaks = db.BooleanProperty(default=False)
    break_time_sec = db.IntegerProperty(default=600)
    def get_NumSubjects(self):
        return self.scheduleitem_set.count()

class ScheduleItem(db.Model):
    schedule = db.ReferenceProperty(Schedule)
    name = db.StringProperty()
    time_weight = db.FloatProperty()
    ordinal = db.IntegerProperty()
     
TIME_FORMAT_STRING = '%I:%M %p'
ADD_FAKE_DELAYS = False

def time_diff(x, y):
    return 3600*(x.hour-y.hour) + 60*(x.minute-y.minute) + x.second-y.second
def to_seconds(x):
    return 3600*x.hour + 60*x.minute + x.second
def add_time(t, delta_seconds):
    total_seconds = time_diff(t, time(0)) + delta_seconds
    td_hours = total_seconds // 3600
    td_minutes = (total_seconds // 60) % 60
    td_seconds = total_seconds % 60
    return time(int(td_hours), int(td_minutes), int(td_seconds))
def multi_duration(td, factor):
    return td * factor
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

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        elif isinstance(obj, Schedule):
            return {
                'name': obj.name,
                'key': str(obj.key()),
                'date': obj.date,
                'start_time': obj.start_time,
                'end_time': obj.end_time,
            }
        return json.JSONEncoder.default(self, obj)

def date_filter(value, format='%x'):
    return value.strftime(format)
env = Environment(loader=FileSystemLoader('.'), autoescape=True)
env.filters['date'] = date_filter

class BaseRequestHandler(webapp.RequestHandler):
    def return_template(self, template_name, data):
        t = env.get_template(template_name)
        self.response.out.write(t.render(data))
    def to_json(self, data):
        return json.dumps(data, cls=DateTimeEncoder)
    def return_json(self, data):
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(self.to_json(data))

class HomePage(BaseRequestHandler):
    def get(self):
        user = users.get_current_user()
        has_user = user is not None
        template_values = {
            'is_loggedin' : has_user,
            'login_link' : users.create_login_url(self.request.uri),
            'logout_link' : users.create_logout_url(self.request.uri),
            'user_name' : user.nickname() if has_user else None,
        }
        self.return_template('index.html', template_values)

class SchedulesPage(BaseRequestHandler):
    @login_required
    def get(self, format):
        user = users.get_current_user()
        schedules = Schedule.all()
        schedules.filter("user = ", user)
        if format == 'json':
            self.return_json(list(schedules.run()))
        else:
            template_values = {
                'schedules' : schedules,
                'logout_link' : users.create_logout_url(self.request.uri),
                'user_name' : user.nickname(),
            }        
            self.return_template('schedules.html', template_values)

def GetSchedule(schedule_key):
    user = users.get_current_user()
    if not user:
        return None
    schedule = Schedule.get(db.Key(schedule_key))
    if schedule.user != user:
        return None
    return schedule
def GetJsonableSchedule(schedule):
    (calc_items, start_time, end_time) = calculate_schedule_items(schedule)
    schedule_json = {
        'items': calc_items,
        'name': schedule.name,
        'key': str(schedule.key()),
        'scheduleKey' : str(schedule.key()),
        'start_time' : start_time.strftime(TIME_FORMAT_STRING),
        'end_time' : end_time.strftime(TIME_FORMAT_STRING),
        'start_time_sec' : to_seconds(start_time),
        'end_time_sec' : to_seconds(end_time),
    }
    return schedule_json

def calculate_schedule_items(schedule):
    items = list(schedule.scheduleitem_set)
    calc_items = []
    total_weight = sum(i.time_weight for i in items)
    start_time = schedule.start_time
    end_time = schedule.end_time
    total_duration = time_diff(end_time, start_time)
    if schedule.enable_breaks:
        total_duration_minus_breaks = total_duration - ((len(items) - 1) * schedule.break_time_sec)
    else:
        total_duration_minus_breaks = total_duration
    current_time = start_time
    for (index, i) in enumerate(items):
        if index != 0 and schedule.enable_breaks:
            calc_items.append({
                'key' : 'break',
                'name' : 'Break',
                'ordinal': i.ordinal + 1.5,
                'pct': schedule.break_time_sec * 1.0 / total_duration * 100,
                'start_time': current_time.strftime(TIME_FORMAT_STRING),
                'end_time': add_time(current_time, schedule.break_time_sec).strftime(TIME_FORMAT_STRING),
                'is_break': True,
            })
            current_time = add_time(current_time, schedule.break_time_sec)

        ci = { }
        ci['key'] = str(i.key())
        ci['name'] = i.name
        ci['is_break'] = False
        ci['ordinal'] = i.ordinal + 1
        ci['start_time'] = current_time.strftime(TIME_FORMAT_STRING)
        
        duration = multi_duration(total_duration_minus_breaks, i.time_weight / total_weight)
        ci['pct'] = duration / total_duration * 100
        current_time = round_time_5min(add_time(current_time, duration))

        item_end = current_time
        ci['end_time'] = item_end.strftime(TIME_FORMAT_STRING)

        calc_items.append(ci)
    if len(calc_items) > 0:
        calc_items[-1]['end_time'] = end_time.strftime(TIME_FORMAT_STRING)
        calc_items[-1]['is_last'] = True
    current_time = end_time
    return (calc_items, start_time, end_time)
    
class ViewSchedule(BaseRequestHandler):
    @login_required
    def get(self, schedule_key, format):
        schedule = GetSchedule(schedule_key)
        if schedule is None:
            self.redirect('/')
            return
        schedule_json = GetJsonableSchedule(schedule)
        has_user = users.get_current_user() is not None
        
        if format == 'json':
            self.return_json(schedule_json)
        else:
            template_values = {
                'schedule' : schedule,
                'originalSchedule' : self.to_json(schedule_json),
                'is_loggedin' : has_user,
                'login_link' : users.create_login_url(self.request.uri),
                'logout_link' : users.create_logout_url(self.request.uri),
                'start_time' : schedule.start_time.strftime(TIME_FORMAT_STRING),
                'end_time' : schedule.end_time.strftime(TIME_FORMAT_STRING),
                'break_time' : schedule.break_time_sec / 60,
                'user_name' : users.get_current_user().nickname() if has_user else None,
            }
            self.return_template('schedule.html', template_values)

class AddSchedule(BaseRequestHandler):
    def post(self):
        user = users.get_current_user()
        if not user:
            self.redirect('/')
            return            
        new_schedule = Schedule()
        new_schedule.user = user
        new_schedule.name = self.request.get('name')
        new_schedule.put()
        new_item = ScheduleItem()
        new_item.schedule = new_schedule
        new_item.name = 'Subject 1'
        new_item.time_weight = 1.0
        new_item.ordinal = 0
        new_item.put()
        self.redirect('/schedule/' + str(new_schedule.key()))

class AddScheduleItem(BaseRequestHandler):
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
        self.return_json(GetJsonableSchedule(schedule))
        
class EditScheduleItem(BaseRequestHandler):
    def post(self, schedule_key, item_key, action):
        item = ScheduleItem.get(db.Key(item_key))
        if item.schedule.user != users.get_current_user():
            self.redirect('/')
            return
        if ADD_FAKE_DELAYS:
            sleep(1)
        if action == 'more':
            item.time_weight *= 1.1
            item.put()
        elif action == 'less':
            item.time_weight *= .9
            item.put()
        elif action == 'remove':
            item.delete()
        elif action == 'rename':
            item.name = self.request.get("value")
            item.put()
            #For renames, just write out the new name rather than all items
            self.response.out.write(item.name)
            return
        else:
            raise Exception('Unknown mode')
        #Return all schedule items
        self.return_json(GetJsonableSchedule(item.schedule))

class EditSchedule(BaseRequestHandler):
    def parse_time(self, s):
        t = datetime.strptime(s, '%I:%M %p').time()
        #logging.info("String: '%s' time: '%s'" % (s,t))
        return t
    def valid(self, s):
        return s is not None and s != ''
    def post(self, schedule_key):
        schedule = GetSchedule(schedule_key)
        if schedule.user != users.get_current_user():
            self.redirect('/')
            return
        if ADD_FAKE_DELAYS:
            sleep(1)
        
        if self.valid(self.request.get("name")):
            schedule.name = self.request.get("name")
            schedule.put()
            self.response.out.write(schedule.name)
            return
        if self.valid(self.request.get("enable_breaks")):
            schedule.enable_breaks = self.request.get("enable_breaks").lower() in ["true", "on"]
        if self.valid(self.request.get("start_time")):
            schedule.start_time = self.parse_time(self.request.get("start_time"))            
        if self.valid(self.request.get("end_time")):
            schedule.end_time = self.parse_time(self.request.get("end_time"))
        if self.valid(self.request.get("break_time_minutes")):
            schedule.break_time_sec = int(self.request.get("break_time_minutes")) * 60
        
        schedule.put()
        self.return_json(GetJsonableSchedule(schedule))
        
class RemoveSchedule(BaseRequestHandler):
    def post(self, schedule_key):
        schedule = GetSchedule(schedule_key)
        if schedule.user != users.get_current_user():
            self.redirect('/')
            return
        schedule.delete()
        self.redirect('/')
        
application = webapp.WSGIApplication(
                                     [('/', HomePage),
                                      ('/schedules(json)?', SchedulesPage),
                                      ('/add_schedule', AddSchedule),
                                      ('/schedule/([^/]*)/add', AddScheduleItem),
                                      ('/schedule/([^/]*)/([^/]*)/(more|less|remove|rename)', EditScheduleItem),
                                      ('/schedule/([^/]*)/edit', EditSchedule),
                                      ('/schedule/([^/]*)/remove', RemoveSchedule),
                                      ('/schedule/([^/]*)/?(json)?', ViewSchedule)],
                                     debug=True)
