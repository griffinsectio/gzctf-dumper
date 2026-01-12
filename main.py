import json
import argparse
import requests
import getpass
import os
import urllib
from urllib.parse import urljoin
from tqdm import tqdm
import utils.utils as utils

class GzctfDumper:
    def __init__(self, url, dry_run, username, password, output_dir):
        self.session = self.login(url, username, password)
        self.url = url
        self.dry_run = dry_run
        self.output_dir = output_dir
        self.games = self.get_games()
        self.game_id = self.get_game_id()
        self.challs = self.get_game_challs()

    def login(self, url, username, password):
        endpoint = urljoin(url, "/api/account/login")
        headers = {
                "Content-Type": "application/json"
        }
        json = {
            "challenge": None,
            "userName": username,
            "password": password
        }

        session = requests.Session()
        res = session.post(endpoint, headers=headers, json=json)

        try:
            res.raise_for_status()
            return session
        except requests.exceptions.HTTPError as e:
            print(f"An HTTP error occurred: {e}")
            if res.status_code == 401:
                utils.print_red("Incorrect username or password")
            self.logout()
            exit(1)

    def logout(self):
        self.session.close()

    def get_games(self):
        endpoint = urljoin(self.url, "/api/game")
        params = {
                "count": 50,
                "skip": 0
        }
        res = self.session.get(endpoint, params=params)
        
        try:
            res.raise_for_status()
            return json.loads(res.text)['data']
        except requests.exceptions.HTTPError as e:
            print(f"An HTTP error occurred: {e}")
            self.logout()
            exit(1)

    def get_game_id(self):
        if len(self.games) == 1:
            self.game_id = self.games[0]['id']
        else:
            for i, game in enumerate(self.games, 1):
                n = f"[{i}] "
                title = game['title']
                summary = game['summary']
                utils.print_green(n, end="")
                utils.print_yellow("Title: " + title)
                utils.print_blue(" "*len(n) + "Summary: " + summary)

            utils.print_red("There are multiple games available")
            utils.print_red("Enter the number of the game you want to dump")

            while True:
                choice = input(">> ")

                try:
                    choice = int(choice)
                except:
                    utils.print_red("Please enter valid game number")
                    continue
                
                if choice < 1 or choice > len(self.games):
                    utils.print_red("Please enter valid game number")
                    continue
                
                break

            return self.games[choice-1]['id']


    def get_game_info(self):
        endpoint = urljoin(self.url, f"/api/game/{self.game_id}")
        res = self.session.get(endpoint)
        
        try:
            res.raise_for_status()
            return json.loads(res.text)
        except requests.exceptions.HTTPError as e:
            print(f"An HTTP error occurred: {e}")
            self.logout()
            exit(1)

    def get_game_challs(self):
        endpoint = urljoin(self.url, f"/api/game/{self.game_id}/details")
        res = self.session.get(endpoint)
        
        try:
            res.raise_for_status()
            challenges = json.loads(res.text)['challenges']
            return challenges
            
        except requests.exceptions.HTTPError as e:
            print(f"An HTTP error occurred: {e}")
            self.logout()
            exit(1)

    def get_chall_info(self, chall_id):
        endpoint = urljoin(self.url, f"/api/game/{self.game_id}/challenges/{chall_id}")
        res = self.session.get(endpoint)
        
        try:
            res.raise_for_status()
            return json.loads(res.text)
        except requests.exceptions.HTTPError as e:
            print(f"An HTTP error occurred: {e}")
            self.logout()
            exit(1)

    def print_challs(self):
        utils.print_yellow("[#] Game Challenges")
        for category, challs in self.challs.items():
            utils.print_blue(f"    [#] {category}")
            for chall in challs:
                chall_info = f"        [-] {chall['title']} ({chall['score']})"
                if chall['solved']:
                    chall_info += " [SOLVED]"
                    utils.print_green(chall_info)
                else:
                    chall_info += " [NOT SOLVED]"
                    utils.print_red(chall_info)
                    
    def write_game_info(self, info, out):
        if self.dry_run:
            return

        with open(out, 'w') as f:
            f.write("# Game title:\n")
            f.write(f"{info['title']}\n")
            f.write('\n')

            f.write("# Game summary:\n")
            f.write(f"{info['summary']}\n")
            f.write('\n')

            f.write("# Game details:\n")
            f.write(f"{info['content']}\n")
            f.write('\n')

    def dump_game_info(self):
        info = self.get_game_info()
        out = f"{self.output_dir}/README.md"

        utils.print_yellow("[#] Downloading game information")
        try:
            self.write_game_info(info, out)
            utils.print_green(f"    [-] Game information written to {out}")
        except Exception as e:
            utils.print_red(f"An error occurred while writing to {out}: {e}")

    def write_chall_info(self, title, score, desc, hints, out):
        if self.dry_run:
            return

        with open(out, 'w') as f:
            f.write(f"# Title: {title}\n")
            f.write(f"# Score: {score}\n")
            f.write("\n")
            
            f.write("# Description\n")
            f.write(f"{desc}\n")
            f.write("\n")

            f.write("# Hints\n")
            for hint in hints:
                f.write(f"- {hint}\n")


    def download_attachment(self, url, out, size):
        if self.dry_run:
            return
        with self.session.get(url, stream=True) as res:
            with tqdm(total=size, desc=out, unit='B', unit_scale=True, colour='blue', leave=False) as pb:
                with open(out, 'wb') as f:
                    res.raise_for_status()

                    for chunk in res.iter_content(chunk_size=8192):
                        pb.update(len(chunk))
                        f.write(chunk)

    def dump_challs(self):
        utils.print_yellow("[#] Downloading challenges attachments")
        for category, challs in self.challs.items():
            category_dir = os.path.join(self.output_dir, category)

            for chall in challs:
                info = self.get_chall_info(chall['id'])
                title = info['title']
                desc = info['content']
                hints = info['hints']
                score = info['score']
                # attachment
                att_url = info['context']['url']
                att_filename = att_url.split('/')[-1]
                att_size = info['context']['fileSize']

                url = urljoin(self.url, att_url)

                chall_dir = os.path.join(category_dir, title)
                info_out = os.path.join(chall_dir, "README.md")
                download_out = os.path.join(chall_dir, att_filename)

                if not self.dry_run:
                    if not utils.is_dir_exists(chall_dir):
                        utils.makedirs(chall_dir)

                try:
                    self.write_chall_info(title, score, desc, hints, info_out)
                    utils.print_green(f"    [-] {info_out} written")
                except Exception as e:
                    print_red(f"An error occurred while writing to {out}: {e}")
                    
                try:
                    self.download_attachment(url, download_out, att_size)
                    utils.print_green(f"    [-] {download_out} downloaded")
                except Exception as e:
                    utils.print_red  (f"{download_out} download failed: {e}")

    def dump_game(self):
        try:
            if not self.dry_run:
                if not utils.is_dir_exists(self.output_dir):
                    utils.makedirs(self.output_dir)
        except Exception as e:
            utils.print_red(f"Unable to prepare output directory {self.output_dir}: {e}")
            self.logout()
            exit(1)

        try:
            if not utils.is_dir_empty(self.output_dir):
                utils.print_red("The output directory is not empty")

                while True:
                    choice = input("Do you want to continue? [Y/n]: ")
                    choice = choice.strip()

                    if (choice == "" or
                        choice.lower() == "y" or
                        choice.lower() == "yes"):
                        break
                    elif (choice.lower() == "n" or
                        choice.lower() == "no"):
                        self.logout()
                        exit(1)
                    else:
                        utils.print_red("Please answer with yes/no")
        except Exception as e:
            if not self.dry_run:
                print(f"An error occurred: {e}")
            

        self.print_challs()
        self.dump_game_info()
        self.dump_challs()
        self.logout()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            description="A simple python script for dumping GZ::CTF games")

    parser.add_argument('url',
                        help="Base URL of GZ::CTF instance")
    parser.add_argument('-d', '--dry-run',
                        action='store_true',
                        help="Run without dumping the game")
    parser.add_argument('-u', '--username',
                        help="Username to login with (omit for interactive username input)")
    parser.add_argument('-p', '--password',
                        help="Password for the user (omit for interactive password input)")
    parser.add_argument('-o', '--output',
                        default="Dump",
                        help="Directory where to dump the files (default: ./Dump)")

    args = parser.parse_args()

    url = args.url
    dry_run = args.dry_run
    username = args.username
    password = args.password
    output_dir = args.output

    if not args.username:
        username = input("Username: ")
    if not args.password:
        password = getpass.getpass(prompt="Password: ")

    dumper = GzctfDumper(url, dry_run, username, password, output_dir)

    dumper.dump_game()

