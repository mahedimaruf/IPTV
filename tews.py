import csv
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from browsermobproxy import Server
import requests
import base64


def send_post_request(driver, state):
    # driver.get("https://www.winsupplyinc.com/location-finder")

    # Find and fill the input field with the state
    input_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "zipcode"))
    )
    input_field.clear()
    input_field.send_keys(state)

    # Wait for the submit button to be clickable (enabled)
   # Wait for the submit button to be clickable (enabled)
    submit_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (By.XPATH, "/html/body/app-root/div/app-static-direct-routes/app-location-finder/div[1]/div/div/div/div[1]/div/div[1]/form/div[3]/button"))
    )

    # Submit the form
    submit_button.click()

    # Wait for the network request and extract JSON response
    time.sleep(3)  # Adjust the delay if needed

    # Get the performance logs from the browser
    logs = driver.get_log("performance")
    response_data = None

    # Find the background request for searchAdditionalSupplier
    request_url = None
    for log in logs:
        message = json.loads(log["message"])["message"]
        if message.get("method") == "Network.responseReceived":
            response = message["params"]["response"]
             
            if "searchAdditionalSupplier" in response["url"]:
                req_id= message["params"]['requestId']
                print(req_id)
                response_data = response
                # print(response_data)
                break
    if response_data:
     try:
        # Retrieve the response body
        response_body = driver.execute_cdp_cmd(
            "Network.getResponseBody",
            {"requestId":req_id}
        )
        # Process the response body as needed
        print(response_body)
     except Exception as e:
        print("Error retrieving response body:", e)
 
    if response_body and response_body.get("body"):
        # Process the response body as needed
        response_body_data = json.loads(response_body["body"])
        # print(response_body_data)
        return response_body_data
    return None


def save_to_csv(data):
    file_exists = csv.reader(open("winsupplyinc.csv", "r"))

    with open("winsupplyinc.csv", mode="a", newline="") as csvfile:
        fieldnames = ["displayName", "address1", "city", "state",
                      "postalCode", "phoneNumber", "email", "seoURL"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if file_exists is None:
            writer.writeheader()

        for result in data["additionalSupplier"]:
            writer.writerow({
                "displayName": result["displayName"],
                "address1": result["address1"],
                "city": result["city"],
                "state": result["state"],
                "postalCode": result["postalCode"],
                "phoneNumber": result["phoneNumber"],
                "email": result["email"],
                "seoURL": result["seoURL"]
            })
            print(result)


def main():
    # Configure Chrome options
    chrome_options = Options()
    chrome_options.headless = False  # Set to True for headless mode
    capabilities = {
        'goog:loggingPrefs': {
            'performance': 'ALL'
        }
    }

    # Provide the path to the chromedriver executable
    path_to_chromedriver = "/path/to/chromedriver"

    # Create a Chrome webdriver instance
    driver = webdriver.Chrome(
        executable_path=path_to_chromedriver, options=chrome_options, desired_capabilities=capabilities)
    driver.get("https://www.winsupplyinc.com/location-finder")
    time.sleep(10)

    with open("states.csv", mode="r") as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header row
        for row in reader:
            state = row[0]
            response = send_post_request(driver, state)
            if response is not None:
                save_to_csv(response)
                print("Scraped data for", state)

    driver.quit()
    print("Data scraping completed!")


if __name__ == "__main__":
    main()
