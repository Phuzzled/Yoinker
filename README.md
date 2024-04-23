# Yoinker
Yoinker is designed to download files from a specified URL and categorize them into folders based on their file types. It employs multi-threading for efficient parallel downloads.

Command-Line Arguments: The script accepts command-line arguments to configure its behaviour:

url: The URL from which to download files.

-o or --output: The output directory where downloaded files will be stored.

-t or --threads: The number of threads to use for parallel downloads.

--user-agent: A custom User-Agent string to use for HTTP requests.

1. HTTP Session: The script creates an HTTP session with the specified User-Agent string.
2. URL Validation: It checks if the provided URL is within the scope of the base URL to prevent downloading files from external websites.
3. Page Content Fetching: The script fetches the HTML content of the initial URL and subsequent pages using the HTTP session.
4. Link Extraction: It parses the HTML content to extract links to files and other pages within the specified scope.
5. File Downloading: The script downloads files using multi-threading. It creates a progress bar for each file to provide real-time download status.
6. Recursive Exploration: The script recursively explores pages within the specified scope, downloading files and following links to other pages.
7. Download Metadata: It maintains a JSON metadata file that tracks the status of each downloaded file, including its URL, filename, status, and local path.
8. Summary and Metadata Saving: After completing the download process, the script prints a summary of the total files attempted, successfully downloaded, and failed. It also saves the download metadata to a JSON file in the output directory.

This script provides a convenient way to download files from a website, categorize them, and track their download status. It leverages multi-threading to optimize the download process and provides a detailed summary of the results.
