# Temperature Difference Alert
# Alerts you when it's cooler outside and its time to open doors and windows for fresh air!
# (Useful in hot climates)
#
# Documentation:    https://github.com/danobot/temperature-alert
# Version:          v0.1.1

import datetime
import logging
from homeassistant.components.alert import Alert
from homeassistant.helpers import service, event
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.core import callback, ServiceCall
from homeassistant.components.notify import (
    ATTR_MESSAGE, DOMAIN as DOMAIN_NOTIFY)

VERSION = '0.1.0'
DOMAIN = 'temperature_alert'
devices = []

logger = logging.getLogger(__name__)
def setup(hass, config):
    _config = config[DOMAIN]
    logger.debug("Termpature alert config: " + str(_config))
    for x in _config:
        logger.debug(x)
        devices.append(TempChecker(hass, x))

    return True

CONF_INDOOR_SENSORS = 'indoor_sensors'
CONF_OUTDOOR_SENSOR = 'outdoor_sensor'
CONF_TEMP_DELTA = 'delta'
CONF_NOTIFIERS = 'notifiers'
CONF_THRESHOLD = 'threshold'
# CONFIG_SCHEMA = vol.Schema({
#     DOMAIN: vol.Schema({
#         vol.Required(CONF_INDOOR_SENSORS, cv.ensure_list):
#             vol.All(cv.ensure_list, [cv.string]),
#         vol.Required(CONF_OUTDOOR_SENSOR): cv.entity_id,
#         vol.Required(CONF_TEMP_DELTA): cv.entity_id,
#         vol.Required(CONF_THRESHOLD): cv.entity_id,
#         vol.Required(CONF_NOTIFIERS): cv.entity_ids,
#     })
# }, extra=vol.ALLOW_EXTRA)
class TempChecker(Alert):

    def __init__(self, hass, config):
        logger.debug("Config: " + str( config ) +"\n\n")
        self.outdoorSensor = config.get(CONF_OUTDOOR_SENSOR)
        logger.info("Outdoor sensor: " + self.outdoorSensor )
        self.indoorSensors = config.get(CONF_INDOOR_SENSORS, None)
        logger.info("Indoor sensor: " +str(self.indoorSensors ))
        self.temp_delta = config.get('temp_delta', None)
        self.threshold = config.get('threshold', 25)

        self._notifiers = config.get('notifiers')
        self.notificationSent = False


        @callback
        def change(entity, old, new):
            logger.debug("State Changes")
            logger.debug("State Old" + entity)
            logger.debug("State New" + str(new))

            if float(new.state) > self.threshold:
                self.thresholdExceeded = True



            temps = []
            logger.debug("Indoor sensor: " +str(self.indoorSensors ))
            for sensor in self.indoorSensors:
                logger.debug("Checking: " + sensor)
                i =  hass.states.get(sensor).state
                logger.debug("Val: " +str( i))
                temps.append(float(i))

                logger.debug("Indoor sensor: " +str(temps ))
                delta = min(temps) - float(new.state)
                logger.debug("Delta:" + str(delta))
            if delta > 0:
                
                if delta >= self.temp_delta:
                    message = "Outdoor temp {} is lower than coolest indoor temp {}".format(new.state, str(min(temps)))
                    logger.info(message)
                    # logger.info(str(hass.services))
                    if not self.notificationSent:

                        for target in self._notifiers:
                            domain, service = target.split('.')
                            logger.debug("Does service {} exist? {}".format(service, hass.services.has_service(DOMAIN_NOTIFY,service)))
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

  