from deebotozmo import *


class ObservableVacBot(VacBot):
    def __init__(self, user, domain, resource, secret, vacuum, continent, live_map_enabled = True, show_rooms_color = False, verify_ssl=True):
        VacBot.__init__(self, user, domain, resource, secret, vacuum, continent, live_map_enabled = True, show_rooms_color = False, verify_ssl=True)

        self.errorEvents = EventEmitter()
        self.lifespanEvents = EventEmitter()
        self.fanspeedEvents = EventEmitter()
        self.cleanLogsEvents = EventEmitter()
        self.waterEvents = EventEmitter()          
        self.batteryEvents = EventEmitter()
        self.statusEvents = EventEmitter()
        self.statsEvents = EventEmitter()

    def _handle_errors(self, event):
        VacBot._handle_error(self, event)        
        self.errorEvents.notify(event)
        
    def _handle_life_span(self, event):
        VacBot._handle_life_span(self, event)
        self.lifespanEvents.notify(event)

    def _handle_fan_speed(self, event):
        VacBot._handle_fan_speed(self, event)
        self.fanspeedEvents.notify(self.fan_speed)

    def _handle_clean_logs(self, event):
        VacBot._handle_clean_logs(self, event)
        self.cleanLogsEvents.notify(event=(self.lastCleanLogs, self.last_clean_image))

    def _handle_water_info(self, event):
        VacBot._handle_water_info(self, event)
        self.waterEvents.notify(event=(self.water_level, self.mop_attached))

    def _handle_clean_report(self, event):
        
        response = event['body']['data']
        if response['state'] == 'clean':
            if response['trigger'] == 'app' or response['trigger'] == 'shed':
                if response['cleanState']['motionState'] == 'working':
                    self.vacuum_status = 'STATE_CLEANING'
                elif response['cleanState']['motionState'] == 'pause':
                    self.vacuum_status = 'STATE_PAUSED'
                else:
                    self.vacuum_status = 'STATE_RETURNING'
            elif response['trigger'] == 'alert':
                self.vacuum_status = 'STATE_ERROR'
        self.statusEvents.notify(self.vacuum_status)

    def _handle_battery_info(self, event):
        VacBot._handle_battery_info(self,event)
        self.batteryEvents.notify(self.battery_status)

    def _handle_charge_state(self, event):
        VacBot._handle_charge_state(self, event)
        self.statusEvents.notify(self.vacuum_status)

    def _handle_stats(self, event):
        VacBot._handle_stats(self, event)
        self.statsEvents.notify(event)

class EventEmitter(object):
    """A very simple event emitting system."""
    def __init__(self):
        self._subscribers = []

    def subscribe(self, callback):
        listener = EventListener(self, callback)
        self._subscribers.append(listener)
        return listener

    def unsubscribe(self, listener):
        self._subscribers.remove(listener)

    def notify(self, event):
        for subscriber in self._subscribers:
            subscriber.callback(event)


class EventListener(object):
    """Object that allows event consumers to easily unsubscribe from events."""
    def __init__(self, emitter, callback):
        self._emitter = emitter
        self.callback = callback

    def unsubscribe(self):
        self._emitter.unsubscribe(self)