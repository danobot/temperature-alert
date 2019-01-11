# Temperature Difference Alert
# Alerts you when it's cooler outside and its time to open doors and windows for fresh air!
# (Useful in hot climates)
#
# Documentation:    https://github.com/danobot/temperature-alert
# Version:          v0.2.0

import datetime
import logging
from homeassistant.components.alert import Alert
from homeassistant.helpers import service, event
import voluptuous as vol
from homeassistant.helpers.entity_component import EntityComponent
import homeassistant.helpers.config_validation as cv
from homeassistant.core import callback, ServiceCall
from homeassistant.components.notify import (
    ATTR_MESSAGE, DOMAIN as DOMAIN_NOTIFY)
from homeassistant.components.binary_sensor import BinarySensorDevice
VERSION = '0.2.0'
DOMAIN = 'temperature_alert'
devices = []

logger = logging.getLogger(__name__)
async def async_setup(hass, config):
    _config = config[DOMAIN]
    component = EntityComponent(logger, DOMAIN, hass)
    logger.debug("Termpature alert config: " + str(_config))
    for x in _config:
        logger.debug(x)
        devices.append(TempChecker(hass, x))
    await component.async_add_entities(devices)

    logger.info("The {} component is ready!".format(DOMAIN))
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
STATE_COOLER = 'cooler'
STATE_WARMER = 'warmer'
class TempChecker(BinarySensorDevice):


    def __init__(self, hass, config):
        self.friendly_name = config.get('name', 'Temperature Alert')
        self.hass = hass
        self._state = None
        logger.debug("Config: " + str( config ) +"\n\n")
        self.outdoorSensor = config.get(CONF_OUTDOOR_SENSOR)
        logger.info("Outdoor sensor: " + self.outdoorSensor )
        self.indoorSensors = config.get(CONF_INDOOR_SENSORS, None)
        logger.info("Indoor sensor: " +str(self.indoorSensors ))
        self.temp_delta = config.get('temp_delta', None)
        self.threshold = config.get('threshold', 25)
        self.default_state = config.get('mode', STATE_COOLER)
        self._notifiers = config.get('notifiers')
        self.notificationSent = False
        self._may_update = False

        
        event.async_track_state_change(hass,self.outdoorSensor, self.change)
    @property
    def state(self):
        return self._state
    @property
    def name(self):
        """Return the state of the entity."""
        return self.friendly_name
    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._state == self.mode

    @property
    def state_attributes(self):
        if self._state == STATE_COOLER:
            return self.att('It is cooler outside.')
        if self._state == STATE_WARMER:
            return self.att('It is warmer outside.')
    def att(self, state):
        return {
                'state': state,
                'delta': self.last_delta
            }
    @property
    def icon(self):
        """Return the entity icon."""
        if self._state == STATE_COOLER:
            return 'mdi:snowflake'
        if self._state == STATE_WARMER:
            return 'mdi:thermometer'
        return 'mdi:circle-outline'

    def update(self):
        if self._may_update:
            self.async_schedule_update_ha_state(True)
    # HA Callbacks
    async def async_added_to_hass(self):
        """Register update dispatcher."""
        event.async_track_state_change(self.hass, self.outdoorSensor, self.change)
        self._may_update = True

    def change(self, entity, old, new):
        logger.debug("State Changes")
        logger.debug("State Old" + entity)
        logger.debug("State New" + str(new))

        if float(new.state) > self.threshold:
            self.thresholdExceeded = True



        temps = []
        logger.debug("Indoor sensor: " +str(self.indoorSensors ))
        for sensor in self.indoorSensors:
            logger.debug("Checking: " + sensor)
            i =  self.hass.states.get(sensor).state
            logger.debug("Val: " +str( i))
            temps.append(float(i))

            logger.debug("Indoor sensor: " +str(temps ))
            delta = min(temps) - float(new.state)
            logger.debug("Delta:" + str(delta))
        self.last_delta = delta
        if delta > 0:
            
            if delta >= self.temp_delta:
                message = "Outdoor temp {} is lower than coolest indoor temp {}".format(new.state, str(min(temps)))
                logger.info(message)
                self._state = STATE_WARMER
                # logger.info(str(hass.services))
                if not self.notificationSent:

                    for target in self._notifiers:
                        domain, service = target.split('.')
                        logger.debug("Does service {} exist? {}".format(service, self.hass.services.has_service(DOMAIN_NOTIFY,service)))
                        self.hass.async_create_task(
                            self.hass.services.async_call(
                                DOMAIN_NOTIFY, service, {ATTR_MESSAGE: message}
                            )
                        )
                    self.hass.bus.fire('temp_alert', {
                        'delta': delta
                    })
                    self.notificationSent = True

            else:
                logger.info("Outdoor {} is cooler than indoor {}, but only by {} degrees, not {} (threshold)".format(new.state, min(temps),delta, self.temp_delta))
        else:
            logger.info("Indoor is cooler.")
            self.notificationSent = False # Send a new notification (This resets the cycle)
            self._state = STATE_COOLER

        self.update()