# DOCCS-Scraper
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
