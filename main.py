#!/usr/bin/env python

from datetime import datetime, date, timedelta
from time import time
from multiprocessing import Pool
from multiprocessing import Lock
import enquiries

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

import config


def process(person):
    print_lock.acquire()
    print(f'\nBooking for {person[0]}...')
    print_lock.release()

    if times:
        book(person, times)
    else:
        book(person, ['4:00 PM', '4:30 PM'])


def book(data, time_slot):
    options = Options()
    options.headless = True
    fp = webdriver.FirefoxProfile()

    with webdriver.Firefox(executable_path=config.driver_path, firefox_profile=fp, options=options) as driver:
        driver.get('https://forms.isyedu.org/fitness-gym-weight-room-sign-up/')

        try:
            driver.find_element_by_xpath('//*[@id="input_68_9_3"]').send_keys(data[0])

            driver.find_element_by_xpath('//*[@id="input_68_9_6"]').send_keys(data[1])

            driver.find_element_by_xpath('//*[@id="input_68_10"]').send_keys(data[2])

            driver.find_element_by_xpath('//*[@id="choice_68_13_1"]').click()

            value = '1607' if data[0] == config.family[-1][0] else '798'
            Select(driver.find_element_by_xpath('//*[@id="input_68_7"]')).select_by_value(value)

            WebDriverWait(driver, 100).until(EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, 'div[class="ga_monthly_schedule_wrapper ga_spinner"]')))

            driver.find_element_by_css_selector(f'td[date-go="{book_date.strftime("%Y-%m-%-d")}"]').click()
            WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.CLASS_NAME, 'slots-title')))

            slot = f'{book_date.strftime("%A, %B %-d %Y")} at '
            cnt = 0

            for t in time_slot:
                el = driver.find_elements_by_css_selector(f'label[lang_slot="{slot + t}"]')

                if el:
                    driver.execute_script("arguments[0].click();", el[0])
                else:
                    cnt += 1

            l = len(time_slot)

            if cnt == l:
                print(f'\n{data[0]}: Could not book because ' + ('both' if l == 2 else 'the') +
                      ' requested timeslot' + ('s are' if l == 2 else ' is') + ' unavailable')
                return

            driver.find_element_by_xpath('//*[@id="gform_submit_button_68"]').click()

            # wait for confirmation
            while driver.find_elements_by_xpath('//*[@id="gform_submit_button_68"]'):
                pass

            while not driver.find_elements_by_xpath('//*[@id="post-1608"]/div/div/div[1]/div/h1'):
                pass

            print(f'\n{data[0]}', end=': ')

            if driver.find_elements_by_id('gform_confirmation_message_68'):
                print('Successful booking')
            else:
                print('Cannot book twice')

        except TimeoutException:
            print(f'\n{data[0]}: Timeout')


print("\nISY GYM BOOKER")

dont_book = [x.capitalize() for x in input("\nIs anyone not going today?\n").split()]

going = config.family
going = [x for x in going if x[0] not in dont_book]

if dont_book:
    print()

options = ['Today', 'Tomorrow']
when = enquiries.choose('Pick one', options)
print("\nBooking for", end=' ')

if when == 'Today':
    when = 0
    print("today")
else:
    when = 1
    print("tomorrow")

book_date = date.today() + timedelta(days=when)

print('\nEnter time or leave blank for default 4:00 PM - 4:30 PM.')

times = []
a = input()
if a != '':
    # book 2 consecutive timeslots - 1 hour in total
    times = [a, (datetime.strptime(a, '%I:%M %p') + timedelta(minutes=30)).strftime('%-I:%M %p')]

print_lock = Lock()
start_time = time()

pool = Pool(len(going))
pool.map(process, going)
pool.close()
pool.join()

runtime = str(round(time() - start_time))

print("\nCompleted all bookings in", runtime, "seconds.\n")
