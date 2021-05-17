#!/usr/bin/env python

import datetime
from multiprocessing import cpu_count, Pool
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

import config


def process(person):
    print(f'Booking for {person[0]}...')

    if times:
        book(person, times)
    else:
        book(person)


def submitted(driver, person):
    if driver.find_elements_by_xpath('//*[@id="gform_submit_button_68"]'):
        print(f'\n{person[0]}', end=': ')

        if driver.find_elements_by_css_selector('div[class="validation_error"]'):
            print('Cannot book twice')
        else:
            print('Successful booking')

        return True
    else:
        return False


def book(data, time_slot=['4:00 PM', '4:30 PM']):
    options = Options()
    options.headless = True
    fp = webdriver.FirefoxProfile()
    path = config.path

    with webdriver.Firefox(executable_path=path, firefox_profile=fp, options=options) as driver:
        driver.get('https://forms.isyedu.org/fitness-gym-weight-room-sign-up/')

        try:
            driver.find_element_by_xpath('//*[@id="input_68_9_3"]').send_keys(data[0])

            driver.find_element_by_xpath('//*[@id="input_68_9_6"]').send_keys(data[1])

            driver.find_element_by_xpath('//*[@id="input_68_10"]').send_keys(data[2])

            driver.find_element_by_xpath('//*[@id="choice_68_13_1"]').click()

            value = '1607' if data[0] == config.family[-1][0] else '798'
            Select(driver.find_element_by_xpath('//*[@id="input_68_7"]')).select_by_value(value)

            today = datetime.date.today()
            WebDriverWait(driver, 20).until(EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, 'div[class="ga_monthly_schedule_wrapper ga_spinner"]')))

            driver.find_element_by_css_selector(f'td[date-go="{today.strftime("%Y-%m-%d")}"]').click()
            time.sleep(1)

            slot = f'{today.strftime("%A, %B %d %Y")} at '
            cnt = 0

            print('')

            for t in time_slot:
                el = driver.find_elements_by_css_selector(f'label[lang_slot="{slot + t}"]')
                print(f'{data[0]}: {t}', end=' ')

                if el:
                    driver.execute_script("arguments[0].click();", el[0])

                    if driver.find_elements_by_xpath('//*[@id="ga_selected_bookings"]/div'):
                        print('has been selected')
                    else:
                        cnt += 1
                        print('is unavailable')
                else:
                    cnt += 1
                    print('is unavailable')

            if cnt == len(time_slot):
                print(data[0], ': Could not book because both requested timeslots are unavailable')
                return

            driver.find_element_by_xpath('//*[@id="gform_submit_button_68"]').click()

            # wait for confirmation
            while not submitted(driver, data):
                pass

        except Exception as e:
            print(data[0], ': Could not book because:')
            print(e)


start_time = time.time()

going = config.family

times = []

print("\nISY GYM BOOKER")

dont_book = [x.capitalize() for x in input("\nIs anyone not going today?\n").split()]

print('\nWhen do you want to go? Enter 1 time slot at a time or leave blank for default 4:00 PM and 4:30 PM.')

for _ in range(2):
    a = input()
    if a == '':
        break
    else:
        times.append(a)

going = [x for x in going if x[0] not in dont_book]

pool = Pool(cpu_count() - 1)
pool.map(process, going)
pool.close()
pool.join()

print("\nCompleted all bookings in", int(time.time() - start_time + 0.5), "seconds.\n")
