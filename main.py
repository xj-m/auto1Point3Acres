from time import sleep
import os
from config import CONFIG_INFO
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common import exceptions as selexception
import platform
import uuid
import json
from loguru import logger
import urllib
import sys
from chrome_driver_manager import ChromeDriverManager

# # NOTE: config loguru
# logger.remove()
# logger.add("info.log", filter=lambda record: record["level"].name == "DEBUG")
# logger.add(sys.stderr, level = 'INFO')
# logger.add("info.log", filter=lambda record: record["level"].name == "INFO")

BBS_ADDRESS, LOCAL_USER_CONFIG_FILE_PATH = [
    CONFIG_INFO[k] for k in ('BBS_ADDRESS', 'LOCAL_USER_CONFIG_FILE_PATH')]


def get_chrome_driver():
    # * init webdriver, using chrome
    # 设置为执行操作时，不需要等待页面完全加载
    caps = DesiredCapabilities().CHROME
    caps["pageLoadStrategy"] = "none"
    chrome_driver = Chrome(desired_capabilities=caps)
    chrome_driver.get(BBS_ADDRESS)
    chrome_driver.maximize_window()
    webdriver_wait = WebDriverWait(chrome_driver, 3)
    return chrome_driver, webdriver_wait


driver, wait = get_chrome_driver()
driver_manager = ChromeDriverManager(driver, wait, logger)


def get_user_config():
    # * get credential info locally or from cloud
    logger.debug(f"Started to get username and password")
    username, password = None, None
    if "USERNAME" in os.environ:
        logger.info("Load user account info from heroku config")
        [username, password] = [os.environ.get(
            "USERNAME"), os.environ.get("PASSWORD")]
    else:
        logger.info("Get user account info from local file")
        with open(LOCAL_USER_CONFIG_FILE_PATH) as config:
            user_config = json.load(config)
            [username, password] = [user_config["USERNAME"], user_config["PASSWORD"]]
    logger.info(f"username:{username}, password:{password}")
    return [username, password]


def driver_login_1p3a(username, password):
    logger.info("started to login")
    # 1. fill in username
    logger.debug(f'start fill in username: f{username}')
    login_btn_element = wait.until(
        ec.presence_of_element_located((By.XPATH, "//em[text()='登录']")))
    usr_name_element = driver_manager.driver.find_element_by_css_selector(
        "input[id='ls_username']")
    usr_name_element.send_keys(username)
    # 2. fill in password
    logger.debug(f'start to fill in password: f{password}')
    pwd_element = driver_manager.driver.find_element_by_css_selector(
        "input[id='ls_password']")
    pwd_element.send_keys(password)
    # 3. click login btn
    login_btn_element.click()
    # 4. check if login success
    wait.until(ec.presence_of_element_located((By.XPATH, '//a[text()="退出"]')))
    logger.info("Login success!")


def get_1p3a_daily_award():
    # NOTE: use chrome to find element by xpath: `$x('PATH')`
    logger.info("start to get daily award")
    # 1. click "签到领奖"
    logger.debug("start to click 签到领奖")
    try:
        driver_manager.find_and_click_by_xpath("//font[text()='签到领奖!']")
    except selexception.NoSuchElementException as e:
        # * already done
        return

    # TODO: add multiple attemptation support
    # for trial in range(15):
    #     if res_text == "" or res_text != correct_res:
    # driver_manager.find_element_by_xpath(
    #     "//input[@name='seccodeverify']").send_keys(result_str)
    # result_indicator_image_element = driver.find_element_by_xpath(
    #     "//span[@id='checkseccodeverify_SA00']//img")
    # res_text = result_indicator_image_element.get_attribute("src")

    def crack():

        # 2. click to select “开心”
        logger.debug("start to select 心情")
        driver_manager.find_and_click_by_xpath('//*[@id="kx"]/center/img')

        # 3. click to use “快速留言”
        logger.debug("start to click 选择快速留言")
        find_and_click_by_xpath(
            driver, wait, '//*[@id="ct"]/div[1]/div[1]/form/table[2]/tbody/tr[1]/td/label[2]')
        # * crack captcha and click submit
        logger.debug("start to crack captcha and click submit")
        # 1. change capcha
        driver_manager.find_and_click_by_xpath("//a[text()='换一个']")
        sleep(5)
        # 2. get result
        result_str = driver_manager.get_cracked_string_by_xpath(
            '//*[@id="seccode_S00"]/img')
        # 3. fill in result
        driver_manager.driver.find_element_by_xpath(
            '//*[@id="seccodeverify_S00"]').send_keys(result_str)
        # 4. click submit
        driver_manager.find_and_click_by_xpath(
            '//*[@id="ct"]/div[1]/div[1]/form/table[4]/tbody/tr/td/div/input')

    for i in range(30):
        crack()
        sleep(5)
        try:
            element = driver_manager.driver.find_element_by_xpath(
                '//*[@id="seccodeverify_S00"]')
        except elenium.common.exceptions.NoSuchElementException as e:
            break

    # 等待签到框消失
    # wait.until(ec.invisibility_of_element_located((By.XPATH, "//div[@id='fwin_dsu_paulsign']")))

    # 等待 “签到领奖！” 链接消失
    # wait.until(ec.invisibility_of_element_located((By.XPATH, "//font[text()='签到领奖!']")))
    sleep(3)

    logger.info("Getting daily award successfully completed")


def get_answer(question):

    # 检查题库
    logger.debug(f"开始检索题库, 题目: {question}")
    with open("question_list.json") as f:
        q_dict = json.load(f)

    try:
        return q_dict[question]
    except KeyError:
        return ""


def get_1p3a_daily_question(browser, wait):
    logger.debug("开始每日答题")

    try:
        browser.find_element_by_xpath(
            "//img[@src='source/plugin/ahome_dayquestion/images/end.gif']")
        logger.debug("今天已经回答过啦！!")
        return
    except selexception.NoSuchElementException:
        pass

    # 等待 “开始答题” 或者 ”答题中“ 图标
    two_icons = "img[src='source/plugin/ahome_dayquestion/images/ing.gif'], img[src='source/plugin/ahome_dayquestion/images/start.gif']"
    # daily_q_element = wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, two_icons)))
    sleep(4)
    daily_q_element = browser.find_element_by_css_selector(two_icons)

    # 每日答题
    browser.execute_script("arguments[0].click();", daily_q_element)
    # daily_q_element.click()

    # 填写验证码
    fill_captcha(browser, wait)

    # 获取问题和答案
    question = browser.find_element_by_xpath("//b[text()='【题目】']/..").text[5:]
    answer = get_answer(question)

    if answer == "":
        logger.debug("今日问题未被收录入题库，跳过每日问答")
        return
    elif type(answer) is list:
        answer_set = set(answer)
    else:
        answer_set = set([answer])

    # 提交答案

    answer = "this make no sense"

    options_list = browser.find_elements_by_xpath("//div[@class='qs_option']")

    for e in options_list:
        potential_ans = e.text.strip()
        if potential_ans in answer_set:
            answer = potential_ans
            choose_btn = browser.find_element_by_xpath(
                f"//div[text()='  {answer}']/input")
            choose_btn.click()

    if answer == "this make no sense":
        logger.debug("题库答案过期，跳过每日问答！")
        return
    else:
        logger.debug(f"答案: {answer}")

    ans_btn = browser.find_element_by_xpath(
        "//button[@name='submit'][@type='submit']")
    browser.execute_script("arguments[0].click();", ans_btn)
    logger.debug("完成每日问答，大米+1")


def find_and_click_by_xpath(driver, wait, xpath):
    element = wait.until(
        ec.presence_of_element_located((By.XPATH, xpath)))
    driver.execute_script("arguments[0].click();", element)


def fill_captcha(driver, wait):

    res_text = ""
    correct_res = "https://www.1point3acres.com/bbs/static/image/common/check_right.gif"
    wrong_res = "https://www.1point3acres.com/bbs/static/image/common/check_error.gif"

    sleep(4)
    # cap_input_element = wait.until(ec.visibility_of_element_located((By.XPATH, "//input[@name='seccodeverify']")))
    cap_input_element = driver.find_element_by_xpath(
        "//input[@name='seccodeverify']")
    trial = 1

    while res_text == "" or res_text != correct_res:  # 验证码解码错误

        if trial >= 20:
            return

        logger.debug(f"开始破解图形验证码，第{trial}次尝试...")
        # 重新获取验证码

        sleep(3)
        # get_new_captcha = wait.until(ec.visibility_of_element_located((By.XPATH, "//a[text()='换一个']")))
        find_and_click_by_xpath("//a[text()='换一个']")

        sleep(3)
        # captcha_img_element = wait.until(ec.visibility_of_element_located((By.XPATH, "//span[text()='输入下图中的字符']//img")))
        captcha_img_element = driver.find_element_by_xpath(
            '//*[@id="seccode_S00"]/img')
        # src = captcha_img_element.get_attribute("src")

        # NOTE: for whole screen
        # driver.save_screenshot('screenshot.png')
        # * capture img
        # loc = captcha_img_element.location
        # size = captcha_img_element.size
        # left, right = loc['x'], loc['x'] + size['width']
        # top, bottom = loc['y'], loc['y'] + size['height']
        # captcha_img = scrsht.crop((left, top, right, bottom))
        # captcha_img.save("captcha.png")

        # * test
        captcha_img = cap_input_element.screenshot_as_png
        with open("captcha.png", "wb") as f:
            f.write(captcha_img_element.screenshot_as_png)

        # * image -> captcha
        captcha_text = captcha.captcha_to_string(Image.open("captcha.png"))
        logger.debug(f"图形验证码破解结果: {captcha_text}")

        cap_input_element.send_keys(captcha_text)

        # 选择答案以激活正确或错误图标
        answer_element = driver.find_element_by_xpath(
            "//input[@name='answer'][@value='1']")
        answer_element.click()

        # 等待错误或正确图标出现，为的是检验刚才输入的验证码是否正确
        # wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "img[src='static/image/common/check_right.gif'], img[src='static/image/common/check_error.gif']")) )
        sleep(4)

        check_image_element = driver.find_element_by_xpath(
            "//span[@id='checkseccodeverify_SA00']//img")
        res_text = check_image_element.get_attribute("src")
        print(res_text)

        if res_text == correct_res:
            logger.debug("验证码输入正确 ^_^ ")
        else:
            logger.debug("验证码输入错误！")
            trial += 1


@ logger.catch
def main():
    task2status = {task: False for task in [
        "login", "daily_award", "daily_question"]}
    try:
        username, password = get_user_config()
        driver_login_1p3a(username, password)
        task2status['login'] = True
        get_1p3a_daily_award()
        task2status['daily_award'] = True
        get_1p3a_daily_question()
        task2status["daily_question"] = True
    except selexception.TimeoutException:
        logger.error(
            "Failed to login, may caused by incorrect username and password")
    except selexception.NoSuchElementException:
        logger.info(f"Already got daily award")
    except Exception:
        logger.debug("Unexpected exception")
    finally:
        info = "\t".join(
            f"{task} {'succeeded' if status else 'failed'}" for task, status in task2status)
        logger.info(info)
        driver_manager.driver.quit()
        exit(0)


if __name__ == "__main__":
    main()
