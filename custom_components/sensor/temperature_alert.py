# Temperature Difference Alert
# Alerts you when it's cooler outside and its time to open doors and windows for fresh air!
# (Useful in hot climates)
#
# Documentation:    https://github.com/danobot/temperature-alert
# Version:          v1.3.0

from datetime import datetime
import logging
from homeassistant.components.alert import Alert
from homeassistant.helpers import service, event
import voluptuous as vol
from homeassistant.helpers.entity_component import EntityComponent
import homeassistant.helpers.config_validation as cv
from homeassistant.core import callback, ServiceCall
from homeassistant.components.notify import (
    ATTR_MESSAGE, DOMAIN as DOMAIN_NOTIFY)
from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_COLD,
    BinarySensorEntity
);

VERSION = '1.3.0'
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
STATE_ON = 'cooler'
STATE_OFF = 'warmer'
class TempChecker(BinarySensorEntity):


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
        self.default_state = config.get('mode', STATE_ON)
        self._notifiers = config.get('notifiers')
        self.notificationSent = False
        self._may_update = False
        self._flipped_over = None
        self.minTemp = None
        self.maxTemp = None
        self.last_delta_max = 0
        self.last_delta_min = 0
        event.async_track_state_change(hass,self.outdoorSensor, self.change)
    # @property
    # def state(self):
    #     return self._state
    @property
    def name(self):
        """Return the state of the entity."""
        return self.friendly_name
    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._state == self.mode
    @property
    def should_poll(self):
        """Return True if entity has to be polled for state."""
        return False
    @property
    def state_attributes(self):
        if self._state == STATE_ON:
            return self.att('It is nice and cool inside.')
        if self._state == STATE_OFF:
            return self.att('It is cooler outside.')

    def att(self, state):
        return {
                'state': state,
                'delta': self.last_delta,
                'delta_min': self.last_delta_min,
                'delta_max': self.last_delta_max,
                'last_change': self._flipped_over,
                'min': self.minTemp,
                'max': self.maxTemp
            }
    @property
    def icon(self):
        """Return the entity icon."""
        if self._state == STATE_ON:
            return 'mdi:snowflake'
        if self._state == STATE_OFF:
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
        logger.debug("State " + entity)
        logger.debug("State New" + str(new))
        try:

            temps = []
            logger.debug("Indoor sensors: " +str(self.indoorSensors ))
            for sensor in self.indoorSensors:
                i = self.hass.states.get(sensor).state
                if i:
                    temps.append(float(i))

            logger.debug("Indoor sensor temps: " + str(temps))

            self.minTemp = round(min(temps), 1)
            self.maxTemp = round(max(temps), 1)

            self.last_delta_min = round(self.minTemp - float(new.state), 1)
            self.last_delta = round(self.last_delta_min, 1)
            self.last_delta_max = round(self.maxTemp - float(new.state), 1)

            logger.debug("Delta:" + str(self.last_delta))
            if self.last_delta > 0:

                if self.last_delta >= self.temp_delta:
                    message = "Outdoor temp is {}. This is lower than coolest indoor temp {}".format(new.state, str(min(temps)))
                    logger.info(message)
                    self._state = STATE_ON
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
                            'delta': round(self.last_delta,1),
                            'delta_min': self.last_delta_min,
                            'delta_max': self.last_delta_max,
                            'last_change': self._flipped_over,
                            'min': self.minTemp,
                            'max': self.maxTemp
                        })

                        self._flipped_over = datetime.now()
                        self.notificationSent = True

                else:
                    logger.info("Outdoor temp is {}. This is cooler than indoor {}, but only by {} degrees, not {} (threshold)".format(new.state, min(temps), self.last_delta, self.temp_delta))
            else:
                logger.info("Indoor is cooler.")
                if (self.notificationSent):
                    self._flipped_over = datetime.now()

                self.notificationSent = False # Send a new notification (This resets the cycle)
                self._state = STATE_OFF
            self.update()
        except ValueError as e:
            logger.debug("It is not ready yet.")
    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return DEVICE_CLASS_COLD
