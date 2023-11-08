# HSE_Python
Homework assignments on python in HSE <br />
## wiki-stats.py (please read the notes inside the script itself carefully): <br />
This script is a console application, i.e., you have to run it from the command line via python wiki_stats.py with one positional argument corresponding to the wiki page name and 4 optinal arguments: <br />
'--pause' (pause between requests to wiki) <br />
'--lang' (wiki page language) <br />
'--links_file' (name of file, where external links will be written) <br />
'--nearest_file' (name of file, where the names of pages that have common categories with a given page and the number of these categories will be written) <br />
Information about the script and its arguments can be obtained via: <br />
```
python wiki_stats.py --help
```
For example, on Windows we can run the script via: <br />
```
python wiki_stats.py Python_(programming language) --pause '1ms' --lang en links_file.txt nearest_file.txt
```
'--pause' argument can be entered either as a number ('1', '1ms', '1s'), or as an interval('1-2'), or as a random variable from Gauss distribution ('gauss:5/2'). <br />
The script, firstly, parses --pause argument and sets the pause duration. <br />
After that, it tries to make a test request to the entered page and checks whether the request is successful or not. <br />
Next, it checks whether the entered page is a disambiguation page or not. If so, it suggest to choose informational pages from the corresponding disambiguation page. <br />
If the page is not a disambiguation page, the script collects all external links from the page and write them into the links_file. <br />
Finally, the script collects the categories to which a given page belongs. After that it parses all the categories and links to Wikipedia articles within this category going to each article and determining the number of categories in common with a given page and their names. In the end, it writes to a nearest_file the name of the page, the number of general categories and their names.
