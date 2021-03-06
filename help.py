'''
Created on 12/07/2011

@author: tim
'''
help_text = """

<html>
<body>
<h3>Help</h3>
<ul>
<li><a href="#quick">Quick start</a></li>
<li><a href="#new">Creating a new harvest</a></li>
<ul>
<li><a href="#new-constructing">Constructing a search</a></li>
<li><a href="#new-required">Required fields</a></li>
<li><a href="#new-optional">Optional fields</a></li>
</ul>
<li><a href="#results">Viewing your harvest results</a></li>
<li><a href="#restart">Restarting an incomplete harvest</a></li>
<li><a href="#open">Opening a saved harvest</a></li>
</ul>

<hr></hr>
<a name="quick"><h5>Quick start</h5></a>
<ol>
<li>Copy the url of the Trove newspapers search you want to harvest</li>
<li>Paste the url into the 'Search URL' field</li>
<li>Give your harvest a name</li>
<li>Choose a directory to store your harvest files</li>
<li>Set your options as desired</li>
<li>Click GO</li>
<li>The progress of your harvest will be displayed in the status box</li>
</ol>

<hr></hr>
<a name="new">
<h5>Creating a new harvest</h5>
</a>
<a name="new-constructing">
<h6>Constructing a search</h6></a>
<p>You construct your search using Trove. Fine tune the search settings until you're 
getting the results that you want. Then simply copy the url in your browser's location 
box and paste into the Harvester's 'Search URL' field.</p>

<a name="new-required">
<h6>Required fields</h6>
</a>

<p><b>Name</b><br></br>
Give your harvest project a name! This name is used to create the filenames of your 
output files. Non-alphanumeric characters will be automatically removed.
</p>

<p><b>Folder</b><br></br>
Where do you want your harvest files to be saved? Your project configuration, log 
and output files will all be stored here.
</p>

<p><b>Search URL</b><br></br>
What do you want to harvest? Once you've constructed a search in the Trove newspapers 
database, simply cut and paste the url into this field. The program will complain 
if the url doesn't look like it came from Trove.
</p>

<a name="new-optional">
<h6>Optional fields</h6>
</a>

<p><b>Save text</b><br></br>
Check this box if you'd like to save the text contents of each individual article 
in a zip file.
</p>
<p><b>Save pdf</b><br></br>
Check this box if you'd like to save a pdf version of each individual article 
in a zip file.
</p>
<p><b>Organise files by</b><br></br>
If you've checked the 'Save text' or 'Save pdf' boxes you can choose how the articles 
will be organised in the zip file. The options are:
<ul>
<li>year -- articles will be sorted into folders according to the year of publication</li>
<li>newspaper -- articles will be sorted into folders according to the newspaper they were published in</li>
</ul>
</p>
<p><b>Start at result number</b><br></br>
If your harvest is interrupted, you can set the starting point here to pick things 
up where they left off. See <a href="#restart">Restarting an incomplete harvest</a>.
</p>

<hr></hr>
<a name="results">
<h5>Viewing your harvest results</h5>
The Harvester saves a number of files in the folder you specified. These are all named 
according to project name you supplied. Depending on the options you set, there 
will be two admin files and up to three results files. Assuming that you named your project 
'My Project' the files will be:

<p><b>Config file: my_project.ini</b><br></br>
This file stores your harvest settings so that it's easy to repeat a harvest at any time
in the future.
</p>

<p><b>Log file: my_project.log</b><br></br>
This file saves the details of your harvest so that you have a record of what you did 
and when you did it!
</p>

<p><b>CSV file: my_project_2011-07-12.csv</b><br></br>
This file stores all the article metadata in CSV (comma separated values) format. It can be easily imported 
into the spreadsheet or database of your choice. Note the YYYY-MM-DD date stamp in the file name. 
This tells you when the harvest was run, so you can repeat a harvest without worrying about overwriting your existing results.
</p>

<p><b>Text zip file: my_project_2011-07-12_text.zip</b><br></br>
This is a zip file that contains the text contents of all the individual articles. 
You can change the internal folder structure by setting the 'Organise files by' option. 
Like the CSV file, this file is date stamped to prevent confusion.
</p>

<p><b>PDF zip file: my_project_2011-07-12_pdf.zip</b><br></br>
This is a zip file that contains the PDF versions of all the individual articles. 
You can change the internal folder structure by setting the 'Organise files by' option. 
Like the CSV file, this file is date stamped to prevent confusion.
</p>
<hr></hr>
<a name="restart">
<h5>Restarting an incomplete harvest</h5>
</a>
<p>If for some reason your harvest is interrupted, it's easy to get it going again.</p>

<p>The Harvester will do it's best to keep a harvest alive, but if there's a problem 
with Trove that won't go away it will eventually give up and tell you that your harvest 
is incomplete.</p>

<p>At this point it will set the 'Start at result number' value to the last article that 
was successfully processed and re-enable the GO button. So all you have to do to get things 
started again is to click the button.</p>

<p>The Harvester will also save the new 'start' value in the config file. So if it looks like 
the problem's going to hang around for a while, you can close the Harvester until you think 
it's worth trying again. All you have to do then is <a href="#open">open your saved project</a> and click GO. 
The harvest will automatically pick up where it left off.</p>

<p>Depending on when your harvest failed, it's possible there could be duplicate rows in your CSV file. 
The project log will record your starting point/s so you can use them to check the CSV.</p>

<hr></hr>
<a name="open">
<h5>Opening a saved harvest</h5>
</a>
<p>New articles are always being added to the Trove newspapers database, so you might want to repeat a harvest 
from time to time to pick up any changes. This is easy. The details of your harvest are saved 
in a config file with a name like 'my_project.ini', all you need to do is open this 
file and the harvest details will be restored:
<ol>
<li>From the File menu choose Open (or Control+O)</li>
<li>Navigate to the directory containing your harvests</li>
<li>Select the relevant .ini file and open it</li>
<li>The Harvester fields will be automatically updated -- just click GO to start</li>
</ol>
</p>
<p>To help you keep track of your harvests, the results files are all date stamped 
and the details of each harvest are recorded in your project's log file.</p>

<p><i>Trove Newspaper Harvester v.0.9, 12 July 2011</i></p>
</body>
</html>
"""