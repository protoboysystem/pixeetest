import requests
import os
import re
from bs4 import BeautifulSoup
import subprocess
import sys
from dotenv import load_dotenv

load_dotenv()
COOKIE = os.getenv("COOKIE")


def download_video_from_m3u8_file(m3u8_url, folder_path, file_name):
    output_string = folder_path + file_name + ".mp4"
    regex_file_name = r"\d."
    matches_of_extras_in_filename = re.finditer(regex_file_name, file_name, re.MULTILINE)
    processed_output_string_file_name = file_name
    for match_in_filename in matches_of_extras_in_filename:
        processed_output_string_file_name = file_name[match_in_filename.end():].lstrip()
        break
    print(f">> Downloading : {processed_output_string_file_name}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "0", "-nostats", "-i", m3u8_url, output_string])


def process_individual_video(video_url, folder_path, file_name, overwrite_file):
    if os.path.exists(folder_path + file_name + ".mp4") and overwrite_file != file_name + ".mp4":
        return

    headers = {
        "Cookie": COOKIE
    }
    r = requests.get(video_url, headers=headers)
    individual_video_html_soup = BeautifulSoup(r.text, "html.parser")
    scripts = individual_video_html_soup.find_all("script")
    script_with_video_id = scripts[-1].text
    regex_course_id = r"id:.*?,"
    video_id = re.finditer(regex_course_id, script_with_video_id, re.MULTILINE)
    for match_of_video_id in video_id:
        download_video_from_m3u8_file(
            "https://fast.wistia.com/embed/medias/" + match_of_video_id.group().split(":")[-1].strip()[1:-2] + ".m3u8",
            folder_path, file_name)


def main(url, root_folder, overwrite_file_name):
    # response = requests.get("https://courses.kevinpowell.co/view/courses/conquering-responsive-layouts")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    html_beautified = soup.find_all("li", class_="list-group list-group-menu list-group-xs mb-6")
    for index, content in enumerate(html_beautified, start=1):
        sub_section = content.find_all("a")
        directory_info = sub_section[0]
        directory = str(index) + ". " + directory_info.text.strip()

        path = f"{root_folder}/{directory}/"
        if not os.path.exists(path):
            os.makedirs(path)
            print(f'>> Creating Folder : "{directory}"')

        for sub_index, sub_content in enumerate(sub_section[1:], start=1):
            process_individual_video("https://courses.kevinpowell.co" + sub_content["href"], path,
                                     str(sub_index) + ". " + sub_content.text.strip(), overwrite_file_name)

        if index == 21:
            break


if __name__ == '__main__':
    argv = sys.argv[1:]

    is_help_command_inserted = False
    try:
        help_command_index = argv.index("-h")
        print("""    -u -> Course URL
    -p -> Set Folder Path To Save Files [Optional]
    -o -> Overwrite Any Existing File With File Name [Optional]
        """)
        is_help_command_inserted = True
    except ValueError:
        is_help_command_inserted = False

    new_folder = "New Folder"
    try:
        url_command_index = argv.index("-u")
        url_string = argv[url_command_index + 1]
        regex = r"\/courses\/.*"
        matches = re.finditer(regex, url_string, re.MULTILINE)
        for match in matches:
            new_folder = match.group().split("/courses/")[1].rstrip("/")
            break
    except (ValueError, IndexError):
        url_string = ""
        if not is_help_command_inserted:
            print(">> Course URL Not Found !!")
            print("!! Run 'python main.py -h' To See Available Commands !!")
        url_command_index = -1

    try:
        root_folder_path_command_index = argv.index("-p")
        root_folder_path = argv[root_folder_path_command_index + 1]
        root_folder_path = os.path.join(root_folder_path, new_folder)
    except (ValueError, IndexError):
        root_folder_path = f"./{new_folder}"

    try:
        overwrite_command_index = argv.index("-o")
        overwrite_file = argv[overwrite_command_index + 1]
    except (ValueError, IndexError):
        overwrite_file = ""

    if url_command_index != -1:
        main(url_string, root_folder_path, overwrite_file)
