import argparse
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tqdm import tqdm
import time


# some notes:
#             0) Apparently, the result of running on Linux and Windows is different. On Windows, I can call the script
#             from the command line via:
#             python wiki_stats.py Python_(programming_language) --pause '-1--2' --lang en
#             and it will work correctly, giving the specified error. On Linux, you need to wrap the page name in quotes
#             Additionally, the line
#             --pause '-1--2'
#             will not be parsed correctly, and argparse will throw its own error. To solve this problem, you need to
#             pass the --pause as the keyword argument, i.e, pause='-1--2'. In this case, the work will be correct.
#             To summarize, if you are running on Linux, call the script via:
#             python wiki_stats.py 'Python_(programming_language)' --pause='-1--2' --lang en

#             1) please, enter a pause as a string, i.e., '1ms', as it's mentioned in --help

#             1.1) parsing thousands of pages in a category is not very fast, so a large pause value will make you wait
#                  forever...

#             2) please, enter links_file and nearest_file with underscore between words, instead of dash (links-file)

#             3) I use the tqdm library to make the output more beautiful and friendly - if you do not have it
#             installed, and you do not want to do this, then please write to me about it and I will remove it,
#             or you can find and remove it from the code yourself using ctrl+F (tqdm)


def parse_cli_args() -> argparse.Namespace:
    """
    Parses command line arguments
    :return: argparse.Namespace object containing parsed command line arguments
    """
    parser = argparse.ArgumentParser(prog='wiki-stats', description='This program parses wiki by creating queries '
                                                                    'with a user-defined pause.')
    parser.add_argument('page', type=str, help='Wiki page name')
    parser.add_argument('--pause', default='3s', type=get_pause,
                        help="Pause between requests (default=3s). Please, enter is as a string, i.e. '1ms'. Can be "
                             "either a number (like '1000s' or '1000') or a"
                             "random variable from uniform distribution (like '1000s-10000ms' (s and ms are "
                             "optional)) or a random variable from Gauss "
                             "distribution (like 'gauss:1000s/2ms' (s and ms are optional)).")
    parser.add_argument('--lang', default='en', type=str, help='Desired wiki language (default=en). Can be en/fr/de/ru '
                                                               'etc.')
    parser.add_argument('--links_file', default='links.txt', type=str, help='')
    parser.add_argument('--nearest_file', default='nearest.txt', type=str, help='')
    args: argparse.Namespace = parser.parse_args()
    return args


def get_pause(pause: str) -> float:
    """
    Creates a pause the duration of which is specified by user
    :param pause: a user-specified parameter whose value determines the duration of the pause
    :return: duration of the pause
    """
    pause = pause.strip("'")
    if (pause.count('-') > 1 or pause[0] == '-') and 'gauss' not in pause:
        raise argparse.ArgumentTypeError("You've entered a negative time, but time cannot be negative! You can "
                                         "enter only positive values!")
    if 'gauss' in pause:
        expectation = convert_to_seconds(pause[pause.index(':') + 1:pause.index('/')])
        sigma = convert_to_seconds(pause[pause.index('/') + 1:])
        if sigma < 0.0:
            raise argparse.ArgumentTypeError(
                f"You've tried to use Gauss pause with sigma={sigma}. Even though random.gauss can handle a negative "
                f"sigma value you must enter it as a positive one, according to the laws of probability theory. Sorry.")
        else:
            pause_seconds = abs(random.gauss(expectation, sigma))
            print(f'Gauss pause was used with corresponding value {pause_seconds}s')
    elif '-' in pause:
        a, b = pause.split('-')
        a = convert_to_seconds(a)
        b = convert_to_seconds(b)
        if a > b:
            raise argparse.ArgumentTypeError('Left border of the entered interval is greater then the right one. That '
                                             'is not good.')
        else:
            pause_seconds = random.uniform(a, b)
            print(f'Uniform pause was used with corresponding value {pause_seconds}s')
    else:
        pause_seconds = convert_to_seconds(pause)
        if pause_seconds == 3.0:
            print(f'Default pause was used with corresponding value {pause_seconds}s')
        else:
            print(f'Pause value is {pause_seconds}s')
    return pause_seconds


def convert_to_seconds(time_string: str) -> float:
    """
    Converts a string representing time in seconds/milliseconds to float value in seconds
    :param time_string: string representing time in seconds/milliseconds
    :return: time in seconds
    """
    if 'ms' in time_string:
        return float(time_string[:-2]) / 1000
    elif 's' in time_string:
        return float(time_string[:-1])
    else:
        return float(time_string) / 1000


def make_test_wiki_request(url: str) -> int:
    """
    Makes a test request to wiki and checks its success
    :param url: page url
    :return: int flag indicating whether the request to page is successfull (1) or not(0)
    """
    response = requests.get(url)
    if response.status_code == requests.codes.ok:
        print(f'Your request to {url} is successful!')
        return 1
    elif response.status_code == requests.codes.not_found:
        print(f'Your request to {url} failed: there is no such page on wiki (code={response.status_code}). Try '
              f'another page.')
        return 0
    else:
        print(f'Something went wrong with request to {url}. code={response.status_code}. reason={response.reason}')
        return 0


def test_ambiguity(url: str, lang: str) -> int:
    """
    Checks whether the requested page is an informational page or a disambiguation page. If the latter,
     it offers you to select possible information pages.
    :param url: page url
    :param lang: page language
    :return: int flag: 0 means we're on the disambiguation page; 1 means we're on the informational page
    """
    response = requests.get(url)
    soup_obj = BeautifulSoup(response.text, 'html.parser')
    wiki_pattern = lang + '.' + 'wikipedia.org/wiki/'
    page_name = url[url.find(wiki_pattern) + len(wiki_pattern):]
    disambiguation_flag = page_name.rfind('_(disambiguation)')
    if disambiguation_flag != -1:
        page_name = page_name.rstrip('_(disambiguation)')
    page_name_counter = 0
    total_wiki_page_counter = 0
    possible_links_if_amb_page: list[str] = []
    service_words: list[str] = ['special:', 'talk:', '_(disambiguation)', page_name + '#']
    print('Testing ambiguity...')
    for a_tag in tqdm(soup_obj.find_all('a')):
        href = a_tag.get('href')
        absolute_url = urljoin(url, href)
        if wiki_pattern in absolute_url.lower() and not any(word in absolute_url.lower() for word in service_words):
            total_wiki_page_counter += 1
            if page_name.lower() in absolute_url.lower() and not any(
                    word.lower() in absolute_url.lower() for word in
                    service_words) and absolute_url.lower() != url.lower():
                page_name_counter += 1
                possible_links_if_amb_page.append(absolute_url)
    if page_name_counter / total_wiki_page_counter > 0.2:
        print("Apparently, you've landed on an ambiguous page instead of an informational one. Try choosing "
              "informational links from the list below:")
        for link in possible_links_if_amb_page:
            print(link)
        return 0
    else:
        print('Congratulations! You are on the informational page!')
        return 1


def get_external_links(url: str, links_file: str, lang: str) -> None:
    """
    Find all external links on the desired wiki page (url) and write them into the file named links_file
    :param url: page url
    :param lang: page language
    :param links_file: name of the file where external links will be written
    :return: None
    """
    response = requests.get(url)
    external_links_lang_tags: dict[str: str] = {'ru': 'Ссылки', 'en': 'External_links', 'de': 'Weblinks',
                                                'es': 'Enlaces_externos', 'fr': 'Liens_externes',
                                                'pt': 'Ligações_externas',
                                                'nl': 'Externe_links'}
    soup_obj = BeautifulSoup(response.text, 'html.parser')
    external_links: list[str] = []
    if external_tag := soup_obj.find(id=external_links_lang_tags[lang]):
        external_tag_parent = external_tag.find_parent()
        siblings = external_tag_parent.find_next_siblings('ul')
        print('Gathering external links...')
        for sibling in siblings:
            for a_tags in tqdm(sibling.find_all('a', class_='external text')):
                external_links.append(a_tags.get('href'))
        with open(links_file, mode='w') as f:
            print(*external_links, file=f, sep='\n')
    else:
        open(links_file, mode='w').close()


def get_cat_neighbors(url: str, nearest_file: str, pause: float) -> None:
    """
    Find all category neighbors of the desired wiki page (url) and write them into the file named nearest_file
    :param pause: pause between requests to pages on category page
    :param url: page url
    :param nearest_file: name of the file where links to the category neighbors will be written
    :return: None
    """
    response = requests.get(url)
    soup_obj = BeautifulSoup(response.text, 'html.parser')
    categories_names_list: list[str] = []
    categories_links_list: list[str] = []
    categories_links_for_file: list[tuple[str, int, ...]] = []
    category_a_tags = soup_obj.find('div', id='mw-normal-catlinks').find('ul').find_all('a')
    for a_tag in category_a_tags:
        categories_names_list.append(a_tag.text)
        categories_links_list.append(urljoin(url, a_tag.get('href')))
    print('Getting category neighbors...')
    for i, category_link in enumerate(tqdm(categories_links_list)):
        category_response = requests.get(category_link)
        next_page_flag = True
        while next_page_flag:
            soup_obj = BeautifulSoup(category_response.text, 'html.parser')
            category_headers_h2 = soup_obj.find_all('h2')
            for header in category_headers_h2:
                if categories_names_list[i] in header.text:
                    category_header = header
                    break
            category_div = category_header.find_next_sibling(
                'div', class_='mw-content-ltr').find('div', class_='mw-category mw-category-columns')
            for a_tag in category_div.find_all('a'):
                link_from_category_page = urljoin(url, a_tag.get('href'))
                link_response = requests.get(link_from_category_page)
                soup_neighbor_obj = BeautifulSoup(link_response.text, 'html.parser')
                category_neighbor_names: set[str] = set()
                category_neighbor_a_tags = soup_neighbor_obj.find('div', id='mw-normal-catlinks').find('ul').find_all(
                    'a')
                for cat_neighbor_a_tag in category_neighbor_a_tags:
                    category_neighbor_names.add(cat_neighbor_a_tag.text)
                categories_names_set = set(categories_names_list)
                category_neighbor_intersection = categories_names_set.intersection(category_neighbor_names)
                categories_links_for_file.append((link_from_category_page[link_from_category_page.find(
                    'wikipedia.org/wiki/') + len('wikipedia.org/wiki/'):], len(category_neighbor_intersection),
                                                  [*category_neighbor_intersection]))
                time.sleep(pause)
            near_pages = category_div.find_parent().find_next_siblings('a')
            if near_pages:
                for near_page in near_pages:
                    near_page_link = near_page.get('href')
                    if 'pagefrom' in near_page_link:
                        category_response = requests.get(urljoin(url, near_page_link))
                        next_page_flag = True
                    else:
                        next_page_flag = False
            else:
                next_page_flag = False
    unique_categories_links_for_file: list[tuple[str, int, ...]] = []
    for elem in categories_links_for_file:
        if elem not in unique_categories_links_for_file:
            unique_categories_links_for_file.append(elem)
    del categories_links_for_file
    del categories_names_list
    del categories_links_list
    del category_neighbor_names
    unique_categories_links_for_file.sort(key=lambda x: x[0])
    unique_categories_links_for_file.sort(key=lambda x: x[1], reverse=True)
    with open(nearest_file, mode='w', encoding='utf-8') as f:
        print(*unique_categories_links_for_file, file=f, sep='\n')


def main() -> None:
    """
    Main function of the wiki-stats program which parses the wiki with user-defined options
    :return: None
    """
    args: argparse.Namespace = parse_cli_args()
    print(args.page)
    url = f'https://{args.lang}.wikipedia.org/wiki/{args.page}'
    request_flag = make_test_wiki_request(url)
    if request_flag:
        ambiguity_flag = test_ambiguity(url, args.lang)
        if ambiguity_flag:
            get_external_links(url, args.links_file, args.lang)
            get_cat_neighbors(url, args.nearest_file, args.pause)


if __name__ == '__main__':
    main()
