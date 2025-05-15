from lazada_scraper import LazadaScraper
from shopee_scraper import ShopeeScraper

import csv

def main():
    shopeeScraper = ShopeeScraper()  
    lazadaScraper = LazadaScraper()
    
    # Get reviews   
    reviews = shopeeScraper.run() + lazadaScraper.run()

    # Write csv file
    with open("output/reviews.csv", "w", newline='', encoding="utf-8") as csvFile:
        csvWriter = csv.writer(csvFile)
        
        # Loop review fetched and write into the csv file
        for index, review in enumerate(reviews, 0):
            review = shopeeScraper.processReview(review) if (review["platform"] == "shopee") else lazadaScraper.processReview(review)

            # Skip current review if there is in issue during processing
            if (not review):
                continue

            # Write header
            if (index == 0):
                csvWriter.writerow(review.keys())

            # Write content
            csvWriter.writerow([value.encode('utf-8', 'ignore').decode('utf-8') if (type(value) == str) else value for value in review.values()])

main()