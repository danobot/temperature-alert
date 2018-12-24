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