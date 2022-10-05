"""
Aggregates first-author publications by members of UMD Astronomy within the last week.

author: @arjunsavel
"""
import re
import arxivscraper
import pandas as pd
import requests
import json
from bs4 import BeautifulSoup
from datetime import date
import datetime
from time import localtime

def aggregate_department_papers():
    """
    Main function for extracting department publications for the last week.
    """
    df = scrape_papers()

    
    # determine the indices in the df that each author corresponds to and each first author.
    authors = []
    first_authors = []
    indices = []
    first_indices = []
    for i, collabs in enumerate(df.authors):
        first_authors += [collabs[0]]
        first_indices += [i]
        for author in collabs:
            authors += [author]
            indices += [i]


    names = get_department_names()
    
    author_papers = cross_reference_names_papers(indices, names, authors, df)
    first_author_papers = cross_reference_names_papers(first_indices, names, first_authors, df)
                
    return first_author_papers, author_papers



def get_name(row):
    """
    From a given row in the scraped department page, grabs the first and last name.
    """
    # TODO: hyphen and middle name? non-initialed middle name?
    
    if '-' in row[0]: # hyphenated last name!
        last_name = row[0].split(',')[0].lower() + row[1].split(',')[0].lower()
        first_name = row[2].split(',')[0].lower()
        return first_name + ' ' + last_name
    
    if '.' in row[1]: # middle initial!
        last_name = row[0].split(',')[0].lower()
        initial = row[1].split(',')[0].lower()
        first_name = row[2].split(',')[0].lower()
        return first_name + ' ' + initial + ' '+ last_name
    
    last_name = row[0].split(',')[0].lower()
    first_name = row[1].split(',')[0].lower()
    return first_name + ' ' + last_name

        
def permutate_name(name):
    """
    Makes a list of potential permutations of a name.
    """
    if '.' in name: # middle initial
        first, initial, last = name.split(' ')
        first_initial = first[0]
        return name, first_initial + '. ' + initial + ' ' + last, first_initial + '. ' + last, last + ', ' + first
    first, last = name.split(' ')
    first_initial = first[0]
    return name, first_initial + '. ' + last, last + ', ' + first

def scrape_papers():
    """
    Scrapes arxiv for papers published in the last week.
    
    Output
    ------
        :df: (pd.DataFrame) object containing all the papers published on astro-oh in the last week.
    """
    today = date.today()

    week_ago = today - datetime.timedelta(days=7)

    scraper = arxivscraper.Scraper(
        category='physics:astro-ph', 
        date_from=week_ago.strftime("%Y-%m-%d"),date_until=today.strftime("%Y-%m-%d"))
    output = scraper.scrape()

    cols = ('id', 'title', 'categories', 'abstract', 'doi', 'created', 'updated', 'authors', 'affiliation', 'url')
    df = pd.DataFrame(output,columns=cols)
    return df


def get_department_names():
    """
    Scrapes the department website for a list of people in the department.
    
    Outputs
    -------
        :names: (list of strs) names of members in the department. 
    """
    
    # scrape the website
    URL = 'https://www.astro.umd.edu/people/directory.html'
    page = requests.get(URL)

    # parse the website
    soup = BeautifulSoup(page.content, 'html.parser')
    
    names = []
    
    # step through the soup object to find the names within the webpage structure.
    for i in range(len(soup.find_all('tr'))):
        row = re.sub(r"([A-Z])", r" \1", soup.find_all('tr')[i].text).split()

        # TODO: change these to test-name func
        if row[0] == 'Last' and row[-1] == 'Website':
            continue
        if row[0] == 'Tenured/' and row[-1] == 'Numbers':
            continue
        name = get_name(row)
        if name != 'first last' and name.split(' ')[0] != 'room':
            names += [name]
    return names
    
   
def cross_reference_names_papers(author_indices, names, authors, df):
    """
    Goes through the df and determines the *papers* that correspond to a given set of *names*,
    assuming that *names* is cross-referenced against a set of *authors* that are in the 
    *author_indices* of the df.

    Inputs
    ------
        :author_indices: (list-like of ints) position in dataframe corresponding to each 
                        author in authors.
        :names: (list-like of strs) names of people we'd like to check for the df.
        :authors: (list-like of strs) list of authors in the df corresdponding to the author_indices.
        :df: (pd.DataFrame) holds all the scraping output.
    """
    author_dict = {}
    for name in names:
        # need to check all variations of the name
        name_permutations = permutate_name(name)
        for name_permutation in name_permutations:

            try:
                inds = [i for i, e in enumerate(authors) if e == name_permutation]

                # if there are no papers for this author, skip past.

                if len(inds) == 0:
                    continue
                for ind in inds:
                    df_ind = author_indices[ind]
                    paper = df.title.values[df_ind]
                    author_dict[name] = paper
            except ValueError: # name wasn't published
                continue
    return author_dict
    
            
if __name__=='__main__':
    first_author_papers, author_papers = aggregate_department_papers()
    
    
    today = date.today().strftime("%Y-%m-%d")
    
    
    with open(f"data/first_authors_{today}.json", "w") as outfile:
        json.dump(first_author_papers, outfile)
        
    with open(f"data/authors_{today}.json", "w") as outfile:
        json.dump(author_papers, outfile)
    
    
    
    
    
    
    
    