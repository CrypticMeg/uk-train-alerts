@cancellation
Feature: Cancellation and alteration
  As a commuter
  I want to know as soon as my train will not run as planned
  So that I can look at my options straight away

  A partial cancellation or diversion is a subset of cancellation. The
  notification only needs to prompt the commuter to look.

  Background:
    Given a monitored journey on a train with an Orignin Departure Time of 15:00

  Rule: A cancellation is notified as soon as it is seen

    Scenario: Train is cancelled before it departs its origin
      Given the train has been cancelled
      When the system checks the train at 14:30
      Then the commuter is notified that the train is cancelled
      And no departure notification is sent

    Scenario: Cancellation replaces the late-departure notification
      Given the train has been cancelled
      When the system checks the train at 15:03
      Then the commuter is notified that the train is cancelled
      And the commuter is not notified that the train has not yet departed

    Scenario: Train is cancelled after it departs its origin
      Given the commuter has been notified that the train departed on time
      And the train has been cancelled
      When the system checks the train at 15:08
      Then the commuter is notified that the train is cancelled

  Rule: A cancelled train is notified once and then no longer monitored

    Scenario: Later checks of a cancelled train
      Given the commuter has been notified that the train is cancelled
      When the system checks the train at 15:13
      Then no notification is sent
      And the journey is no longer monitored

  Rule: Partial cancellations and diversions are notified as cancellations

    Scenario Outline: Train no longer runs as planned
      Given the train has the alteration "<alteration>"
      When the system checks the train at 14:30
      Then the commuter is notified that the train is altered and should be checked

      Examples:
        | alteration                               |
        | cancelled at the boarding station        |
        | starts short of its planned origin       |
        | terminates short of its planned terminus |
        | no longer calls at the boarding station  |
        | diverted                                 |
