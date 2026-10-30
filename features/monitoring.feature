@monitoring
Feature: Monitoring journeys
  As a commuter
  I want every journey I plan to be watched reliably
  So that I can trust silence to mean nothing has changed

  The system checks all monitored journeys every 5 minutes.

  Rule: Several journeys are monitored independently

    Scenario: Two journeys on the same day
      Given monitored journeys on the 15:00 and 16:00 trains
      When the system checks the trains
      Then each journey's notifications are decided independently
      And each notification identifies its train

  Rule: The calendar is the primary source of journeys when available

    @assumption
    Scenario: Same train in the calendar and the configuration
      Given the calendar is available
      And the 15:00 train appears in both the calendar and the configuration
      When the system checks the trains
      Then the 15:00 train is monitored once
      And the calendar's journey details are used

    @assumption
    Scenario: Calendar is unavailable
      Given the calendar is unavailable
      And the 15:00 train appears in the configuration
      When the system checks the trains
      Then the 15:00 train is monitored using the configuration's journey details

    @assumption
    Scenario: Journey removed from the calendar
      Given the 15:00 train was monitored at the last check
      And its journey has since been removed from the calendar
      When the system checks the trains
      Then the 15:00 train is no longer monitored

  Rule: Monitoring of a journey ends when the train departs the boarding station

    Scenario: Train departs the boarding station
      Given a monitored journey with a delay band size N of 5 minutes
      And the train has departed the boarding station
      And the train is now 10 minutes late
      When the system checks the trains
      Then no notification is sent
      And the journey is no longer monitored

    Scenario: Boarding station is the origin
      Given a monitored journey whose boarding station is the train's origin
      And the train departed its origin on time
      When the system checks the trains
      Then the commuter is notified that the train departed on time
      And the journey is no longer monitored

  Rule: A notification is only recorded as sent once it is delivered

    Scenario: Notification service is unavailable
      Given a notification is due for a monitored journey
      And the notification service is unavailable
      When the system checks the trains
      Then the notification is not recorded as sent

    Scenario: Notification service recovers
      Given a notification was not delivered at the last check
      And the notification is still due
      And the notification service is available
      When the system checks the trains
      Then the notification is sent

  Rule: A train data source failure is notified once per outage

    Scenario: Train data source becomes unavailable
      Given the train data source was available at the last check
      And the train data source is unavailable
      When the system checks the trains
      Then the commuter is notified that train data is unavailable

    Scenario: Train data source remains unavailable
      Given the commuter has been notified that train data is unavailable
      And the train data source is unavailable
      When the system checks the trains
      Then no notification is sent

    @assumption
    Scenario: Train data source fails again after recovering
      Given the train data source recovered at the last check
      And the train data source is unavailable
      When the system checks the trains
      Then the commuter is notified that train data is unavailable

  Rule: A train that cannot be found is a system error, not a notification

    Scenario: Journey's train is not in the train data
      Given a monitored journey on a train that the train data source does not know
      When the system checks the trains
      Then no notification is sent
      And a system error is logged for the journey
