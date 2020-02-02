from time import sleep
import os
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common import exceptions as selexception
from PIL import Image
import platform
import uuid
import captcha
import json
from loguru import logger
import urllib
import sys

# # NOTE: set logger
# logger.remove()
# logger.add("info.log", filter=lambda record: record["level"].name == "DEBUG")
# logger.add(sys.stderr, level = 'INFO')
# logger.add("info.log", filter=lambda record: record["level"].name == "INFO")

# passed info
passed = [False for _ in range(3)]

# 初始化 webdriver, 使用chrome浏览器
# 设置为执行操作时，不需要等待页面完全加载
caps = DesiredCapabilities().CHROME
caps["pageLoadStrategy"] = "none"
browser = Chrome(desired_capabilities=caps)
browser.get("https://www.1point3acres.com/bbs/")
browser.maximize_window()
wait = WebDriverWait(browser, 3)

def login(browser, wait):
    # * read user name and password from local json
    # if platform.system() == "Darwin" and hex(uuid.getnode()) == "0x3035add3a8d0":
    #     conf_file = "dev-username.json"
    # else:
    #     conf_file = "username.json"

    # logger.debug("从配置文件中获取用户名和密码...")
    # with open(conf_file) as config:
    #     usr_pwd = json.load(config)
    # usr_name = usr_pwd["username"]
    # password = usr_pwd["password"]
    # usr_name = usr_pwd["usernameL"]
    # password = usr_pwd["passwordL"]

    usr_name = os.environ.get("USERNAME")
    password = os.environ.get("PASSWORD")

    logger.debug("开始登录一亩三分地, 账号:" + usr_name)

    # 登录
    login_btn_element = wait.until(ec.presence_of_element_located((By.XPATH, "//em[text()='登录']")))
    usr_name_element = browser.find_element_by_css_selector("input[id='ls_username']")
    usr_name_element.send_keys(usr_name)

    pwd_element = browser.find_element_by_css_selector("input[id='ls_password']")
    pwd_element.send_keys(password)

    login_btn_element.click()

    wait.until(ec.presence_of_element_located((By.XPATH, '//a[text()="退出"]')))

    logger.debug("登录成功!")
    passed[0] = True

def daily_check_in(browser, wait):
    logger.debug("开始每日签到")

    # 每日签到
    logger.debug("点击签到按钮")
    check_element = browser.find_element_by_xpath("//font[text()='签到领奖!']")
    # check_element.click()
    browser.execute_script("arguments[0].click();", check_element)

    # 自动选择表情：“开心”
    logger.debug("选择心情——开心")
    happy_element = wait.until(ec.presence_of_element_located((By.XPATH, '//li[@id="kx"]')))
    browser.execute_script("arguments[0].click();", happy_element)
    # happy_element.click()

    # 使用快速选择留言
    logger.debug("选择快速留言")
    say_element = browser.find_element_by_xpath("//input[@name='qdmode'][@value='2']")
    browser.execute_script("arguments[0].click();", say_element)
    # say_element.click()

    # 点击签到
    logger.debug("点击签到")
    check_btn_element = browser.find_element_by_xpath("//strong[text()='点我签到!']/..")
    browser.execute_script("arguments[0].click();", check_btn_element)
    # check_btn_element.click()

    # 等待签到框消失
    # wait.until(ec.invisibility_of_element_located((By.XPATH, "//div[@id='fwin_dsu_paulsign']")))

    # 等待 “签到领奖！” 链接消失
    # wait.until(ec.invisibility_of_element_located((By.XPATH, "//font[text()='签到领奖!']")))
    sleep(3)

    logger.debug("签到完成，大米+1")
    passed[1] = True
    return 1

def get_answer(question):

    # 检查题库
    logger.debug(f"开始检索题库, 题目: {question}")
    with open("question_list.json") as f:
        q_dict = json.load(f)
    
    try:
        return q_dict[question]
    except KeyError:
        return ""

def daily_question(browser, wait):
    logger.debug("开始每日答题")

    try:
        browser.find_element_by_xpath("//img[@src='source/plugin/ahome_dayquestion/images/end.gif']")
        logger.debug("今天已经回答过啦！!")
        passed[2] = True
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
            choose_btn = browser.find_element_by_xpath(f"//div[text()='  {answer}']/input")
            choose_btn.click()

    if answer == "this make no sense":
        logger.debug("题库答案过期，跳过每日问答！")
        return
    else:
        logger.debug(f"答案: {answer}")

    ans_btn = browser.find_element_by_xpath("//button[@name='submit'][@type='submit']")
    browser.execute_script("arguments[0].click();", ans_btn)
    logger.debug("完成每日问答，大米+1")
    passed[2] = True

def fill_captcha(browser, wait):

    res_text = ""
    correct_res = "https://www.1point3acres.com/bbs/static/image/common/check_right.gif"
    wrong_res = "https://www.1point3acres.com/bbs/static/image/common/check_error.gif"

    sleep(4)
    # cap_input_element = wait.until(ec.visibility_of_element_located((By.XPATH, "//input[@name='seccodeverify']")))
    cap_input_element = browser.find_element_by_xpath("//input[@name='seccodeverify']")
    trial = 1

    while res_text == "" or res_text != correct_res: # 验证码解码错误

        if trial >= 20:
            return

        logger.debug(f"开始破解图形验证码，第{trial}次尝试...")
        # 重新获取验证码

        sleep(3)
        # get_new_captcha = wait.until(ec.visibility_of_element_located((By.XPATH, "//a[text()='换一个']")))
        get_new_captcha = browser.find_element_by_xpath("//a[text()='换一个']")
        browser.execute_script("arguments[0].click();", get_new_captcha)

        sleep(3)
        # captcha_img_element = wait.until(ec.visibility_of_element_located((By.XPATH, "//span[text()='输入下图中的字符']//img")))
        captcha_img_element = browser.find_element_by_xpath("//span[text()='输入下图中的字符']//img")
        # src = captcha_img_element.get_attribute("src")

        browser.save_screenshot('screenshot.png')
        scrsht = Image.open("screenshot.png")


        # * capture img
        # loc = captcha_img_element.location
        # size = captcha_img_element.size
        # left, right = loc['x'], loc['x'] + size['width']
        # top, bottom = loc['y'], loc['y'] + size['height']
        # captcha_img = scrsht.crop((left, top, right, bottom))
        # captcha_img.save("captcha.png")

        # * test
        captcha_img = cap_input_element.screenshot_as_png
        with open ("captcha.png", "wb") as f:
            f.write(captcha_img_element.screenshot_as_png)

        # * image -> captcha
        captcha_text = captcha.captcha_to_string(Image.open("captcha.png"))
        logger.debug(f"图形验证码破解结果: {captcha_text}")

        cap_input_element.send_keys(captcha_text)

        # 选择答案以激活正确或错误图标
        answer_element = browser.find_element_by_xpath("//input[@name='answer'][@value='1']")
        answer_element.click()

        # 等待错误或正确图标出现，为的是检验刚才输入的验证码是否正确
        # wait.until(ec.presence_of_element_located((By.CSS_SELECTOR, "img[src='static/image/common/check_right.gif'], img[src='static/image/common/check_error.gif']")) )
        sleep(4)

        check_image_element = browser.find_element_by_xpath("//span[@id='checkseccodeverify_SA00']//img")
        res_text = check_image_element.get_attribute("src")
        print(res_text)

        if res_text == correct_res:
            logger.debug("验证码输入正确 ^_^ ")
        else:
            logger.debug("验证码输入错误！")
            trial += 1

def end():
    # write in log file
    info = ""
    for i, s in enumerate(["登陆","签到","答题"]):
        info += "\t" + s + ("成功" if passed[i] else "失败")
    logger.info(str(os.environ.get("USERNAME"))+info)
    logger.debug("=".center(50,"="))

    # exit
    browser.quit()
    exit(0)

@logger.catch
def start():
    for _ in range(1):
        # 执行登录，在做任何其他操作前必须先登录
        try:
            login(browser, wait)
        except selexception.TimeoutException:
            msg = "登陆失败, 可能是用户名密码不正确导致"
            logger.debug(msg)
            break
        except:
            msg = "Unexpected issue"
            logger.debug(msg)
            break

        # 每日签到
        try:
            daily_check_in(browser, wait)
        except selexception.NoSuchElementException:
            logger.debug("今天已经签过啦！!")
            passed[1] = True

        # 每日答题
        daily_question(browser, wait)

    end()

"""
========================= START =============================
"""
start()