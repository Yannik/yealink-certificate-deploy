#!/usr/bin/env python3

import logging
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.options import Options

def stepshot(driver, screenshots, suffix):
    if screenshots:
        driver.save_screenshot('selenium_' + str(suffix) + '.png')

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("host", help="host")
parser.add_argument("password", help="yealink phone admin password")
parser.add_argument("certfile", help="certfile should contain both cert and key")
parser.add_argument("--headless", action="store_true", help="run headless")
parser.add_argument("--keep-open", action="store_true", help="keep browser window open")
parser.add_argument("--insecure", action="store_true", help="ignore invalid ssl cert on phone (useful for first setup)")
parser.add_argument("--no-screenshots", action="store_false", help="disable saving screenshots for each step")
parser.add_argument("--debug", action="store_true", help="debug output")
args = parser.parse_args()

screenshots = args.no_screenshots

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logging.getLogger().addHandler(ch)

options = Options()
if args.debug:
  options.log.level = "trace"
  logger.setLevel(logging.DEBUG)
if args.headless:
  options.add_argument("--headless")

capabilities = DesiredCapabilities.FIREFOX.copy()
if args.insecure:
  capabilities['acceptInsecureCerts'] = True
driver = webdriver.Firefox(capabilities=capabilities, options=options)
driver.set_window_size(1600, 900)

driver.get("https://" + args.host)

stepshot(driver, screenshots, 1)

logger.info("Entering username/password and submitting form")
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, 'input#idUsername'))
).send_keys("admin")
password_field = driver.find_element(By.CSS_SELECTOR, 'input#idPassword')
password_field.send_keys(args.password)
password_field.send_keys(Keys.RETURN)
stepshot(driver, screenshots, 2)

logger.info("Opening security page")
securityButton = WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.XPATH, '//label[contains(@onclick, "security")] | //li[@id="Security"]'))
).click()
stepshot(driver, screenshots, 3)

logger.info("Opening server certificates page")
WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.XPATH, '//label[contains(@onclick, "server-cert")] | //li[@id="SecurityServerCert"]'))
).click()
stepshot(driver, screenshots, 4)

logger.info("Selecting certificate for upload" + os.path.abspath(args.certfile))
fileinput = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, '//input[@id="_upload_UploadServerCert"]|//input[@id="server-cert-file"]'))
).send_keys(os.path.abspath(args.certfile))
stepshot(driver, screenshots, 4)

logger.info("Clicking upload button")
driver.find_elements(By.XPATH, '//button[@id="btn_upload"] | //button[@id="server-cert-upload-btn"]')[0].click()

logger.info("Waiting for upload to complete")
# for successfull uploads without any errors, no div.upload-result is created on T54W
# therefore we just check if the upload was successful
WebDriverWait(driver, 10).until(
      EC.presence_of_element_located((By.CSS_SELECTOR, 'div.upload_result, div.upload-result, div.ivu-progress-success')),
)

upload_result = driver.find_elements(By.CSS_SELECTOR, 'div.upload_result, div.upload-result')
if len(upload_result) > 0:
  WebDriverWait(driver, 10).until_not(
      EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'div.upload_result'), "Uploading, please wait"),
  )
  logger.info("Upload result: " + upload_result[0].text)

stepshot(driver, screenshots, 5)

# upload_result == T46S, upload-result == T54W. T54W does not do a page reload.
if len(upload_result) > 0 and upload_result[0].get_attribute("class") == "upload_result":
  # page automatically reloads after upload
  old_page=driver.find_element(By.TAG_NAME, 'html')
  WebDriverWait(driver, 10).until(
      EC.staleness_of(old_page)
  )
  stepshot(driver, screenshots, 6)
  logger.info("Page reload completed.")

logger.info("Opening Settings page")
driver.find_element(By.XPATH, '//label[contains(@onclick, "settings-preference")] | //li[@id="Settings"]').click()
logger.info("Opening upgrade page")
WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.XPATH, '//label[contains(@onclick, "settings-upgrade")] | //li[@id="SettingUpgrade"]'))
).click()
stepshot(driver, screenshots, 7)
logger.info("Clicking reboot button")
WebDriverWait(driver, 10).until(
    EC.visibility_of_element_located((By.CSS_SELECTOR, 'button#Reboot, div[name="RebootPhone"] button'))
).click()

el = WebDriverWait(driver, 10).until(
    EC.any_of(
      EC.alert_is_present(),
      EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.ivu-modal-confirm button.ivu-btn-primary'))
    )
)
# on T54W this is simply a html modal, on T46S it the confirmation is a javascript alert()
if isinstance(el, webdriver.remote.webelement.WebElement):
  el.click()
  WebDriverWait(driver, 10).until(
      EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'div.ivu-modal-confirm-body'), "Rebooting, please wait..."),
  )
else:
  driver.switch_to.alert.accept()
  WebDriverWait(driver, 10).until(
      EC.visibility_of_element_located((By.CSS_SELECTOR, 'div.notice-info'))
  )

if not args.keep_open:
  driver.quit()
