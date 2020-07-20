from selenium import webdriver
from selenium.common.exceptions import *
import pandas as pd
import re
import time
from selenium.webdriver.chrome.options import Options
import multiprocessing
import random

'''
Scrapes the DOCCS inmate lookup, given a list of DINS. Outputs a csv of the information gathered, each row being one 
individual. If they were incarcerated multiple times, there is a different row for each commitment. 

Before running for the first time:
 - Update Chrome and install ChromeDriver, replacing the executable path with your own Chromedriver path.
 - Install all packages listed.
 - Replace the self.dins instantiation in the MultiProcess class to your own list of dins.
 - Uncomment the to_csv statement at the bottom and write in your own csv you'd like the information to be stored in.

** The batch size is set for the test data as default, for a large dataset, set it to 100. ** 

To make sure it's functioning correctly, 
 - set self.dins to be:
[   '00A0094',
    '00A0476',
    '00A0531',
    '00A0593',
    '00A0774',
    '18A3699',
    '17R2700',
    '00A0786',
    '00A1123',
    '00A1244',
    '00A1268']

 - Uncomment the test phrase at the bottom. 

The output should be "The DIN 17R2700 is not present in the DOCCS database." 
Followed by a dataframe containing 12 rows, with each row being a DIN and the columns being the information gathered 
from the scrape. 

'''


# This class instantiates the driver and creates a parser
class Parser:
    def __init__(self):
        self.mydriver = self.get_driver()

    # Instantiates the web driver and returns it
    def get_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")

        # Instantiate this driver with your own executable path.
        mydriver = webdriver.Chrome(executable_path="/Users/rileyneher/PycharmProjects/CANY/chromedriver",
            options=chrome_options)

        return mydriver

    # Parses the tables in the DOCCS lookup page and returns a dataframe containing the information
    def parse_page(self):

        tables = self.mydriver.find_elements_by_tag_name('table')

        # Goes through the general information table
        rows = tables[0].find_elements_by_tag_name('tr')
        rows = map(lambda x: x.find_elements_by_tag_name('td')[1], rows)
        rows = map(lambda x: x.get_attribute('innerText').strip(), rows)
        cols = ['din', 'Name', 'Gender', 'DOB',
                'Eth', 'CustStat', 'FacString', 'FIncar',
                'CurFincar', 'AdmitType', 'County', 'Latest_Release_Date']

        # Stores the information in a dictionary
        info = dict(zip(cols, rows))

        # Splits data into date format
        try:
            date_type = info['Latest_Release_Date']
            date = re.search(r'[0-9]+/[0-9]+/[0-9]+', date_type)[0]
            release_type = re.split(r'[0-9]+/[0-9]+/[0-9]+', date_type)[-1]
            info['Latest_Release_Date'] = date
            info['Release_Type'] = release_type.strip()

        except TypeError:
            info['Release_Type'] = ''

        # Find the charges and classes
        rows = tables[1].find_elements_by_tag_name('tr')[1:]
        rows = filter(lambda x: x.find_elements_by_tag_name('td')[0]. \
                      get_attribute('innerText').strip() != '', rows)
        rows = [map(lambda x: x.get_attribute('innerText').strip(), \
                    row.find_elements_by_tag_name('td')) for row in rows]

        # Store the charges and classes
        cols = ['Crime', 'Class']
        charges = [dict(zip(cols, row)) for row in rows]

        # Stores the sentencing information
        rows = tables[2].find_elements_by_tag_name('tr')
        rows = list(map(lambda x: x.find_elements_by_tag_name('td'), rows))
        cols = list(map(lambda x: x[0].text.replace(' ', '_'), rows))
        values = list(map(lambda x: x[1].get_attribute('innerText').strip(), rows))
        sentence = dict(zip(cols, values))

        # Aggregates the information and stores it in a dataframe
        info['Charges'] = charges
        info.update(sentence)

        return pd.DataFrame(info)


# Scrapes the DOCCS website and returns a dataframe of information found.
def scrape(din):

    parse = Parser()

    # Inputs the din into the search
    parse.mydriver.get('http://nysdoccslookup.doccs.ny.gov')
    parse.mydriver.find_element_by_id('M00_DIN_FLD1I').send_keys(din[:2])
    parse.mydriver.find_element_by_id('M00_DIN_FLD2I').send_keys(din[2])
    parse.mydriver.find_element_by_id('M00_DIN_FLD3I').send_keys(din[3:7])

    myButtonsList = parse.mydriver.find_elements_by_xpath("//div[contains(concat(' ',@class,' '),' aligncenter  ')]")
    myButtons=myButtonsList[0]
    submit=myButtons.find_element_by_xpath("//input[@type='submit']")
    submit.click()

    num = random.randint(1,5)

    time.sleep(num)

    multi_commit = True

    # Instantiates the dataframe
    info = pd.DataFrame(columns = ['din', 'Name', 'Gender', 'DOB',
                                    'Eth', 'CustStat', 'FacString', 'FIncar',
                                    'CurFincar', 'AdmitType', 'County', 'Latest_Release_Date',
                                    'Release_Type', 'Charges', 'Aggregate_Minimum_Sentence',
                                    'Aggregate_Maximum_Sentence', 'Earliest_Release_Date', 'Earliest_Release_Type',
                                    'Parole_Hearing_Date', 'Parole_Hearing_Type', 'Parole_Eligibility_Date',
                                    'Conditional_Release_Date', 'Maximum_Expiration_Date', 'Maximum_Expiration_Date_for_Parole_Supervision',
                                    'Post_Release_Supervison_Maximum_Expiration_Date', 'Parole_Board_Discharge_Date'])

    # Catches if the DIN is not present in the database
    try:
        parse.mydriver.find_element_by_xpath('//*[@id="il"]/p[3]')
        print(format(f"The DIN {din} is not present in the DOCCS database."))
        return None

    except NoSuchElementException:

        # Checks if there are multiple commitments for the din
        try:
            parse.mydriver.find_element_by_xpath('//*[@id="content"]/h3[2]')
        except NoSuchElementException:
            multi_commit = False

        # If there are multiple commitments, store them as different rows of the dataframe
        if multi_commit == True:
            inmate_numbers = [x.get_attribute('value') for x in parse.mydriver.find_elements_by_class_name('buttolink')]

            for x in inmate_numbers:
                if x != '':
                    ind = inmate_numbers.index(x)
                    form = parse.mydriver.find_elements_by_class_name('buttolink')[ind]

                    # go to the record
                    form.submit()
                    time.sleep(num)
                    record = parse.parse_page()
                    info = info.append(record, ignore_index=True)
                    parse.mydriver.back()

            info.drop_duplicates(subset=['din'], inplace=True, ignore_index=True)

        elif multi_commit == False:
            info = parse.parse_page().iloc[0]

    parse.mydriver.close()
    parse.mydriver.quit()

    return info


# A class that performs the multiprocess with batching
class MultiProcess:

    # Initiates the pool and dins
    def __init__(self, pool):
        self.pool=pool

        # Replace this list with your own list of dins to be scraped.
        self.dins = \
            [   '00A0094',
                '00A0476',
                '00A0531',
                '00A0593',
                '00A0774',
                '18A3699',
                '17R2700',
                '00A0786',
                '00A1123',
                '00A1244',
                '00A1268']
        self.lst = []

    # Creates the batch system to break up the multiprocess
    def batch(self, iterable, n=1):
        l = len(iterable)
        for ndx in range(0, l, n):
            yield iterable[ndx:min(ndx + n, l)]

    # Returns a dataframe of all the information found in all the dins
    def main(self, df):

        # Change the batch size to 100 if working with a large dataset
        for x in self.batch(self.dins, 5):
            self.lst.append(x)

        for i in self.lst:
            results = self.pool.map(scrape, i)
            time.sleep(10)

            for result in results:
                df = df.append(result, ignore_index=True)


        return df


if __name__ == '__main__':
    df = pd.DataFrame(columns=['din', 'Name', 'Gender', 'DOB',
                               'Eth', 'CustStat', 'FacString', 'FIncar',
                               'CurFincar', 'AdmitType', 'County', 'Latest_Release_Date',
                               'Release_Type', 'Charges', 'Aggregate_Minimum_Sentence',
                               'Aggregate_Maximum_Sentence', 'Earliest_Release_Date',
                               'Earliest_Release_Type',
                               'Parole_Hearing_Date', 'Parole_Hearing_Type', 'Parole_Eligibility_Date',
                               'Conditional_Release_Date', 'Maximum_Expiration_Date',
                               'Maximum_Expiration_Date_for_Parole_Supervision',
                               'Post_Release_Supervison_Maximum_Expiration_Date',
                               'Parole_Board_Discharge_Date'])

    with multiprocessing.Pool(multiprocessing.cpu_count() - 1) as pool:
        table = MultiProcess(pool).main(df)

    # For the test, uncomment the print statement
    print(table)

    # To save the dataframe to a csv, uncomment this statement. 
    #table.to_csv('')

    pool.close()
