## Description
A python script for dumping challenges and attachment files from CTF event hosted with GZ::CTF. This script will automatically parse a GZ::CTF game challenges and download related static attachments to the directory specified by the user.

## Installation
- Clone this repository with the following command:
```
git clone https://github.com/griffinsectio/gzctf-dumper.git
```
- This script requires some python packages in order to perform its functions properly. The packages required are listed in requirements.txt and run the following command to install them:
```
pip install -r requirements.txt
```

## Usage
To use the script to dump a GZ::CTF game challenges the user and password to login to the platform with is required. **To avoid credential leak, run the script without `-u`/`--user` and `p`/`--password` arguments and the script will ask the username and password interactively**. The url where the game is hosted is required and can be passed to the script as positional argument. By default, the script will store the dump in `./Dump` directory, but another directory can be specified by passing the path to `-o`/`--out` argument.

## Demonstration
```
┌[griffinsectio@arch]-(~/gzctf-dumper)-[git://main ✗]-
└> python main.py --help
usage: main.py [-h] [-d] [-u USERNAME] [-p PASSWORD] [-o OUTPUT] url

A simple python script for dumping GZ::CTF games

positional arguments:
  url                   Base URL of GZ::CTF instance

options:
  -h, --help            show this help message and exit
  -d, --dry-run         Run without dumping the game
  -u, --username USERNAME
                        Username to login with (omit for interactive username input)
  -p, --password PASSWORD
                        Password for the user (omit for interactive password input)
  -o, --output OUTPUT   Directory where to dump the files (default: ./Dump)
┌[griffinsectio@arch]-(~/gzctf-dumper)-[git://main ✗]-
└> python main.py -o ~/localctf http://localhost
Username: Test0
Password:
[1] Title: new game
    Summary: new game summary
[2] Title: Test
    Summary: Summary
There are multiple games available
Enter the number of the game you want to dump
>> 2
[#] Game Challenges
    [#] Pwn
        [-] Spill (1000) [NOT SOLVED]
    [#] Forensics
        [-] Riddle Registry (1000) [SOLVED]
[#] Downloading game information
    [-] Game information written to /home/griffinsectio/localctf/README.md
[#] Downloading challenges attachments
    [-] /home/griffinsectio/localctf/Pwn/Spill/README.md written
    [-] /home/griffinsectio/localctf/Pwn/Spill/spill.zip downloaded
    [-] /home/griffinsectio/localctf/Forensics/Riddle Registry/README.md written
    [-] /home/griffinsectio/localctf/Forensics/Riddle Registry/confidential.pdf downloaded
```

