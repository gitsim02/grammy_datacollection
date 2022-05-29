# packages
from urllib.request import urlopen, Request
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import re
import time
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# import Action chains 
from selenium.webdriver.common.action_chains import ActionChains

import warnings
import logging

warnings.filterwarnings('ignore')

logging.basicConfig(
    filename='grammy_run.log', filemode='w',
    format='%(asctime)s %(levelname)s:%(message)s',
    level=logging.INFO)

# seed urls, webdriver location for Selenium,
webdriver_location = r"msedgedriver.exe"

seed_url = ['https://www.grammy.com/awards',
            'https://en.wikipedia.org/wiki/List_of_Grammy_Award_ceremony_locations',
            'https://www.latingrammy.com/en/nominees/search?page=1',
            'https://en.wikipedia.org/wiki/List_of_Latin_Grammy_Award_ceremony_locations']


def expand_page(webdriver_loc, url, element_identifier):
    '''
    this function clicks on "show more" button of Grammy Seed Url
    & returns complete html.
    Accepts webdriver location, url, html element complete xpath;
    Returns error and html string
    '''
    try:
        # instantiate & open webdriver browser 
        browser = webdriver.Edge(webdriver_location)
        # get the url
        browser.get(url)

        # create action chain object
        action = ActionChains(browser)
        for i in range(0, 18):

            # wait 10 seconds until element located
            element = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.XPATH, element_identifier)))

            if element:
                # perform click action
                action.click(on_element=element)
                action.perform()
                time.sleep(7)
            else:
                break

    except Exception as e:
        return (f"Exception occured : {e}", "")

    finally:
        html = browser.execute_script('return document.body.innerHTML;')
        #         print(html)
        browser.quit()

    return ("", html)


def get_html_selenium(webdriver_loc, url, isLatin=False):
    '''
    this function returns html for a specific url. 
    If the Url is for Latin Grammy, 
    this will scroll the webpage to get to the end and return html.
    Accepts webdriver location, url, isLatin boolean;
    Returns error and html string
    '''
    try:
        # instantiate & open webdriver browser 
        browser = webdriver.Edge(webdriver_location)

        if isLatin:
            browser.get(url)

            SCROLL_PAUSE_TIME = 0.5

            # scroll for 50 times
            for i in range(0, 50):
                # Scroll down to bottom
                browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                # Wait to load page
                time.sleep(SCROLL_PAUSE_TIME)

                if i == 49:
                    return ("", browser.execute_script("return document.body.innerHTML;"))

        else:
            # get the url
            browser.get(url)
            html = browser.execute_script('return document.body.innerHTML;')
            time.sleep(5)
            return ("", html)

    except Exception as e:
        return (f"Exception occured : {e}", "")


def invoke_selenium(webdriver_loc, url, element_identifier=None):
    '''
    This function is a driver function to get html by further calling custom function based on URL.
    Accepts webdriver location, url, html element complete xpath;
    Returns error and html string
    '''

    if re.search(r'(grammy.com/awards)', str(url)):

        # individual grammy award page link
        if len(str(url).split("awards")) > 2:
            error, html = get_html_selenium(webdriver_loc, url)
            return (error, html)

        # grammy awards crawler page
        else:
            error, html = expand_page(webdriver_location, url, element_identifier)
            return (error, html)

    else:
        error, html = get_html_selenium(webdriver_loc, url, isLatin=True)
        return (error, html)


def crawl_grammy_links(webdriver_loc, url):
    '''
    This functions crwals the seed URL of Grammy Awards page and gets all individual Award Pages' Links
    Accepts webdriver location, url;
    Returns error string and dictionary of links and Grammy award title
    '''
    show_more_xpath = '/html/body/div[2]/div/main/section[3]/section[4]/div/button'

    # get html
    error, html = invoke_selenium(webdriver_location, url, show_more_xpath)

    if error == "":

        soup = BeautifulSoup(html, "html.parser")
        # crawler links class
        crawler_links = soup.find_all('div',
                                      {"class": "max-w-610px w-full md-xl:pt-25px md-xl:pr-20px md-xl:pl-5px relative"})
        grammy_links = {}

        for row in crawler_links:
            div = row.find('div',
                           {"class": "mb-20px md-xl:mb-30px text-center md-xl:text-left leading-7"})

            if div:
                # create grammy_links dictionary
                grammy_links[div.a.text.replace('..', '')] = urljoin(url, div.a["href"])
                div = None

        return ("", grammy_links)

    else:
        return (error, "")


def get_text(tag):
    '''
    This functions returns text for a tag
    '''
    if tag:
        text = tag.get_text()
        if text and text != '':
            return text
        else:
            return "NA"
    else:
        return "NA"


def scraper_grammy(soup, key):
    '''
    This function scrapes and returns data points for Grammy Awards.
    Accepts bs4 object, key( Grammy Award Title)
    Returns a list of list
    '''
    dataset = []

    pg_heading = soup.find('h1',
                           {
                               "class": 'text-grammy-gold font-polaris uppercase text-30 md-xl:text-42 font-thin leading-tight mb-25px'})

    year = get_text(pg_heading).split()[0]

    title = key

    for section in soup.find_all('section', {"class": "h-full w-full flex flex-col items-center mt-6 md-xl:mt-8"}):

        category_div = section.find('div', {
            "class": "w-full text-left md-xl:text-right mb-1 md-xl:mb-20px text-14 md-xl:text-22 font-polaris uppercase"})
        category = get_text(category_div)

        nom_winner_div = section.find('div',
                                      {
                                          "class": "w-full text-center md-xl:text-left text-17 md-xl:text-22 mr-10px md-xl:mr-30px font-polaris font-bold md-xl:leading-8 tracking-wider"})
        nom_winner = get_text(nom_winner_div)

        artist_div = section.find('div', {"class": "awards-category-link"})
        artist = get_text(artist_div)

        worker_div = section.find('div',
                                  {"class": "mb-15px mt-30px text-left flex"})
        worker = get_text(worker_div)

        # title, year, category, winner, artist, workers, isWinner
        dataset.append([title, year, category, nom_winner, artist, worker, "True"])

        # NOMINEES
        for nom_outer_div in section.find_all('div',
                                              {"class": "pt-15px flex flex-row md-xl:w-710px flex flex-row"}):
            nom_div = nom_outer_div.find('div',
                                         {
                                             "class": "w-full text-left md-xl:text-22 text-17 mr-10px md-xl:mr-30px font-polaris font-bold md-xl:leading-8 tracking-wider flex flex-row justify-between"})
            nom = get_text(nom_div)

            nom_artist_div = nom_outer_div.find('div',
                                                {"class": "awards-nominees-link"})
            nom_artist = get_text(nom_artist_div)

            nom_worker_div = nom_outer_div.find('div',
                                                {"class": "accordion__content"})
            nom_worker = get_text(nom_worker_div)

            # title, year, category, winner, artist, workers, isWinner
            dataset.append([title, year, category, nom, nom_artist, nom_worker, "False"])
            nom, nom_artist, nom_worker = '', '', ''

        category, nom_winner, artist, worker = '', '', '', ''

    return dataset


def scrape_grammy(links, webdriver_loc):
    '''
    This functions loops through all the grammy links and calls the scraper to get the data.
    It creates a dictionary of data frames for each Grammy Award
    Accepts dictionay of Url links, webdriver location;
    Returns error string and dictionay of dataframes
    '''
    df_dic = {}
    headers = ['Title', 'Year', 'Category', 'Nominee', 'Artist', 'Worker', 'isWinner']
    index = 0
    error = ""

    logging.info("Starting to scrape Grammy Awards...")

    for key, value in links.items():
        logging.info(f"fetching for {key}:{value}...")

        # get html
        error, html = invoke_selenium(webdriver_loc, url=value)

        if error == "":
            soup = BeautifulSoup(html, "html.parser")

            # scrape data
            data = scraper_grammy(soup, key)

            # create datafram and save in dictionary
            df_dic[index] = pd.DataFrame(data, columns=headers)

            index = index + 1
            logging.info(f"data frame created for {key}...")
        else:
            break

    return (error, df_dic)


def get_html(url):
    '''
    This function opens a URL and returns the html content 
    '''
    agent = "Mozilla/5.0 (platform; rv:geckoversion) Gecko/geckotrail Firefox/firefoxversion"

    return urlopen(Request(url, headers={'User-Agent': agent})).read()


def scrape_latin_grammy(webdriver_loc, url):
    """
    This function scrapes the historical latin grammy awards winners and created a data frame
    Accepts webdriver location, url;
    Returns error string and data frame
    """
    error, html = invoke_selenium(webdriver_loc, url)

    if error == "":
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find('table')
        return "", pd.DataFrame(pd.read_html(str(table))[0])
    else:
        return error, ""


def get_details(url):
    """
    This function returns Details of each grammy award.
    Returns a datafram object
    """
    soup = BeautifulSoup(get_html(url), 'html.parser', multi_valued_attributes=None)
    table = soup.find('table')
    return pd.DataFrame(pd.read_html(str(table))[0])


def get_artist(x):
    '''
    This function searches for artist in a text and returns the Artist
    '''
    if re.search(r'\bartist\b', str(x)):
        return str(x).split('artist')[0].replace(',', "")
    elif re.search(r'\bartists\b', str(x)):
        return str(x).split('artists')[0].replace(',', "")
    else:
        return "NA"


def remove_brace(rows):
    '''
    This function is to clean the text by removing the brackets
    '''
    data = []
    for ele in rows:
        if re.search(r'\[', str(ele)):
            data.append(str(ele).split("[")[0])
        else:
            data.append(ele)
    return data


#     return [str(ele).split("[")[0] for ele in rows if re.search(r'\[', str(ele) else ele) ]


def create_title(x):
    '''
    This function is to derive the Latin Grammy Title from Year
    '''
    tens = int(x) % 10 + 1
    hundreds = int(x) % 100 + 1
    if tens == 1 and (hundreds == 1 or hundreds == 21):
        end = "st"
    elif tens == 2 and (hundreds == 2 or hundreds == 22):
        end = "nd"
    elif tens == 3 and (hundreds == 3 or hundreds == 23):
        end = "rd"
    else:
        end = "th"
    return str(hundreds) + end + " Annual Latin Grammy Awards"


def clean_grammy_details(df):
    '''
    clean grammy details data frame 
    '''

    # rename Ceremony to Title
    df.rename(columns={"Ceremony": "Title"}, inplace=True)

    # convert Title column to titlecase to join with Grammy Data Frame
    df['Title'] = df['Title'].apply(lambda x: str(x).title())

    # Clean Viewers( in millions ) - to Numerical, replace Nan with 0, convert to float
    df['Viewers (in millions)'] = df['Viewers (in millions)'].apply(lambda x: str(x).split("[")[0]
    if x and x != 'TBA'
    else 0)
    df['Viewers (in millions)'] = df['Viewers (in millions)'].astype('float')
    df['Viewers (in millions)'].fillna(0, inplace=True)

    # Clean Venue,
    df = df_grammy_details.apply(remove_brace, axis=0)

    return df


def clean_latin_details(df):
    # drop Person of the year, 
    df.drop(['Person of the Year'], axis=1, inplace=True)

    # rename Host City to Venue City( same as grammy details ); Host(s) to Host
    df.rename(columns={'Host City': "Venue City", "Host(s)": "Host"}, inplace=True)

    # Add Network column as blank
    df['Network'] = ""

    # change the order as Date,Venue,Venue City,Host, Network, Viewers(in millions)
    df = df.loc[:, ['Year', 'Date', 'Venue', 'Venue City', 'Host', 'Network', 'Viewers (in millions)']]

    # clean Viewers(in millions) and make it float data type
    df['Viewers (in millions)'].fillna(0, inplace=True)
    df['Viewers (in millions)'] = df['Viewers (in millions)'].apply(lambda x: str(x).split("[")[0]
    if x
    else 0)
    # replace comma by '.' in Viewes (in millions) column
    df['Viewers (in millions)'] = df['Viewers (in millions)'].apply(lambda x: str(x).replace(",", "."))

    # convert to float data type
    df['Viewers (in millions)'] = df['Viewers (in millions)'].astype("float")

    # clean Venue, Venue City, Host
    df = df.apply(remove_brace, axis=0)

    return df


def clean_latin_grammy(df):
    # create Artist column from Winners column
    df['Artist'] = df['Winners'].apply(get_artist)

    # rename colums, Title : Nominee, Wineers : Workers
    df.rename(columns={"Title": "Nominee", "Winners": "Worker"}, inplace=True)

    # add isWinner column as  True ( as these are all winners )
    # add isLatin column as True
    df['isWinner'] = "True"
    df['isLatin'] = "True"

    # create title column for latin df
    df['Title'] = df['Year'].apply(create_title)
    # make it title case
    df['Title'] = df['Title'].apply(lambda x: str(x).title())

    return df


def merge_grammy_with_details(df_main, df_details):
    # add isLatin column as False for Grammy Awards
    df_combined['isLatin'] = "False"

    # convert title to title case; set title as index for grammy and grammy-detail data frame
    df_main['Title'] = df_main['Title'].apply(lambda x: str(x).title())
    df_main.set_index(['Title'], inplace=True)

    # reset inde for grammy details
    df_details.set_index(['Title'], inplace=True)

    # join grammy and details
    df_main = df_main.join(other=df_details, on='Title', how="left", )

    # reset combined df index
    df_main.reset_index(inplace=True)

    return df_main


def merge_latin_grammy_details(df_main, df_details):
    df_main.set_index('Year', inplace=True)
    df_details.set_index('Year', inplace=True)

    df_main = df_main.join(other=df_details,
                           on='Year', how="left")

    df_main.reset_index(inplace=True)

    return df_main


if __name__ == '__main__':

    # steps
    # crawl grammy awards
    logging.info(f"Starting to Crawl : {seed_url[0]}...")

    error, grammy_links = crawl_grammy_links(webdriver_location, seed_url[0])
    if error == "":

        logging.info("Crawl Succesfull...")

        # scrape grammy awards
        error, dic_of_df = scrape_grammy(grammy_links, webdriver_location)

        if error == "":

            logging.info("Grammy Scrape Succesfull...")

            # combine all year data frames
            df_combined = pd.concat(dic_of_df, ignore_index=True)

            logging.info("Scraping Grammy Details...")
            # get details for grammy
            df_grammy_details = get_details(seed_url[1])

            logging.info("Scraping Latin Grammy Awards...")
            # scrape latin grammy
            error, df_latin = scrape_latin_grammy(webdriver_location, seed_url[2])

            if error == "":

                logging.info("Lating Grammy Scraping Successfull...")
                # get latin grammy details
                df_latin_grammy_details = get_details(seed_url[3])

                logging.info("Scraping Latin Grammy Details...")

                # clean grammy details data frame
                df_grammy_details = clean_grammy_details(df_grammy_details)

                logging.info("Cleaning the Data Collected...")

                # clean details dataframe for latin grammy
                df_latin_grammy_details = clean_latin_details(df_latin_grammy_details)

                # # combine grammy and locations
                df_combined = merge_grammy_with_details(df_combined, df_grammy_details)

                ## Clean and create data points for latin grammy
                df_latin = clean_latin_grammy(df_latin)

                # combine latim grammy and latin grammy details dataframes
                df_latin = merge_latin_grammy_details(df_latin, df_latin_grammy_details)

                # reorder the latin grammy columns( in line with grammy )
                df_latin = df_latin[list(df_combined.columns)]

                # combine latin grammy data with Grammys
                final_df = pd.concat([df_combined, df_latin], ignore_index=True)

                # replace \n from all columns if present, " from nominee(if starts and endswith), + from nominee

                # remove // ? % + \n "
                characs = re.compile(r'(\/\/|\?|\%|\+|\n|\"|\r)')
                # remove unicode point character
                unicode_point = re.compile(r'\u2022')

                # new_lines = re.compile(r'\n')
                # quotes = re.compile(r'"')

                # clean columns
                final_df['Nominee'] = final_df['Nominee'].apply(lambda x: re.sub(characs, "", str(x)))

                final_df['Artist'] = final_df['Artist'].apply(lambda x: re.sub(characs, "", str(x)))

                final_df['Artist'] = final_df['Artist'].apply(lambda x: re.sub(r',', "", str(x)))

                final_df['Worker'] = final_df['Worker'].apply(lambda x: re.sub(characs, "", str(x)))

                # # save to csv
                # final_df.to_csv("dcpp_final_grammy.csv", encoding='utf-8-sig',index=False)

                logging.info("Saving the data...")

                # save to json
                with open("dcpp_final_grammy.json", "w", encoding='utf-8-sig') as file:
                    final_df.to_json(file, orient='records', force_ascii=False)

            else:
                logging.error(f"Error while scraping Latin Grammy Awards : {error} ")

        else:
            logging.error(f"Error while scraping Grammy Awards : {error} ")

    else:
        logging.error(f"Error while crawling : {error}")
