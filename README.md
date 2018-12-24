Configure like this:

```yaml
temperature_alert:
  - indoor_sensor:
      - input_number.inside_temp
    outdoor_sensor: input_number.outside_temp
    temp_delta: 1
    notifiers:
      - 'notify.file_notification'

```