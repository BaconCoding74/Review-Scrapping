import requests;
import os;
import json;
import re;
import datetime;
import time;
from dotenv import load_dotenv;

# Load environment variables from a .env file
load_dotenv()

class LazadaScraper:
    def __init__(self) -> None:
        self.shopDetails = {}
        self.error = False

        envHeader = os.getenv("LAZADA_HEADERS")
        envCookie = os.getenv("LAZADA_COOKIES")

        if envHeader is not None:
            self.headers = json.loads(os.getenv("LAZADA_HEADERS"))

        if envCookie is not None:
            self.cookies = json.loads(os.getenv("LAZADA_COOKIES"))
    
    def searchItem(self, query:str, pageNumber:int = 1, pageLimit:int = 1) -> list:
        
        items = []

        # Loop search result pages
        for pageIncrement in range(pageLimit):
            # Define search url
            url = f"https://www.lazada.com.my/catalog/?ajax=true&q={query}&page={pageNumber + pageIncrement}"

            # Send get request
            req = requests.get(url, headers=self.headers, cookies=self.cookies)

            # Return if request failed
            if (req.status_code != 200):
                print(f"Invalid status code at {url}")
                return items

            itemList = req.json()["mods"]["listItems"]

            # Return if no result
            if (len(itemList) == 0):
                return items;

            # Add fetched items to list
            items = items + itemList

            # Set rate limit
            time.sleep(0.5)

        # Return results
        return items

    def getShopName(self, itemId:str) -> str:
        # Define search url
        url = f"https://www.lazada.com.my/catalog/?ajax=true&q={itemId}"

        # Send get request
        req = requests.get(url, headers=self.headers, cookies=self.cookies)

        # Return if request failed
        if (req.status_code != 200):
            print(f"Invalid status code at {url}")
            return None

        # Format data
        item = req.json()["mods"]["listItems"]

        # Return if abnormal
        if (len(item) != 1):
            return None
        
        item = item[0]

        # Cache
        self.shopDetails[item["sellerId"]] = item["sellerName"]

        return item["sellerName"]

    def getItemIdFromLink(self, url:str) -> str:
        # Regex capture the item id
        result = re.search(r'i(\d+)-s\d+\.html', url) or re.search(r'i(\d+)\.html', url)
        
        # Handle string return
        return result.group(1) if result else None;

    def getReviews(self, itemId:str = None, pageNumber:int = 1, pageLimit:int = 1, itemUrl:str = None) -> list:
        
        # Intialize essential variables
        reviews = []
        totalPage = float('inf')
        itemId = itemId or self.getItemIdFromLink(itemUrl)

        # Return if no item id
        if (not itemId):
            return reviews

        for pageIncrement in range(pageLimit):
            self.error = False

            # Check if exceed total page
            if (pageNumber + pageIncrement > totalPage):
                break

            try:
                # Define get review url
                url = f"https://my.lazada.com.my/pdp/review/getReviewList?itemId={itemId}&pageSize=50&filter=0&sort=0&pageNo={pageNumber + pageIncrement}"

                # Send get request
                req = requests.get(url, headers=self.headers, cookies=self.cookies)

                # Return if request failed
                if (req.status_code != 200):
                    print(f"Invalid status code at {url}")
                    break
                
                # Return if something wrong
                if ("model" not in req.json()):
                    self.error = True
                    break

                # Return if review not found
                if (req.json()["model"] == None):
                    break
                
                # Record total page
                if (totalPage == float('inf')):
                    totalPage = req.json()["model"]["paging"]["totalPages"]

                reviewList = req.json()["model"]["items"]

                # Return if no result
                if (len(reviewList) == 0):
                    break
                
                # Concatenate reviews
                reviews = reviews + reviewList

                # Filter out reviews with no rating
                [review for review in reviews if review["rating"] is not None]

                # Set rate limit
                time.sleep(1)
            except requests.exceptions.RequestException as error:
                print(itemId, error)
        
        print(f"Scrapped {itemId}")
        
        # Return result
        return reviews
    
    def processReview(self, review:dict) -> dict:

        temp = {}
        
        # Get shop name if not cache
        if (str(review["sellerId"]) not in self.shopDetails):
            self.getShopName(review["itemId"])

        try:
            temp["customerName"] = review["buyerName"]
            temp["itemName"] = review["itemTitle"]
            temp["variances"] = review["skuInfo"]
            temp["shopName"] = self.shopDetails[str(review["sellerId"])]
            temp["rating"] = review["rating"]
            temp["review"] = review["reviewContent"]
            temp["rating_date"] = review["reviewTime"]
            temp["platform"] = "Lazada"
        except:
            print(f"Review {temp["reviewRateId"]} have errors!")
            return None

        return temp


    def run(self) -> list:
        # Review list
        reviews = []

        # Search item first
        for index, item in enumerate(self.searchItem("pendrive", pageLimit=3), 1):
            print(f"{index}.Fetching {item["itemId"]}")
            
            reviews = reviews +  self.getReviews(item["itemId"], pageLimit=50)   

            if (self.error):
                print("Validation error")
                break

        # Tag platform
        [review.update({"platform": "lazada"}) for review in reviews]

        print("Lazada scraper finished!")
        print(f"Total Lazada Reviews: {len(reviews)}")

        return reviews



