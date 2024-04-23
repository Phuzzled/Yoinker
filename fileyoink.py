import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import os
from tqdm import tqdm
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

def setup_argparse():
    parser = argparse.ArgumentParser(description="Download files from a given URL into categorized folders.")
    parser.add_argument("url", help="The URL to scrape files from.")
    parser.add_argument("-o", "--output", help="The output directory.", default="./downloads")
    parser.add_argument("-t", "--threads", type=int, help="Number of threads for parallel downloads.", default=10)
    parser.add_argument("--user-agent", help="Custom User-Agent string.", default="Mozilla/5.0 (compatible; FileYoink/1.0)")
    return parser.parse_args()

def get_session(user_agent):
    session = requests.Session()
    session.headers.update({'User-Agent': user_agent})
    return session

def is_within_scope(url, scope_url):
    parsed_url = urlparse(url)
    parsed_scope_url = urlparse(scope_url)
    if parsed_url.netloc != parsed_scope_url.netloc:
        return False
    if not parsed_url.path.startswith(parsed_scope_url.path):
        return False
    return True

def fetch_url(session, url, scope_url):
    try:
        response = session.get(url, allow_redirects=True)
        response.raise_for_status()
        if not is_within_scope(response.url, scope_url):
            return None
        return response.content
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None

def find_links(session, page_content, base_url, visited_urls):
    soup = BeautifulSoup(page_content, 'lxml')
    links = {'files': [], 'pages': []}
    for link in soup.find_all('a', href=True):
        href = link['href']
        if not href:
            continue  # Skip empty hrefs
        if any(href.lower().endswith(ext) for ext in ('.jpg', '.jpeg', '.js', '.webp', '.css', '.png', '.gif')):
            continue  # Skip unwanted file types
        full_link = urljoin(base_url, href)
        if not is_within_scope(full_link, base_url) or full_link in visited_urls:
            continue
        visited_urls.add(full_link)
        if any(href.lower().endswith(ext) for ext in ('.pdf', '.zip', '.mp3', '.mp4', '.mpg', '.mpeg', '.wav', '.csv', '.7z', '.rar', '.ppt', '.pptx', '.doc', '.docx', '.xls', '.txt')):
            links['files'].append(full_link)  # Add to files list for downloading
        else:
            links['pages'].append(full_link)  # Add to pages list for further exploration
    return links

def download_file(session, file_url, output_folder, metadata):
    parsed_url = urlparse(file_url)
    file_path = parsed_url.path.lstrip('/')
    save_path = os.path.join(output_folder, *file_path.split('/'))
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    try:
        with session.get(file_url, stream=True) as response:
            response.raise_for_status()
            total_size_in_bytes = int(response.headers.get('content-length', 0))
            with open(save_path, 'wb') as file, tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True, desc=os.path.basename(file_path), leave=False) as progress_bar:
                for data in response.iter_content(1024):
                    progress_bar.update(len(data))
                    file.write(data)

        metadata['files'].append({'url': file_url, 'filename': os.path.basename(file_path), 'status': 'Downloaded', 'path': save_path})
        return True
    except Exception as e:
        print(f"Error downloading {file_url}: {e}")
        metadata['files'].append({'url': file_url, 'filename': os.path.basename(file_path), 'status': 'Failed'})
        return False

def download_files(session, file_links, output_folder, threads, metadata):
    success_count = 0
    fail_count = 0
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(download_file, session, url, output_folder, metadata): url for url in file_links}
        for future in as_completed(futures):
            if future.result():
                success_count += 1
            else:
                fail_count += 1
    return success_count, fail_count

def explore_and_download(session, initial_url, output_folder, threads, metadata, visited_urls):
    print(f"Exploring {initial_url}...")
    page_content = fetch_url(session, initial_url, initial_url)  # Use initial_url as the scope
    if not page_content:
        return

    links = find_links(session, page_content, initial_url, visited_urls)
    if links['files']:
        print(f"Downloading {len(links['files'])} files from {initial_url}")
        success_count, fail_count = download_files(session, links['files'], output_folder, threads, metadata)
        metadata['success'] += success_count
        metadata['failed'] += fail_count

    for page_url in links['pages']:
        explore_and_download(session, page_url, output_folder, threads, metadata, visited_urls)

def main():
    args = setup_argparse()
    session = get_session(args.user_agent)
    output_dir = os.path.join(args.output, urlparse(args.url).netloc.replace('.', '_'), urlparse(args.url).path.strip('/'))
    os.makedirs(output_dir, exist_ok=True)

    metadata = {'files': [], 'success': 0, 'failed': 0, 'base_url': args.url}
    visited_urls = set([args.url])

    explore_and_download(session, args.url, output_dir, args.threads, metadata, visited_urls)

    print(f"\nDownload Summary:")
    print(f"Total Files Attempted: {len(metadata['files'])}")
    print(f"Successfully Downloaded: {metadata['success']}")
    print(f"Failed: {metadata['failed']}")

    with open(os.path.join(output_dir, 'download_metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=4)

if __name__ == "__main__":
    main()
