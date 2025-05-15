rawCookies=""
rawHeaders={
    "accept": "",
    "accept-language": "",
    "priority": "",
    "sec-ch-ua": "",
    "sec-ch-ua-mobile": "",
    "sec-ch-ua-platform": "",
    "sec-fetch-dest": "",
    "sec-fetch-mode": "",
    "sec-fetch-site": "",
    "x-csrf-token": "",
    "x-requested-with": "",
    "x-ua": "",
    "x-umidtoken": ""
}

# Convert to form that can be loaded by json module from string
def process_cookies():
    cookies=[];
    for cookie in rawCookies.split(";"):
        key, value = cookie.split("=", 1);
        cookies.append(f'"{key}": "{value}"');

    return f'{{{", ".join(cookies)}}}';

def process_headers():
    headers=[];
    for key, value in rawHeaders.items():
        headers.append(f'"{key}": "{value.replace('"','\\"')}"');

    # Debugging
    # for header in headers:
    #     print(header);

    return f'{{{", ".join(headers)}}}';

with open(".env", "w") as file:
    file.write(f"LAZADA_HEADERS={process_headers()}\n")
    file.write(f"LAZADA_COOKIES={process_cookies()}")