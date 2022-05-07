from datetime import datetime
from AO3.works import Work
import requests
import Utils
import AO3
import FFScraper

class AutoStory:
    def __init__(self, main_link, main_story_type):
        self.main_story_type = main_story_type

        if main_story_type == 'Ao3':
            try:
                self.story = AO3.Work(AO3.utils.workid_from_url(main_link), session = AO3.Session('FiftySixw', '8f6GVjXc%%xCpK33'), load = False)
            except AO3.utils.InvalidIdError:
                raise Utils.InvalidLinkError('Invalid first link :x:')
            except AO3.utils.HTTPError as err:
                raise AO3.utils.HTTPError(str(err) + ' :x:')
            except Exception as err:
                raise Utils.UnknownExceptionError(str(err) + ' :x:')
        else:
            try:
                self.story = FFScraper.Story.Story(main_link)
            except FFScraper.utils.FFInvalidLink:
                raise Utils.InvalidLinkError('Invalid first link :x:')
            except FFScraper.utils.CloudflareError:
                raise FFScraper.utils.CloudflareError('FFN Cloudflare version 2 check has been detected :x:\nTry again in a *while*')
            except Exception as err:
                raise Utils.UnknownExceptionError(str(err) + ' :x:')



    def get_links(self, user_story_links, db):
        story_links = []
        ao3_added = False
        ffn_added = False
        wattpad_added = False
        tumblr_added = False
        deviantart_added = False

        #Adding the mian link to the list      
        if self.main_story_type == 'Ao3':
            ao3_link = 'https://archiveofourown.org/works/' + str(self.story.id)
            story_links.append({"type": self.main_story_type, "link": ao3_link})

            #Checking for duplicate on DB
            if db.collection.find_one({"links": {"type": "Ao3", "link": ao3_link}}, {}) != None:
                raise Utils.DuplicateLinkError("First link is already on the list :x:\n")

            ao3_added = True
        else:
            ffn_link = self.story.getLink()
            story_links.append({'type': self.main_story_type, "link": ffn_link})

            #Checking for duplicate on DB
            if db.collection.find_one({"links": {"type": "FFN", "link": ffn_link}}, {}) != None:
                raise Utils.DuplicateLinkError("First link is already on the list :x:\n")            
            
            ffn_added = True
        
        response = None
        #Removing the main link since it'a aded
        del user_story_links[0]

        #Adding alt links to the list
        for link in user_story_links:           
            #Identifying FFN link with API
            try:
                #Checking syntax duplicate
                if ffn_added:
                    raise Utils.DuplicateSiteError('Duplicate FFN link in syntax :x:\n' + link)

                link = FFScraper.Story.Story(link).getLink()
            
                #Checking for duplicates on DB
                if db.collection.find_one({"links": {"type": "FFN", "link": link}}, {}) != None:
                    raise Utils.DuplicateLinkError("This FFN link is already on the list :x:\n" + link)
                #Adding story
                else:
                    story_links.append({"type": "FFN", "link": ffn_link})
                    ffn_added = True
            except FFScraper.utils.CloudflareError:
                raise FFScraper.utils.CloudflareError('FFN Cloudflare version 2 check has been detected :x:\nTry again in a *while*')
            except:
                #Validating connection
                try:
                    response = requests.get(link, headers = {'User-Agent': 'Mozilla/5.0'})
                    
                    if response.status_code == 404:
                        raise Utils.InvalidLinkError('Story not found :x:\n' + link)
                except requests.ConnectionError:
                    raise Utils.InvalidLinkError('Connection failed to:\n' + link)
                finally:
                    if response != None:
                        response.close()  

                #Identifying Wattpad link
                if link.startswith('https://www.wattpad.com/'):
                    #Checking syntax duplicate
                    if wattpad_added:
                        raise Utils.DuplicateSiteError('Duplicate Wattpad link in syntax :x:\n' + link)
                    #Rejecting link if linked wrong by the user
                    elif 'story' not in link:
                        raise Utils.InvalidLinkError('Link the Wattpad story, not the chapter :x:')
                    #Checking for duplicates on DB
                    elif db.collection.find_one({"links": {"type": "Wattpad", "link": link}}, {}) != None:
                        raise Utils.DuplicateLinkError("This Wattpad link is already on the list :x:\n" + link)
                    #Adding story
                    else:
                        story_links.append({"type": "Wattpad", "link": link.replace(' ', '')})
                        wattpad_added = True
                #Identifying Tumblr link  
                elif 'https://' in link and 'tumblr.com' in link:
                    #Checking syntax duplicate
                    if tumblr_added:
                        raise Utils.DuplicateSiteError('Duplicate Tumblr link in syntax :x:\n' + link)
                    #Checking for duplicates on DB                    
                    elif db.collection.find_one({"links": {"type": "Tumblr", "link": link}}, {}) != None:
                        raise Utils.DuplicateLinkError("This Tumblr link is already on the list :x:\n" + link)
                    #Adding story
                    else:
                        story_links.append({"type": "Tumblr", "link": link.replace(' ', '')})
                        tumblr_added = True
                #Identifying DeviantArt link
                elif link.startswith('https://www.deviantart.com/'):
                    #Checking syntax duplicate
                    if deviantart_added:
                        raise Utils.DuplicateSiteError('Duplicate DeviantArt link in syntax :x:\n' + link)
                    #Checking for duplicates on DB
                    elif db.collection.find_one({"links": {"type": "Deviantart", "link": link}}, {}) != None:
                        raise Utils.DuplicateLinkError("This DeviantArt link is already on the list :x:\n" + link)
                    #Adding story
                    else:
                        story_links.append({"type": "Deviantart", "link": link.replace(' ', '')})
                        deviantart_added = True
                #Identifying AO3 link with API
                elif link.startswith('https://archiveofourown.org/'):
                    #Checking syntax duplicate
                    if ao3_added:
                        raise Utils.DuplicateSiteError('Duplicate Ao3 link in syntax :x:\n' + link)

                    if 'works' not in link:
                        raise Utils.InvalidLinkError('Ao3 link must have "works" in it\'s syntax :x:')

                    link = "https://archiveofourown.org/works/" + (str(AO3.utils.workid_from_url(link)))
                    #Checking for duplicates on DB
                    if db.collection.find_one({"links": {"type": "Ao3", "link": link}}, {}) != None:
                        raise Utils.DuplicateLinkError("This Ao3 link is already on the list :x:\n" + link)
                    #Adding story
                    else:
                        story_links.append({"type": "Ao3", "link": link})
                        ao3_added = True
                elif ffn_added:
                    raise Utils.InvalidLinkError('Invalid alt link :x:\n' + link + '\nMake sure it is not a redirect!\nSupported sites: Ao3, FFN, Wattpad, Tumblr, DeviantArt')

        return story_links

    def get_title(self):
        if self.main_story_type == 'Ao3':
            return self.story.title
        
        return self.story.title()

    def get_authors(self):
        author_list = []
        authors_str = ''

        if self.main_story_type == 'Ao3':
            author_list = self.story.authors

            for author in author_list:
                authors_str += author.username + ', '

            authors_str = authors_str.rstrip(authors_str[-1])
            authors_str = authors_str.rstrip(authors_str[-1])

            return authors_str
        
        author_link = self.story.authors()

        return author_link.split('/')[-1] 

    def get_date_updated(self):
        if self.main_story_type == 'Ao3':
            return self.story.date_updated
        
        date_updated_str = self.story.lastUpdated().strftime('%y-%m-%d') + ' 00:00:00'
        date_updated = datetime.strptime(date_updated_str,  '%y-%m-%d %H:%M:%S')
        return date_updated

    def get_chapters(self):
        if self.main_story_type == 'Ao3':
            chapters = self.story.nchapters
            expected_chapters = self.story.expected_chapters

            if expected_chapters == 1:
                return 'One-shot' 
            elif expected_chapters == None:
                return str(chapters) + '/?'
            else:
                return str(chapters) + '/' + str(expected_chapters)
        
        chapters = self.story.chapters()
        
        if chapters == 1:
            return 'One-shot'
        elif self.story.status() == 'Complete':
            return str(chapters) + '/' + str(chapters)
        else:
            return str(chapters) + '/?'

    def get_word_count(self):
        if self.main_story_type == 'Ao3':
            return self.story.words
        
        return self.story.words()

    def get_series_title(self):
        if self.main_story_type == 'Ao3' and self.story.series != []:
            return self.story.series[0].name
        
        return ''

    def get_status(self):
        if self.main_story_type == 'Ao3':
            if self.story.complete:
                return 1
            
            return 0 
        
        if self.story.status() == 'Complete':
            return 1
        
        return 0

    def get_maturity_rating(self):
        if self.main_story_type == 'Ao3':
            return self.story.rating
        
        return self.story.rating()
    
    


            
        


        







