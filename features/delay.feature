@delay
Feature: Delay at the boarding station
  As a commuter
  I want to be told when my train's delay changes materially
  So that I can catch an earlier or later train

  Delay is the forecast or actual departure from the boarding station
  less the boarding station departure time (BDT). The delay band is
  floor(delay / N), so a delay of exactly N minutes is in band 1. A
  train running early is in band 0. The first check treats the
  previous band as 0.

  Background:
    Given a monitored journey with a delay band size N of 5 minutes

  Rule: The commuter is notified whenever the delay band rises

    Scenario Outline: Delay rises into a higher band
      Given the train was <previous> minutes late at the last check
      When the system checks the train and it is <current> minutes late
      Then the commuter is notified that the train is <current> minutes late

      Examples:
        | previous | current |
        | 4        | 5       |
        | 0        | 6       |
        | 9        | 10      |
        | 14       | 15      |

    Scenario: First check finds the train already delayed
      Given the train has not been checked before
      When the system checks the train and it is 7 minutes late
      Then the commuter is notified that the train is 7 minutes late

    Scenario: Delay skips several bands between checks
      Given the train was 3 minutes late at the last check
      When the system checks the train and it is 12 minutes late
      Then exactly one delay notification is sent
      And the commuter is notified that the train is 12 minutes late

  Rule: The commuter is notified whenever the delay band falls

    Scenario Outline: Delay falls into a lower, non-zero band
      Given the train was <previous> minutes late at the last check
      When the system checks the train and it is <current> minutes late
      Then the commuter is notified that the train is <current> minutes late

      Examples:
        | previous | current |
        | 12       | 8       |
        | 15       | 9       |
        | 10       | 9       |

    Scenario Outline: Delay falls back into band 0
      Given the train was <previous> minutes late at the last check
      When the system checks the train and it is <current> minutes late
      Then the commuter is notified that the train is back on time

      Examples:
        | previous | current |
        | 7        | 2       |
        | 5        | 4       |
        | 6        | -1      |

  Rule: No notification is sent while the delay stays within its band

    Scenario Outline: Delay changes within a band
      Given the train was <previous> minutes late at the last check
      When the system checks the train and it is <current> minutes late
      Then no delay notification is sent

      Examples:
        | previous | current |
        | 0        | 4       |
        | 5        | 9       |
        | 12       | 10      |
        | -2       | 3       |

  Rule: A delay oscillating across a band boundary notifies on every crossing

    Scenario: Delay flaps across a band boundary
      Given the train was 9 minutes late at the last check
      When successive checks find the train 10, 9 and 10 minutes late
      Then 3 delay notifications are sent
