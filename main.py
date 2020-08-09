import requests
import os
import subprocess
from rich.progress import Progress
from rich import print
import ctypes
import sys
import shutil

REPO_URL = "https://alexisdelhaie.ovh/dlcenter/chronos-repo/installer/"
VERSION_FILE = "version"
COMPANY_NAME = "alexlegarnd"
SOFTWARE_NAME = "chronos-installer"
CACHE_FOLDER = "cache"
INSTALL_FOLDER = "{}\\{}\\{}".format(os.getenv('APPDATA'), COMPANY_NAME, SOFTWARE_NAME)
CACHE_FOLDER_PATH = "{}\\{}".format(INSTALL_FOLDER, CACHE_FOLDER)
INSTALLED_VERSION_PATH = "{}\\{}".format(INSTALL_FOLDER, VERSION_FILE)
EXECUTABLE = "Install.exe"
EXECUTABLE_PATH = "{}\\{}".format(INSTALL_FOLDER, EXECUTABLE)
FILES = ["libeay32.dll", "ssleay32.dll", "7z.dll", EXECUTABLE]


def get_installed_version():
    print('[bold green]INFO[/] Checking installed version')
    if os.path.exists(INSTALLED_VERSION_PATH):
        file = open(INSTALLED_VERSION_PATH, "r")
        version = file.read()
        file.close()
        print('[bold green]INFO[/] {} found'.format(version))
        return version
    print('[bold green]INFO[/] no version installed')
    return "0.0.0"


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def get_version_from_repo():
    print('[bold green]INFO[/] Getting version on repo')
    url = "{}{}".format(REPO_URL, VERSION_FILE)
    r = requests.get(url, allow_redirects=True)
    return r.text


def download_file_from_repo(filename):
    url = "{}{}".format(REPO_URL, filename)
    with open("{}\\{}".format(INSTALL_FOLDER, filename), 'wb') as f:
        response = requests.get(url, stream=True)
        total_length = response.headers.get('content-length')

        if total_length is None:  # no content length header
            f.write(response.content)
        else:
            with Progress() as progress:
                task = progress.add_task("Fetching {}".format(filename), total=int(total_length))
                for data in response.iter_content(chunk_size=4096):
                    f.write(data)
                    progress.update(task, advance=len(data))


def create_install_folder():
    company_directory = "{}\\{}".format(os.getenv('APPDATA'), COMPANY_NAME)
    if not os.path.exists(company_directory):
        os.mkdir(company_directory)
        print('[bold green]INFO[/] Creating {} folder'.format(company_directory))
    if not os.path.exists(INSTALL_FOLDER):
        os.mkdir(INSTALL_FOLDER)
        print('[bold green]INFO[/] Creating {} folder'.format(INSTALL_FOLDER))


def clean_folder(path):
    if os.path.exists(path):
        for filename in os.listdir(path):
            if filename != CACHE_FOLDER:
                file_path = os.path.join(path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('[bold red]ERROR[/] Failed to delete {}. Reason: {}'.format(file_path, e))


def clean():
    if '--clean' in sys.argv:
        clean_folder(INSTALL_FOLDER)
        clean_folder(CACHE_FOLDER_PATH)
    if '--clean-cache' in sys.argv:
        clean_folder(CACHE_FOLDER_PATH)
    if '--clean-installer' in sys.argv:
        clean_folder(INSTALL_FOLDER)


def main():
    if not is_admin():
        print('[bold red]ERROR[/] This app need to be launched eleveted')
        sys.exit(0)
    version = get_version_from_repo()
    create_install_folder()
    clean()
    if get_installed_version() != version:
        clean_folder(INSTALL_FOLDER)
        for file in FILES:
            download_file_from_repo(file)
        if os.path.exists(INSTALLED_VERSION_PATH):
            os.remove(INSTALLED_VERSION_PATH)
        file = open(INSTALLED_VERSION_PATH, "w")
        file.write(version)
        file.close()
    if os.path.exists(EXECUTABLE_PATH):
        print('[bold green]INFO[/] Starting installer')
        subprocess.Popen([EXECUTABLE_PATH], cwd=INSTALL_FOLDER)
    else:
        print('[bold red]ERROR[/] Executable not found')
        input('-- Press enter key to quit --')


main()
