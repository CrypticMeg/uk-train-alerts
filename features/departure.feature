@departure
Feature: Departure from origin
  As a commuter
  I want to know whether my train has left its origin on time
  So that I can decide early whether to change my plans

  Departure is judged against the origin departure time (ODT), even
  when the commuter boards at a later calling point.

  Background:
    Given a monitored journey on a train with an ODT of 15:00

  Rule: A train that departs its origin on time is notified once

    @assumption
    Scenario: Train departs its origin on time
      Given the train departed its origin at 15:00
      When the system checks the train at 15:03
      Then the commuter is notified that the train departed on time

    Scenario: Train that departed on time is not re-notified
      Given the commuter has been notified that the train departed on time
      When the system checks the train at 15:08
      Then no departure notification is sent

  Rule: A train not departed by its ODT is notified once, then again when it departs

    Scenario: Train has not departed at the first check after its ODT
      Given the train has not departed its origin
      When the system checks the train at 15:03
      Then the commuter is notified that the train has not yet departed

    Scenario: Train is still waiting at its origin on later checks
      Given the commuter has been notified that the train has not yet departed
      And the train has not departed its origin
      When the system checks the train at 15:08
      Then no departure notification is sent

    Scenario: Delayed train eventually departs its origin
      Given the commuter has been notified that the train has not yet departed
      And the train departed its origin at 15:07
      When the system checks the train at 15:08
      Then the commuter is notified that the train departed 7 minutes late

    Scenario: Train departed late before the first check after its ODT
      Given the train departed its origin at 15:02
      When the system checks the train at 15:03
      Then the commuter is notified that the train departed 2 minutes late
      And the commuter is not notified that the train has not yet departed

  Rule: Nothing is said about departure before the ODT

    Scenario: Check before the ODT
      Given the train has not departed its origin
      When the system checks the train at 14:58
      Then no departure notification is sent
