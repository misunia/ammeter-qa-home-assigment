# Ammeter Testing Framework – QA Exercise

This project was implemented as part of a QA exercise for an embedded systems role.

The goal of the exercise is to design a small but flexible testing framework that can work with different ammeter types, perform configurable sampling, analyze results, and store them in a structured way.

The ammeters themselves are emulated and do not represent real hardware. The focus is on testing approach, structure, and correctness rather than physical accuracy.

## Overview

The project includes emulators for three different ammeter types: Greenlee, ENTES, and CIRCUTOR.  
A unified testing framework is used to run measurements on all ammeter types using the same interface.

The framework supports configurable sampling, statistical analysis of results, and optional visualization.

## Project Structure

Ammeters  
Ammeter emulators and socket client implementation

src/testing  
AmmeterTestFramework implementation

src/utils  
Configuration loading utilities

examples  
Example scripts for running measurements and generating plots

results  
Saved measurement results and graphs

config  
YAML configuration files

## Sampling and Measurement

The framework supports two sampling modes.

The first option is sampling by a fixed number of measurements using measurements_count.

The second option is time based sampling using total_duration_seconds together with sampling_frequency_hz.

Both modes are validated. Missing or partially provided sampling parameters will raise an error.

## Result Analysis

For each test run the following statistics are calculated from the collected measurements.

Mean  
Median  
Standard deviation  
Minimum value  
Maximum value  

The calculated statistics are returned as part of the test result and can also be stored for later inspection.

## Result Management

Each test run receives a unique run ID and stores metadata such as sampling configuration and timestamps.

Results are saved as JSON files under the results directory which allows easy review and comparison of previous runs.

## Running the Tests

Framework behavior is covered using pytest integration tests.

From the project root run:

python -m pytest -vv

The tests verify correct sampling behavior for all ammeter types and validate error handling for invalid configurations.

## Running a Measurement Campaign

A simple measurement campaign can be executed using the example script.

From the project root run:

python -m examples.run_measurements

The script starts all ammeter emulators, runs time based sampling for each ammeter, saves results as JSON files and generates plots.

## Visualization

The generated plots show current measurements over time for each ammeter.

A comparison plot is also generated showing all ammeters under identical sampling conditions.

Since each ammeter emulator uses a different internal model and measurement range, absolute current values differ. The visualization is intended to compare behavior and stability rather than exact numeric values.

## Challenges and Notes

During the implementation several issues were handled including import path resolution, pytest discovery, socket reuse between emulator runs, and validation of sampling parameters.

The solution was kept intentionally simple and extensible without adding unnecessary dependencies.

## Requirements

Python 3.10 or newer

Additional library used:  
matplotlib for visualization

## Final Notes

This project demonstrates testing structure, validation, and analysis in an embedded systems QA context rather than real hardware behavior.


