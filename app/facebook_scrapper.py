from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from time import sleep
from selenium.webdriver.common.keys import Keys
import pandas as pd
from pymongo import MongoClient 
from typing import List

class FacebookScrapper:
    def __init__(self) -> None:
        pass

    def login(
        self,
        email: str,
        password: str
    ):
        """
        Logs in to Facebook using the provided email and password.

        Args:
            email (str): The email address of the Facebook account.
            password (str): The password of the Facebook account.
        """

        # Creating a webdriver instance
        chrome_options = Options()
        self.driver = webdriver.Chrome(chrome_options=chrome_options)
        self.driver.maximize_window()

        # Opening facebook login page
        self.driver.get("https://www.facebook.com/")

        # waiting for the page to load
        time.sleep(5)

        username = self.driver.find_element(By.ID, "email")

        # Enter Your Email Address
        username.send_keys(email)

        # entering password
        pword = self.driver.find_element(By.ID, "pass")
        pword.send_keys(password)

        
        # Login button 
        self.driver.find_element(By.XPATH, "//button[@name='login']").click()

    def search_subject(
        self,
        subject: str,
    ):
        """
        Searches for publications about a subject on Facebook in the "Rechercher sur Facebook" section.

        Args:
            subject (str): The subject to search for on Facebook.
        """
        elt = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.XPATH,"(//input[@placeholder='Rechercher sur Facebook'])[1]")))[0]
        elt.send_keys(subject)

        actions = ActionChains(self.driver)
        actions.send_keys(Keys.ENTER)
        actions.perform()

        elt = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.XPATH,"(//span[contains(text(),'Publications')])[1]")))[0]
        elt.click()


    def get_posts_links(
            self,
    ):
        """
        Retrieves the links to the posts on the current page.

        Returns:
            list: A list of post links.
        """

        # Scroll down to get more posts
        duree_defilement = 15
        scroll_pause_time = 0.5
        for _ in range(duree_defilement):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause_time)
        # Get posts links by scrapping the elements containg the date with it's xpath class
        posts = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.XPATH,'(//a[contains(@class,"x1i10hfl xjbqb8w x6umtig x1b1mbwd xaqea5y xav7gou x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz x1heor9g xt0b8zv xo1l8bm")])')))
        print(posts)
        post_links = []
        # For each post, get the href link of the post
        for post in posts:
            post_links.append(post.get_attribute('href'))

        return post_links 
    
    def scrap_informations_post(
        self,
        post_url: str,
    ):
        """
        Scrapes information from a Facebook post.

        Args:
            post_url (str): The URL of the Facebook post.

        Returns:
            tuple: A tuple containing the post text, comments list, and source images.
        """
                
        # Navigate to post url 
        self.driver.get(post_url)
        source = self.driver.page_source
        # create beautiful soup instance
        soup = BeautifulSoup(source, 'html.parser')

        # find the post text 
        elt_text = soup.findAll('div', {'class': 'xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs x126k92a'})
        if len(elt_text) > 0  :
            post_text= elt_text[0].get_text()
            # find comments in a facebook post page
            print("Scrapping completed")

            comments = soup.findAll('div', {'class': 'x1lliihq xjkvuk6 x1iorvi4'})
            comments_list = []
            for comment in comments:
                comments_list.append(comment.get_text(strip=True))


            # find all the images in the post like requested
            images = soup.findAll("img")
            src_images = []
            for img in images:
                src_images.append(img['src'])

            return post_text, comments_list, src_images
        else :
            return None, None, None
    
    def save_post_information(
            self,
            post_text :str,
            comments_list :List[str],
            src_images :List[str]
    ):
        """
        Saves the scraped information of a post to a MongoDB collection.

        Args:
            post_text (str): The text content of the post.
            comments_list (list): A list of comments on the post.
            src_images (list): A list of image URLs in the post.
        """

        # Get our collection 
        collection = self.fb_col
        # Create the document contained scrapped informations 
        post_document = {
            "texte" : post_text,
            "comments_list" : comments_list,
            "images_list" : src_images
        }
        # Add the document to the DB 
        collection.insert_one(post_document)

    def save_postes_informations(
            self,
            posts_links: List[str]
    ):
        """
        Scrapes and saves information from multiple posts to a MongoDB collection.

        Args:
            posts_links (list): A list of post links to scrape and save.
        """
        for link in posts_links:
            # Scrap the post with the link "link"
            post_text, comments_list, src_images = self.scrap_informations_post(link)
            if post_text != None :
                # Save scrapped informations to our MongoDB
                self.save_post_information(post_text, comments_list, src_images)

    def get_DBCollection(
            self,
            mongoClient: str,      
    ):
        """
        Connects to a MongoDB database and retrieves the Facebook collection.

        Args:
            mongoClient (str): The connection string for the MongoDB client.
        """

        # Connect to MongoDB 
        client = MongoClient(mongoClient)
        db = client["kaisens"]
        fb_col = db["facebook"]
        # Get our posts collection 
        self.fb_col = fb_col