# Requirements

This is a home assistant component to find the best priced energy in a time slot. The user will set up the length of the slot, the total kWh taken across that time slot, and an optional start and end time to constrain the slot.

The prices are in two states, one for today's rates and one for tomorrow's rates. Each one looks like this;

event_types:
  - octopus_energy_electricity_current_day_rates
event_type: octopus_energy_electricity_current_day_rates
rates:
  - start: "2026-05-29T00:00:00+01:00"
    end: "2026-05-29T00:30:00+01:00"
    value_inc_vat: 0.22302
    is_capped: false
  - start: "2026-05-29T00:30:00+01:00"
    end: "2026-05-29T01:00:00+01:00"
    value_inc_vat: 0.2142
    is_capped: false
  - start: "2026-05-29T01:00:00+01:00"
    end: "2026-05-29T01:30:00+01:00"
    value_inc_vat: 0.191625
    is_capped: false
  - start: "2026-05-29T01:30:00+01:00"
    end: "2026-05-29T02:00:00+01:00"
    value_inc_vat: 0.19005
    is_capped: false
  - start: "2026-05-29T02:00:00+01:00"
    end: "2026-05-29T02:30:00+01:00"
    value_inc_vat: 0.183015
    is_capped: false
  - start: "2026-05-29T02:30:00+01:00"
    end: "2026-05-29T03:00:00+01:00"
    value_inc_vat: 0.18354
    is_capped: false
  - start: "2026-05-29T03:00:00+01:00"
    end: "2026-05-29T03:30:00+01:00"
    value_inc_vat: 0.19425
    is_capped: false
  - start: "2026-05-29T03:30:00+01:00"
    end: "2026-05-29T04:00:00+01:00"
    value_inc_vat: 0.19992
    is_capped: false
  - start: "2026-05-29T04:00:00+01:00"
    end: "2026-05-29T04:30:00+01:00"
    value_inc_vat: 0.201915
    is_capped: false
  - start: "2026-05-29T04:30:00+01:00"
    end: "2026-05-29T05:00:00+01:00"
    value_inc_vat: 0.20538
    is_capped: false
  - start: "2026-05-29T05:00:00+01:00"
    end: "2026-05-29T05:30:00+01:00"
    value_inc_vat: 0.20307
    is_capped: false
  - start: "2026-05-29T05:30:00+01:00"
    end: "2026-05-29T06:00:00+01:00"
    value_inc_vat: 0.213675
    is_capped: false
  - start: "2026-05-29T06:00:00+01:00"
    end: "2026-05-29T06:30:00+01:00"
    value_inc_vat: 0.20307
    is_capped: false
  - start: "2026-05-29T06:30:00+01:00"
    end: "2026-05-29T07:00:00+01:00"
    value_inc_vat: 0.218505
    is_capped: false
  - start: "2026-05-29T07:00:00+01:00"
    end: "2026-05-29T07:30:00+01:00"
    value_inc_vat: 0.21903
    is_capped: false
  - start: "2026-05-29T07:30:00+01:00"
    end: "2026-05-29T08:00:00+01:00"
    value_inc_vat: 0.22953
    is_capped: false
  - start: "2026-05-29T08:00:00+01:00"
    end: "2026-05-29T08:30:00+01:00"
    value_inc_vat: 0.227325
    is_capped: false
  - start: "2026-05-29T08:30:00+01:00"
    end: "2026-05-29T09:00:00+01:00"
    value_inc_vat: 0.22491
    is_capped: false
  - start: "2026-05-29T09:00:00+01:00"
    end: "2026-05-29T09:30:00+01:00"
    value_inc_vat: 0.20349
    is_capped: false
  - start: "2026-05-29T09:30:00+01:00"
    end: "2026-05-29T10:00:00+01:00"
    value_inc_vat: 0.19152
    is_capped: false
  - start: "2026-05-29T10:00:00+01:00"
    end: "2026-05-29T10:30:00+01:00"
    value_inc_vat: 0.18081
    is_capped: false
  - start: "2026-05-29T10:30:00+01:00"
    end: "2026-05-29T11:00:00+01:00"
    value_inc_vat: 0.1659
    is_capped: false
  - start: "2026-05-29T11:00:00+01:00"
    end: "2026-05-29T11:30:00+01:00"
    value_inc_vat: 0.149415
    is_capped: false
  - start: "2026-05-29T11:30:00+01:00"
    end: "2026-05-29T12:00:00+01:00"
    value_inc_vat: 0.13965
    is_capped: false
  - start: "2026-05-29T12:00:00+01:00"
    end: "2026-05-29T12:30:00+01:00"
    value_inc_vat: 0.13692
    is_capped: false
  - start: "2026-05-29T12:30:00+01:00"
    end: "2026-05-29T13:00:00+01:00"
    value_inc_vat: 0.12369
    is_capped: false
  - start: "2026-05-29T13:00:00+01:00"
    end: "2026-05-29T13:30:00+01:00"
    value_inc_vat: 0.11487
    is_capped: false
  - start: "2026-05-29T13:30:00+01:00"
    end: "2026-05-29T14:00:00+01:00"
    value_inc_vat: 0.11886
    is_capped: false
  - start: "2026-05-29T14:00:00+01:00"
    end: "2026-05-29T14:30:00+01:00"
    value_inc_vat: 0.11487
    is_capped: false
  - start: "2026-05-29T14:30:00+01:00"
    end: "2026-05-29T15:00:00+01:00"
    value_inc_vat: 0.11487
    is_capped: false
  - start: "2026-05-29T15:00:00+01:00"
    end: "2026-05-29T15:30:00+01:00"
    value_inc_vat: 0.14448
    is_capped: false
  - start: "2026-05-29T15:30:00+01:00"
    end: "2026-05-29T16:00:00+01:00"
    value_inc_vat: 0.17787
    is_capped: false
  - start: "2026-05-29T16:00:00+01:00"
    end: "2026-05-29T16:30:00+01:00"
    value_inc_vat: 0.28854
    is_capped: false
  - start: "2026-05-29T16:30:00+01:00"
    end: "2026-05-29T17:00:00+01:00"
    value_inc_vat: 0.28854
    is_capped: false
  - start: "2026-05-29T17:00:00+01:00"
    end: "2026-05-29T17:30:00+01:00"
    value_inc_vat: 0.315945
    is_capped: false
  - start: "2026-05-29T17:30:00+01:00"
    end: "2026-05-29T18:00:00+01:00"
    value_inc_vat: 0.31395
    is_capped: false
  - start: "2026-05-29T18:00:00+01:00"
    end: "2026-05-29T18:30:00+01:00"
    value_inc_vat: 0.33432
    is_capped: false
  - start: "2026-05-29T18:30:00+01:00"
    end: "2026-05-29T19:00:00+01:00"
    value_inc_vat: 0.344505
    is_capped: false
  - start: "2026-05-29T19:00:00+01:00"
    end: "2026-05-29T19:30:00+01:00"
    value_inc_vat: 0.22953
    is_capped: false
  - start: "2026-05-29T19:30:00+01:00"
    end: "2026-05-29T20:00:00+01:00"
    value_inc_vat: 0.23835
    is_capped: false
  - start: "2026-05-29T20:00:00+01:00"
    end: "2026-05-29T20:30:00+01:00"
    value_inc_vat: 0.24822
    is_capped: false
  - start: "2026-05-29T20:30:00+01:00"
    end: "2026-05-29T21:00:00+01:00"
    value_inc_vat: 0.242445
    is_capped: false
  - start: "2026-05-29T21:00:00+01:00"
    end: "2026-05-29T21:30:00+01:00"
    value_inc_vat: 0.240765
    is_capped: false
  - start: "2026-05-29T21:30:00+01:00"
    end: "2026-05-29T22:00:00+01:00"
    value_inc_vat: 0.24738
    is_capped: false
  - start: "2026-05-29T22:00:00+01:00"
    end: "2026-05-29T22:30:00+01:00"
    value_inc_vat: 0.23373
    is_capped: false
  - start: "2026-05-29T22:30:00+01:00"
    end: "2026-05-29T23:00:00+01:00"
    value_inc_vat: 0.24717
    is_capped: false
  - start: "2026-05-29T23:00:00+01:00"
    end: "2026-05-29T23:30:00+01:00"
    value_inc_vat: 0.224175
    is_capped: false
  - start: "2026-05-29T23:30:00+01:00"
    end: "2026-05-30T00:00:00+01:00"
    value_inc_vat: 0.22554
    is_capped: false
min_rate: 0.11487
max_rate: 0.344505
average_rate: 0.20971562
mpan: "XXXXXXXXXXX"
serial_number: XXXXXXXXXXXXXX
tariff_code: E-1R-AGILE-24-10-01-H
friendly_name: Electricity Meter Current Day Rates Electricity 

The name of the current and next state will come from a setting for the device. The next state rates will be empty until 4pm on the day