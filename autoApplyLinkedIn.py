from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from info import PAGE_LOAD_WAIT_TIME, KEYWORD_LIST, LOCATION
import pwinput
import os
import json
import time
import traceback

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
PAGES = 3

def initDriver(headess: bool):
  options = webdriver.ChromeOptions()
  options.add_argument('log-level=3')
  if headess:
    options.add_argument("--headless=new")
  return webdriver.Chrome(options=options)

def doSignInStuff(driver: webdriver.Chrome):
  driver.get("https://www.linkedin.com/home")
  emailPhone = driver.find_element(by=By.NAME, value="session_key")
  emailPhone.click()
  emailPhone.send_keys(input("Email: "))
  password = driver.find_element(by=By.NAME, value="session_password")
  password.click()
  password.send_keys(pwinput.pwinput())
  signInButton = driver.find_element(by=By.CSS_SELECTOR, value='[data-id="sign-in-form__submit-btn"]')
  signInButton.submit()
  if("https://www.linkedin.com/checkpoint/challenge" in driver.current_url):
    waitToCompleteTest(driver)

def waitToCompleteTest(driver: webdriver.Chrome):
  print("Please complete the verification check (waiting 5 mins)...")
  wait = WebDriverWait(driver, timeout=250)
  wait.until(lambda d : "https://www.linkedin.com/checkpoint/challenge" not in d.current_url)
  print("test complete!")

def doJobSearch(searchKeyWord: str):
  driver.get("https://www.linkedin.com/jobs/search/?keywords={}".format(searchKeyWord))
  locationInp = driver.find_element(by=By.CSS_SELECTOR, value='.jobs-search-box__input--location input')
  locationInp.send_keys(Keys.CONTROL,"a")
  locationInp.send_keys(Keys.DELETE)
  locationInp.send_keys(LOCATION)
  jobSearchSubmitButton = driver.find_element(by=By.CLASS_NAME, value='jobs-search-box__submit-button')
  jobSearchSubmitButton.click()
  curPage = 1
  while True:
    time.sleep(PAGE_LOAD_WAIT_TIME)
    for scrollPos in range(0, 5000, 500):
      driver.execute_script("document.querySelector('.jobs-search-results-list').scrollTo(0, {})".format(scrollPos))
      time.sleep(1)
    jobCardsLink = driver.find_elements(by=By.CSS_SELECTOR, value='.jobs-search-results__list-item a')
    print("Found {} {} jobs in page {} =>".format(len(jobCardsLink), searchKeyWord, curPage))
    alreadyApplied = 0
    for i in range(len(jobCardsLink)):
      print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
      jobTitle = jobCardsLink[i].get_attribute("innerText")
      print("Title: ", jobTitle)
      ActionChains(driver).move_to_element(jobCardsLink[i]).perform()
      jobCardsLink[i].click()
      time.sleep(PAGE_LOAD_WAIT_TIME)
      topCard = driver.find_element(by=By.CLASS_NAME,value="jobs-unified-top-card")
      print("Info: ", topCard.find_element(by=By.CLASS_NAME,value="job-details-jobs-unified-top-card__primary-description-without-tagline").get_attribute("innerText"))
      applyDiv = topCard.find_element(by=By.CLASS_NAME,value="jobs-s-apply")
      applyText = applyDiv.get_attribute("innerText")
      print("Apply Text:\n", applyText)
      if("Applied" in applyText):
        alreadyApplied += 1
      elif(jobTitle.isascii() and applyText == "Easy Apply"):
        applyDiv.find_element(by=By.TAG_NAME,value="button").click()
        easyApplyClicked(driver)
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print("{} jobs were already applied to before".format(alreadyApplied))
    curPage += 1
    if(curPage == PAGES): break
    driver.find_element(by=By.CSS_SELECTOR, value='.artdeco-pagination__pages [data-test-pagination-page-btn="{}"]'.format(curPage)).click()

def easyApplyClicked(driver: webdriver.Chrome):
  time.sleep(PAGE_LOAD_WAIT_TIME)
  applyContent = driver.find_element(by=By.CLASS_NAME,value="jobs-easy-apply-content")
  def getApplyContentChild(cssSelector) -> list[WebElement]:
    nonlocal applyContent
    return applyContent.find_elements(by=By.CSS_SELECTOR, value= cssSelector)

  try:
    if not len(getApplyContentChild('[aria-label="Submit application"]')):
      while not len(getApplyContentChild('[aria-label="Review your application"]')):
        getApplyContentChild('[aria-label="Continue to next step"]')[0].click()
        time.sleep(PAGE_LOAD_WAIT_TIME)
        if len(getApplyContentChild('[type="error-pebble-icon"]')):
          fillForm(applyContent)
      getApplyContentChild('[aria-label="Review your application"]')[0].click()
      time.sleep(PAGE_LOAD_WAIT_TIME)
      while len(getApplyContentChild('[type="error-pebble-icon"]')):
        fillForm(applyContent)
        getApplyContentChild('[aria-label="Review your application"]')[0].click()
    time.sleep(PAGE_LOAD_WAIT_TIME)
    getApplyContentChild('[aria-label="Submit application"]')[0].click()
    time.sleep(PAGE_LOAD_WAIT_TIME)
    while len(driver.find_elements(by=By.CSS_SELECTOR, value='[type="error-pebble-icon"]')):
      fillForm(applyContent)
      getApplyContentChild('[aria-label="Submit application"]')[0].click()
      time.sleep(PAGE_LOAD_WAIT_TIME)
    while len(driver.find_elements(by=By.CSS_SELECTOR, value='button[aria-label="Dismiss"]')) == 0:
      time.sleep(PAGE_LOAD_WAIT_TIME)
    driver.find_element(by=By.CSS_SELECTOR, value='button[aria-label="Dismiss"]').click()
  except:
    print("Error encountered while processing application, skipping to next application...")

def fillForm(applyContent: WebElement):
  global qaDict

  qGroups = applyContent.find_elements(by=By.CLASS_NAME, value='jobs-easy-apply-form-section__grouping')
  for qGroup in qGroups:
    if(len(qGroup.find_elements(by=By.TAG_NAME, value="fieldset"))):
      input("Fieldset has to be filled Manually.\nPress 1 after you have filled the fieldset: ")
    else:
      curLabelText = qGroup.find_element(by=By.CSS_SELECTOR, value="label").get_attribute("innerText")
      if(curLabelText not in qaDict.keys()):
        qaDict[curLabelText] = input("No pre-saved answer for:\n{}\nEnter Ans: ".format(curLabelText))
      curInp = qGroup.find_element(by=By.CSS_SELECTOR, value="input, select")
      curInp.send_keys(Keys.CONTROL,"a")
      curInp.send_keys(Keys.DELETE)
      curInp.send_keys(qaDict[curLabelText])
      
if __name__ == "__main__":

  file = open(DIR_PATH + "/qa.json")
  qaDict = json.load(file)
  file.close()

  try:
    driver = initDriver(False)
    doSignInStuff(driver)
    for keyword in KEYWORD_LIST:
      doJobSearch(keyword)
  except:
    print(traceback.format_exc())
    input("Press any key to quit: ")  
  else:
    driver.quit()

  file = open(DIR_PATH + "/qa.json","w")
  json.dump(qaDict, file) 
  file.close()


  