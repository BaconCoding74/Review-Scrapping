from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

import re
import time
import datetime
import requests
import json


class ShopeeScraper:

    def __init__(self):
        self.edgeDriver = None
        self.shopDetail = {}
        self.itemUrls = self.loadUrl()

    def loadUrl(self) -> list:
        temp = []

        # Load item url from text file
        with open("shopee_url.txt", "r") as file:
            for line in file:
                temp.append(line.strip())

        return temp

    # Setup webdriver
    def startWebDriver(self):
        path = "webdriver/chromedriver.exe"
        service = Service(path)
        options = Options()
        options.add_experimental_option("detach", True)
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument("--headless")

        # Initialize webdriver
        self.edgeDriver = webdriver.Edge(service=service, options=options)

    def getIds(self, itemUrl:str) -> dict:
        # Capture shopId and itemId
        result = re.search(r'-i\.(\d+)\.(\d+)', itemUrl)

        return {"shopId":result.group(1), "itemId":result.group(2)} if (result) else None;

    def getShop(self, shopId:int) -> dict:
        url = f"https://shopee.com.my/api/v4/promotion/get_shop_info?shop_id={shopId}"

        # Call api
        req = requests.get(url)

        # Check status code
        if (req.status_code != 200):
            print("Request failed!")
            return None
        
        # Get and store data
        data = req.json()["data"]

        return data

    def getReviews(self, itemId:str = None, shopId:str = None, limit:int = 50, pageNumber:int = 1, maxPage:int = 1, itemUrl:str = None) -> dict:
        
        reviews = []

        # Initialize item id and shop id
        if (itemUrl):
            ids = self.getIds(itemUrl)
            itemId = ids["itemId"]
            shopId = ids["shopId"]

        # Fetch shop details if not cached
        if (shopId not in self.shopDetail):
            self.shopDetail[shopId] = self.getShop(shopId)

        # Start webdriver
        if (not self.edgeDriver):
            self.startWebDriver()

        # Console log
        print(f"Fetching {itemId}")

        # Rating 0 is all but since the max size able to fetched is 3050, I seperate it to rating categories so it will fetch more 
        for rating in range(1, 6):
            # Loop review pages
            for offset in range(0, maxPage * limit, limit):

                # Redirect to another page
                self.edgeDriver.get(f"https://shopee.com.my/api/v2/item/get_ratings?exclude_filter=1&filter=0&filter_size=0&flag=1&fold_filter=0&itemid={itemId}&limit={limit}&offset={(pageNumber - 1) * limit + offset}&relevant_reviews=false&request_source=2&shopid={shopId}&tag_filter=&type={rating}&variation_filters=")

                # Set rate limit
                time.sleep(0.5)

                # Get content
                content = self.edgeDriver.find_element(By.TAG_NAME, "pre")
                data = json.loads(content.text)["data"]
                
                # Break loop if reached the end
                if ("ratings" not in data):
                    break

                # Concatenate reviews list
                reviews = reviews + data["ratings"]

        # Console log
        print(f"Scrapped {itemId}")

        return reviews
    
    def getVariances(self, product_items:dict):
        variances = []

        # Check if model name exist
        for item in product_items:
            if ("model_name" in item):
                variances.append(item)
        
        return ";".join([item["model_name"] for item in variances])


    
    def processReview(self, review:dict) -> dict:
        
        temp = {}

        # Process review
        temp["customerName"] = review["author_username"] if ("author_username" in review) else "NA"
        temp["itemName"] = review["original_item_info"]["name"]
        temp["variances"] = self.getVariances(review["product_items"]) if ("product_items" in review) else "NA"
        temp["shopName"] = self.shopDetail[str(review["original_item_info"]["shopid"])]["name"]
        temp["rating"] = review["rating_star"] if ("rating_star" in review) else "NA"
        temp["review"] = review["comment"] if ("comment" in review) else "NA"
        temp["rating_date"] = datetime.datetime.fromtimestamp(review["ctime"]).strftime("%Y-%m-%d %H:%M:%S")
        temp["platform"] = "Shopee"
        

        return temp;


    def run(self) -> list:
        # Review list
        reviews = []

        # Get reviews
        for itemUrl in self.itemUrls:
            # Get reviews
            reviews = reviews + self.getReviews(itemUrl=itemUrl, pageNumber=1, maxPage=1500)
        
        # Tag platform
        [review.update({"platform": "shopee"}) for review in reviews]

        print("Shopee Scraper finished!")
        print(f"Total Shopee Review: {len(reviews)}")

        return reviews
