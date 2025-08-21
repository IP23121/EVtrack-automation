# utils — Helper utilities for Selenium and browser automation

This folder contains utility modules used across the automation layer to start and manage Selenium WebDriver instances and perform common Selenium tasks.

Files

- `selenium_utils.py`
  - Provides `start_driver(headless=True)` which sets up a local Chrome WebDriver using webdriver_manager.
  - Adds many Chrome options optimized for headless operation and aggressive download blocking to prevent files being written during automation.
  - Exposes helper functions:
    - `wait_for_element(driver, by, value, timeout=20)` — wait until an element is present and return it.
    - `click_element(driver, by, value)` — waits then clicks an element.
    - `fill_text_field(driver, by, value, text)` — waits, clears, then types text into an input.
  - This module is used by automation modules when running locally or in non-Lambda environments.

- `lambda_selenium.py`
  - Provides `start_driver_lambda(headless=True)` which initializes Chrome and chromedriver from Lambda layers (`/opt/chrome/chrome` and `/opt/chromedriver`).
  - Falls back to `selenium_utils.start_driver` when not running in Lambda.
  - Includes `cleanup_temp_files()` to purge temporary Chrome data under `/tmp`.
  - Use this module when running in AWS Lambda with a headless Chrome layer.

Usage

- For local development, prefer `from utils.selenium_utils import start_driver` and pass the driver returned to automation classes.
- For Lambda deployments, use `from utils.lambda_selenium import start_driver_lambda`.
