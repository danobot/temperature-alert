This is a Home Assistant component which can be configured to send reminders on any `notify` service when it is getting cooler outside. This allows you to open doors and windows and save on A/C electricity usage.

Configure like this:

```yaml

temperature_alert:
  indoor_sensor:
    - sensor.living_room_temp
    - sensor.bedroom_temp
    - sensor.kitchen_temp
    - sensor.office_temp
  outdoor_sensor: sensor.bom_air_temp_c
  temp_delta: 2
  notifiers: 
    - 'notify.telegram'
```




# Automatic updates
Use the `custom_updater` component to track updates.

```yaml
custom_updater:
  track:
    - components
  component_urls:
    - https://raw.githubusercontent.com/danobot/temperature-alert/master/tracker.json
```