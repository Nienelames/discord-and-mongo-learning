import discord
from discord.ext import commands, tasks

import DB
import Mail
import Utils
import Attributes

import time
import traceback



intents = discord.Intents.all()
intents.members = True

client = commands.Bot(command_prefix = ".", intents = intents)

@client.event
async def on_ready():
    print("Bot online")

@client.command()
async def test(ctx):
    channel = client.get_channel(853350057465741343)
    await channel.send('Test')
    
@client.command(aliases = ['add', 'a'])
async def add_story(ctx, *, user_links):
    await ctx.send('Verifying links... :hourglass_flowing_sand:')
    db = None
    user_links = str(user_links).split(' ')
    
    try:
        db = DB.Mongo()
        if user_links[0].startswith('https://a'):
            attr = Attributes.AutoStory(user_links[0], main_story_type = 'Ao3')
            attr.story.subscribe()
        else:
            attr = Attributes.AutoStory(user_links[0], main_story_type = 'FFN')

        links = attr.get_links(user_links, db)
        await ctx.send('Adding story... :hourglass:')

        title = attr.get_title()
        authors = attr.get_authors()
        date_updated = attr.get_date_updated()
        chapters = attr.get_chapters()
        word_count = attr.get_word_count()
        series_title = attr.get_series_title()
        status = attr.get_status()
        maturity_rating = attr.get_maturity_rating()

        db.collection.insert_one({"title": title, "authors": authors, "links": links, "date_updated": date_updated, "chapters": chapters, "word_count": word_count, "series_title": series_title, "status": status, "maturity_rating": maturity_rating})
        await ctx.send('Story successfully added! :white_check_mark:')
    except DB.errors.ConnectionFailure:
        await ctx.send('Connection to Database failed :x:\nTry again later')
        return
    except DB.errors.PyMongoError:
        await ctx.send('An unknown Database error has occured :x:\nMessage has been relayed to the dev')
        
        err = traceback.format_exc()
        await send_err_to_dev(err)

        return
    except Exception as err:
        await ctx.send(err)
    finally:
        if db != None:
            db.cluster.close()

@client.command(aliases = ['del', 'remove', 'delete', 'd', 'r'])
async def remove_story(ctx, user_link):
    await ctx.send('Removing story :hourglass:')
    user_link = str(user_link)
    db = None

    try:
        db = DB.Mongo()

        removed_links = db.collection.find_one_and_delete({"links.link": user_link}, projection = {"links": True, "_id": False})

        if removed_links != None:
            for removed_link in removed_links:
                if removed_link["type"] == 'Ao3':
                    try:
                        attr = Attributes.AutoStory(removed_link)
                    except:
                        pass
            await ctx.send('Story successfully removed :whie_check_mark:')
            return

        await ctx.send('Story not found :x:')
    except DB.errors.ConnectionFailure:
        await ctx.send('Connection to Database failed :x:\nTry again later')
        return
    except DB.errors.PyMongoError:
        await ctx.send('An unknown Database error has occured :x:\nMessage has been relayed to the dev')
        
        err = traceback.format_exc()
        await send_err_to_dev(err)

        return
    except Exception as err:
        await ctx.send(err)
    finally:
        if db != None:
            db.cluster.close()

async def update_ao3():
    db = None
    update_channel = None

    try:
        update_channel = client.get_channel(853350057465741343)
    except:
        err = traceback.format_exc()
        send_err_to_dev(err)  

    while True:
        try:
            mailer = Mail.Mailer()
            db = DB.Mongo()

            story_links = mailer.get_updated_story_links()

            for story_link in story_links:
                try:
                    attr = Attributes.AutoStory(main_link = story_link, main_story_type = 'Ao3')
                except Utils.InvalidLinkError:
                    try:
                        dead_story = db.collection.find_one({"links": {"type": "Ao3", "link": story_link}}, {"title": 1, "authors": 1, "_id": 0})
                        await update_channel.send(f'Ao3 link has died on {dead_story["title"]} by {dead_story["authors"]} :\n{story_link}')
                    except:
                        err = traceback.format_exc()
                        send_err_to_dev(err) 
                except Attributes.AO3.utils.HTTPError:
                    time.sleep(60)
                    continue
                except Utils.UnknownExceptionError:
                    err = traceback.format_exc()
                    send_err_to_dev(err)
                    return
            
                title = attr.get_title()
                authors = attr.get_authors()
                chapters = attr.get_chapters()
                word_count = attr.get_word_count()
                series_title = attr.get_series_title()
                status = attr.get_status()
                maturity_rating = attr.get_maturity_rating()

                old_story = db.collection.find_one_and_update({"links": {"type": "Ao3", "link": story_link}}, {"$set": {"title": title, "authors": authors, "chapters": chapters, "word_count": word_count, "series_title": series_title, "status": status, "maturity_rating": maturity_rating}}, projection = {"word_count": True, "_id": False})

                new_words = word_count - old_story["word_count"]

                if new_words > 0:
                    try:
                        await update_channel.send('An update of {:,} words!\n{}'.format(new_words, story_link))
                    except:
                        err = traceback.format_exc()
                        send_err_to_dev(err)         
            
            break
        except Utils.MailNotFoundError:
            return
        except Utils.MailerExecutionError as err:
            send_err_to_dev(err)
            return
        except DB.errors.ConnectionFailure:
            time.sleep(30)
            continue
        except:
            err = traceback.format_exc()
            send_err_to_dev(err)
        finally:
            if db != None:
                db.cluster.close()
            
            mailer.close()
            

async def update_ffn():
    db = None
    update_channel = None

    try:
        update_channel = client.get_channel(853350057465741343)
    except:
        err = traceback.format_exc()
        send_err_to_dev(err)  

    while True:
        try:
            db = DB.Mongo()

            stories = db.collection.find({"status": 0}, {"links": 1, "date_updated": 1})

            for story in stories:
                attr = None

                try:
                    for link in story["links"]:
                        if link["type"] == "Ao3":
                            stories.next
                            continue

                        if link["type"] == "FFN":
                            story_link = link["link"]
                            
                    attr = Attributes.AutoStory(story_link, main_story_type = 'FFN')
                except Utils.InvalidLinkError:
                    try:
                        dead_story = db.collection.find_one({story["_id"]}, {"title": 1, "authors": 1, "_id": 0})
                        await update_channel.send(f'FNN link has died on {dead_story["title"]} by {dead_story["authors"]} :\n{story_link}')
                    except:
                        err = traceback.format_exc()
                        send_err_to_dev(err)  

                    stories.next
                    continue                 
                except Attributes.FFScraper.utils.CloudflareError:
                    return
                except Utils.UnknownExceptionError:
                    err = traceback.format_exc()
                    send_err_to_dev(err)
                    return

                date_updated = attr.get_date_updated()

                if date_updated != story["date_updated"]:
                    title = attr.get_title()
                    authors = attr.get_authors()
                    chapters = attr.get_chapters()
                    word_count = attr.get_word_count()
                    series_title = attr.get_series_title()
                    status = attr.get_status()
                    maturity_rating = attr.get_maturity_rating()

                    new_words = word_count - story["word_count"]

                    if new_words > 0:
                        try:
                            await update_channel.send('An update of {:,} words!\n{}'.format(new_words, story_link))
                        except:
                            pass

                    db.collection.update_one({"_id": story["_id"]}, {"$set": {"title": title, "authors": authors, "chapters": chapters, "word_count": word_count, "series_title": series_title, "status": status, "maturity_rating": maturity_rating}})      
                    time.sleep(60)     
            
            break
        except DB.errors.ConnectionFailure:
            time.sleep(30)
            continue
        except Exception:
            err = traceback.format_exc()
            await send_err_to_dev(err)

            return
        finally:
            if db != None:
                db.cluster.close()  

async def send_err_to_dev(err):
    try:
        dev = await client.fetch_user(453933820253569037)
    
        while len(err) != 0:
            await dev.send(err[:2000])
            err = err.replace(err[:2000], '') 
    except:
        pass

