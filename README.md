This is a Home Assistant component which can be configured to send reminders on any `notify` service when it is getting cooler outside. This allows you to open doors and windows and save on A/C electricity usage.

Configure like this:

```yaml

temperature_alert:
  - indoor_sensor:
      - sensor.living_room_temp
      - sensor.bedroom_temp
      - sensor.kitchen_temp
      - sensor.office_temp
    outdoor_sensor: sensor.bom_air_temp_c
    temp_delta: 2                           # min delta before triggering
    notifiers: 
      - 'notify.telegram'
    mode: cooler                            # cooler/warmer
```

# Binary Sensor
An entity under `binary_sensor` will be created which can be used in automations. 

* It's state will be `cooler` if indoor temps are cooler than outdoor temps.
* It's state will be `warmer` if indoor temps are warmer than outdoor temps.


# Automatic updates
Install using HACS
```
