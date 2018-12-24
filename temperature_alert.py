# Temperature Difference Reminder
# Alerts you when its cooler outside and its time to open doors and windows for fresh air!
# (Useful in hot climates)
#
# Documentation:    https://github.com/danobot/temp_alert
# Version:          v0.1.0

import datetime
import logging
from homeassistant.components.alert import Alert
from homeassistant.helpers import service, event
from homeassistant.core import callback, ServiceCall
from homeassistant.components.notify import (
    ATTR_MESSAGE, DOMAIN as DOMAIN_NOTIFY)

DOMAIN = 'temperature_alert'
devices = []

logger = logging.getLogger(__name__)
def setup(hass, config):
    _config = config[DOMAIN]
    
    for x in _config:
        logger.info(x)
        devices.append(TempChecker(hass, x))

    return True


class TempChecker(Alert):

    def __init__(self, hass, config):
        logger.info("Config: " + str( config ) +"\n\n")
        self.outdoorSensor = config.get('outdoor_sensor')
        logger.info("Outdoor sensor: " + self.outdoorSensor )
        self.indoorSensors = config.get('indoor_sensor', None)
        logger.info("Indoor sensor: " +str(self.indoorSensors ))
        self.temp_delta = config.get('temp_delta', None)
        self.threshold = config.get('threshold', 25)

        self._notifiers = config.get('notifiers')
        self.notificationSent = False


        @callback
        def change(entity, old, new):
            logger.info("State Changes")
            logger.info("State Old" + entity)
            logger.info("State New" + str(new))

            if float(new.state) > self.threshold:
                self.thresholdExceeded = True



            temps = []
            logger.info("Indoor sensor: " +str(self.indoorSensors ))
            for sensor in self.indoorSensors:
                logger.info("Checking: " + sensor)
                i =  hass.states.get(sensor).state
                logger.info("Val: " +str( i))
                temps.append(float(i))

                logger.info("Indoor sensor: " +str(temps ))
                delta = min(temps) - float(new.state)
                logger.info("Delta:" + str(delta))
            if delta > 0:
                
                if delta >= self.temp_delta:
                    message = "Outdoor temp {} is lower than coolest indoor temp {}".format(new.state, str(min(temps)))
                    logger.info(message)
                    logger.info(str(hass.services))
                    if not self.notificationSent:

                        for target in self._notifiers:
                            domain, service = target.split('.')
                            logger.info("Does service {} exist? {}".format(service, hass.services.has_service(DOMAIN_NOTIFY,service)))
                            hass.async_create_task(
                                hass.services.async_call(
                                    DOMAIN_NOTIFY, service, {ATTR_MESSAGE: message}
                                )
                            )

                        self.notificationSent = True

                else:
                    logger.info("Outdoor {} is cooler than indoor {}, but only by {} degrees, not {} (threshold)".format(new.state, min(temps),delta, self.temp_delta))
            else:
                logger.info("Indoor is cooler.")
                self.notificationSent = False # Send a new notification (This resets the cycle)

        event.async_track_state_change(hass,self.outdoorSensor, change)

  