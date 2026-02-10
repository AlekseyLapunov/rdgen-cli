import argparse
import json
import os
from urllib.parse import urlparse
import requests
import re
import time

CHECK_STATUS_TIMEOUT_SEC = 15
MAX_TIME_CHECKING_SEC    = 7200

LOCAL_DOWNLOADS_DIR  = "downloads"

MAX_REQUEST_TRIES = 5

BODY_DATA_AS_FORM = "form"
BODY_DATA_AS_JSON = "json"

PORT_HTTP  = 80
PORT_HTTPS = 443

BUILD_GENERATING = "generating"
BUILD_GENERATED  = "generated"

RE_PATTERN_BUILD_STATUS   = r'<span id="statusText">(.*?)<\/span>'
RE_PATTERN_CHECK_FOR_FILE = r"window\.location\.replace\('\/check_for_file\?(.*)'\);"
RE_PATTERN_PAGE_TITLE     = r'<title id="pageTitle">(.*)<\/title>'

reBuildStatus = re.compile(RE_PATTERN_BUILD_STATUS)
reCheckFile   = re.compile(RE_PATTERN_CHECK_FOR_FILE)
rePageTitle   = re.compile(RE_PATTERN_PAGE_TITLE)

def parseAddress(url):
    if "://" not in url:
        url = "http://" + url

    parsed = urlparse(url)
    
    if parsed.scheme not in ("http", "https"):
        print(f"Wrong protocol (scheme): {parsed.scheme}")
        return None, None, None, None

    login = parsed.username
    password = parsed.password
    domain = parsed.hostname
    port = parsed.port
    scheme = parsed.scheme

    if port is None:
        port = PORT_HTTPS if scheme == "https" else PORT_HTTP

    return login, password, domain, port, scheme

def tryRequest(method, url, body = None, auth = None, bodyDataType = BODY_DATA_AS_JSON) -> requests.Response:
    curTry = 0
    response = None

    if bodyDataType != BODY_DATA_AS_FORM and bodyDataType != BODY_DATA_AS_JSON and body is not None:
        print(f"Unknown body data type: {bodyDataType}")
        return None
    
    while curTry != MAX_REQUEST_TRIES:
        try:
            formData = None
            jsonData = None

            if body:
                formData = body if bodyDataType == BODY_DATA_AS_FORM else None
                jsonData = body if bodyDataType == BODY_DATA_AS_JSON else None

            response = requests.request(method=method, url=url, json=jsonData, data=formData, auth=auth)
            break
        except Exception as e:
            curTry += 1
            print(f"[{curTry}/{MAX_REQUEST_TRIES}] Request unsuccessful: {e}")

    if curTry == MAX_REQUEST_TRIES:
        return None

    return response

def parseArguments():
    parser = argparse.ArgumentParser()

    parser.add_argument("-f", "--file",   required=True, help="Input configuration file (JSON)")
    parser.add_argument("-s", "--server", required=True, help="Address of rdgen server. HTTP (:80) is the default scheme")

    parser.add_argument("-v", "--verbose",          action="store_true", help="Increase output verbosity")
    parser.add_argument("-p", "--preserve-log",     action="store_true", help="Preserve build status log")
    parser.add_argument("-d", "--disable-download", action="store_true", help="Disable automatic result download")

    args = parser.parse_args()

    return args.file, args.server, args.verbose, args.preserve_log, args.disable_download

def parseBuildStageInfo(html):
    resultStatus = reBuildStatus.search(html)

    if not resultStatus:
        print("Problem parsing build status from HTML.")
        return None, None, None, None
    
    stageInfo = resultStatus.group(1)
    
    resultCheckFile = reCheckFile.search(html)

    if not resultStatus:
        print("Problem parsing check file query from HTML.")
        return None, None, None, None
    
    checkFileQuery = resultCheckFile.group(1)
    
    queries = checkFileQuery.split("&")

    filename = None
    uuid = None
    platform = None

    for q in queries:
        keyVal = q.split("=")

        key = keyVal[0]
        val = keyVal[1]
        if key == "filename":
            filename = val
        elif key == "uuid":
            uuid = val
        elif key == "platform":
            platform = val
        else:
            print(f"Catched unexpected key in query: '{key}':'{val}'")

    return stageInfo, filename, uuid, platform

def getPageTitle(html):
    result = rePageTitle.search(html)

    if result is None:
        print("Failed to get page title")
        return None

    return result.group(1)

def getResultDownloadLinks(baseUrl, filename, platform, uuid):
    downloadLinks = []

    common = f"{baseUrl}/download?"

    if platform == 'windows':
        downloadLinks.append(f"{common}filename={filename}.exe&uuid={uuid}")
        downloadLinks.append(f"{common}filename={filename}.msi&uuid={uuid}")
    elif platform == 'windows-86':
        downloadLinks.append(f"{common}filename={filename}.exe&uuid={uuid}")
    elif platform == 'linux':
        downloadLinks.append(f"{common}filename={filename}-x86_64.deb&uuid={uuid}")
        downloadLinks.append(f"{common}filename={filename}-x86_64.rpm&uuid={uuid}")
        downloadLinks.append(f"{common}filename={filename}-suse-x86_64.rpm&uuid={uuid}")
        downloadLinks.append(f"{common}filename={filename}-x86_64.pkg.tar.zst&uuid={uuid}")
        downloadLinks.append(f"{common}filename={filename}-aarch64.deb&uuid={uuid}")
        downloadLinks.append(f"{common}filename={filename}-aarch64.rpm&uuid={uuid}")
        downloadLinks.append(f"{common}filename={filename}-suse-aarch64.rpm&uuid={uuid}")
        downloadLinks.append(f"{common}filename={filename}-aarch64.pkg.tar.zst&uuid={uuid}")
        downloadLinks.append(f"{common}filename={filename}-x86_64.AppImage&uuid={uuid}")
        downloadLinks.append(f"{common}filename={filename}-aarch64.AppImage&uuid={uuid}")
        downloadLinks.append(f"{common}filename={filename}-x86_64.flatpak&uuid={uuid}")
        downloadLinks.append(f"{common}filename={filename}-aarch64.flatpak&uuid={uuid}")
    elif platform == 'android':
        downloadLinks.append(f"{common}filename={filename}-aarch64.apk&uuid={uuid}")
        downloadLinks.append(f"{common}filename={filename}-x86_64.apk&uuid={uuid}")
        downloadLinks.append(f"{common}filename={filename}-armv7.apk&uuid={uuid}")
    elif platform == 'macos':
        downloadLinks.append(f"{common}filename={filename}-x86_64.dmg&uuid={uuid}")
        downloadLinks.append(f"{common}filename={filename}-aarch64.dmg&uuid={uuid}")
    else:
        print(f"Unexpected platform: {platform}")
        return None
    
    return downloadLinks

def downloadFiles(links: list[str], path, verbose) -> int:
    idx = 1
    count = len(links)

    reFileName = re.compile(r"download\?filename=(.*)&")

    successCount = 0

    for link in links:
        preamble = f"[{idx}/{count}]"

        try:
            filename = os.path.join(path, link.split("/")[-1])

            filename = reFileName.search(filename).group(1)

            maxLen = 1

            if verbose:
                output = f"\r{preamble} Downloading: {filename} ..."
                maxLen = max(maxLen, len(output))
                print(output, end=" "*(maxLen - len(output)), flush=True)
            
            response = requests.get(link, stream=True)
            response.raise_for_status()

            with open(f"{path}/{filename}", 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"\r{preamble} File saved locally: {filename}")

            successCount += 1
            
        except requests.exceptions.RequestException as e:
            print(f"Error downloading {link}: {e}")
            continue
        
        idx += 1
        
    return successCount

def formatResponse(response: requests.Response) -> str:
    return f"HTTP {response.status_code}: {response.text}"

def printBulletPoints(bulletPoints):
    for bp in bulletPoints:
        print(f"\t- {bp}")

def isHttpSuccess(code) -> bool:
    return code >= 200 and code <= 299 

def fatal(msg):
    print(f"! {msg}; Terminating.")
    exit(-1)

def main():
    confFile, rdgenAddress, verbose, dontFlushStatusLog, dontDownloadResult = parseArguments()

    if verbose:
        if dontFlushStatusLog:
            print("Preserving build status")
        if dontDownloadResult:
            print("Automatic download disabled")

    if not os.path.exists(confFile):
        fatal(f"Configuration file not found: {confFile}")

    confStr = None
    try:
        with open(confFile, "r", encoding="utf-8") as f:
            confStr = f.read()
    except Exception as e:
        fatal(f"Problem reading configuration file: {e}")
        confStr = None

    if verbose:
        print(f"Reading configuration file '{confFile}'...")

    confObj = None
    try:
        confObj = json.loads(confStr)
    except Exception as e:
        fatal(f"Problem unmarhalling the JSON configuration: {e}")

    print("Configuration JSON parsed successfully!")

    login, password, domain, port, scheme = parseAddress(rdgenAddress)

    if domain is None:
        fatal("Failed parsing the address of rdgen server")

    if verbose:
        print("rdgen address information:")
        printBulletPoints([f"Domain: {domain}", f"Port: {port}", f"Scheme: {scheme}", f"Login: {login or '<absent>'}", f"Password: <{'supplied' if login else 'absent'}>"])

    portStr = f":{port}" if port != PORT_HTTPS and port != PORT_HTTP else ""
    rdgenBaseUrl = f"{scheme}://{domain}{portStr}"

    basicAuth = (login, password) if login and password else None

    print("Requesting generator start...")

    response = tryRequest("POST", f"{rdgenBaseUrl}/generator", body=confObj, auth=basicAuth, bodyDataType=BODY_DATA_AS_FORM)

    if response is None:
        fatal(f"Connection error: {rdgenBaseUrl}")

    if not isHttpSuccess(response.status_code):
        fatal(f"Failed to start generator: {formatResponse(response)}")

    print("Generator started! Checking initial build stage...")

    stageInfo, filename, uuid, platform = parseBuildStageInfo(response.text)

    if stageInfo is None:
        fatal("Problem getting initial build stage information")

    if verbose:
        print("Initial build stage info:")
        printBulletPoints([f"File name: {filename}", f"UUID: {uuid}", f"Platform: {platform}", f"Stage: {stageInfo}"])
        print("Evaluating download links...")
    
    downloadLinks = getResultDownloadLinks(rdgenBaseUrl, filename, platform, uuid)

    if downloadLinks is None:
        fatal("Problem getting download links")

    print("Printing download links up-front. The result will be accessible as soon as the build is done:")
    printBulletPoints(downloadLinks)    
    
    print(f"Build initiated. Checking status every {CHECK_STATUS_TIMEOUT_SEC} seconds...")

    elapsedSeconds = 0

    maxLen = 1

    while True:
        response = tryRequest("GET", f"{rdgenBaseUrl}/check_for_file?filename={filename}&uuid={uuid}&platform={platform}", auth=basicAuth)

        if not isHttpSuccess(response.status_code):
            fatal("Response was not successful from rdgen server")

        pageTitle = getPageTitle(response.text)

        if pageTitle is None:
            fatal("Page title is None")
        else:
            pageTitle = pageTitle.lower()

        stageInfo = None

        if BUILD_GENERATING in pageTitle:
            stageInfo, _, _, _ = parseBuildStageInfo(response.text)
        elif BUILD_GENERATED in pageTitle:
            if "<p>Error: No file generated</p>" in response.text:
                fatal("No result file were generated")
            break
        else:
            fatal(f"Unexpected page title: {pageTitle}")

        if stageInfo is None:
            fatal("Problem getting stage information")

        h = elapsedSeconds // 3600
        m = (elapsedSeconds % 3600) // 60
        s = elapsedSeconds % 60
            
        output = f"[{h:02}:{m:02}:{s:02}] Stage: {stageInfo}"

        if dontFlushStatusLog:
            print(output)
        else:
            maxLen = max(maxLen, len(output))
            print(f"\r{output}", end=" "*(maxLen - len(output)), flush=True)

        time.sleep(CHECK_STATUS_TIMEOUT_SEC)
        elapsedSeconds += CHECK_STATUS_TIMEOUT_SEC

        if elapsedSeconds >= MAX_TIME_CHECKING_SEC:
            fatal("Waiting for too long. Something might be wrong, need to check GitHub Action manually")

    if not dontFlushStatusLog:
        print("")

    print("Build complete! Result download links:")
    printBulletPoints(downloadLinks)

    if dontDownloadResult:
        print("Automatic result downloading was disabled. Use provided links to download manually")
        exit(0)

    savePath = f"{LOCAL_DOWNLOADS_DIR}/{filename}_{uuid}"

    if verbose:
        print(f"Creating directory for storing downloaded files... ({savePath})")

    try:
        os.makedirs(savePath)
    except Exception as e:
        fatal(f"Problem creating directory for result files: {e}")

    downloadedCount = downloadFiles(downloadLinks, savePath, verbose)

    filesToDownload = len(downloadLinks)

    postamble = f"({downloadedCount}/{filesToDownload})"

    if downloadedCount == 0:
        fatal(f"No files were downloaded {postamble}")

    if downloadedCount != filesToDownload:
        fatal(f"Not all files have been downloaded {postamble}")
    
    print(f"Build result files downloaded locally: {savePath}")
    
if __name__ == "__main__":
    main()
