import sqlite3
import configparser
import discord
import asyncio
import pyjokes
from discord.ext import commands
from botstorage import BotStorage

# Some values for setting up
configfile = 'config.ini'
config = configparser.ConfigParser()
config.read(configfile)

token = config['Discord']['token']
description = config['Bot']['description']
prefix = config['Bot']['prefix']

database_tables = 'database_tables.ini'
database_start_values = 'database_start_values.ini'
datahandler = BotStorage()

# Creating the bot
bot = commands.Bot(command_prefix=prefix, description=description)

def runbot():
    bot.loop.create_task(event_reminder())
    bot.run(token)

def show_event(ctx, name_or_id = None):
    '''Command for listing events.'''
    server_id = ctx.message.server.id
    resultlist = list()
    now = datahandler.get_now()
    for item in datahandler.get_event(server_id, name_or_id):
        print(item)
        if float(item[5]) > now:
            resultlist.append(item)
    if len(resultlist) == 0:
        message = "Sorry, I don't understand you."
    elif type(resultlist) != list:
        message = resultlist
    elif len(resultlist) == 1:
        resultlist = resultlist[0]
        timestr = datahandler.get_localtime(server_id, resultlist[5])
        utctimestr = datahandler.get_utctime(server_id, resultlist[5])
        date = timestr.split(' ')[0]
        time = timestr.split(' ')[1]
        utcdate = utctimestr.split(' ')[0]
        utctime = utctimestr.split(' ')[1]
        message = '```\r\n_________________________________\r\nID: {} | Event: {} \r\nGame: {} \r\nMode: {} | League: {} \r\nDate: {} \r\nTime: {} | UTC-Time : {} \r\n_________________________________'
        message = message.format(resultlist[0], resultlist[1], resultlist[2], resultlist[3], resultlist[4], date, time, utctime)
        status = datahandler.get_status(server_id, str(resultlist[0]))
        attending = list()
        reserves = list()
        declined = list()
        for item in status:
            print(item)
            if item[2] == 0:
                attending.append(item)
            elif item[2] == 1:
                reserves.append(item)
            elif item[2] == 2:
                declined.append(item)
        if len(attending) > 0:
            message += '\r\nAttending:\r\n\r\n'
            for item in attending:
                print(item)
                print(item[1])
                namestr = datahandler.get_name_from_id(server_id, 'Users', item[1]) + '\r\n'
                print(namestr)
                message += namestr
        if len(reserves) > 0:
            message += '\r\nReserves:\r\n\r\n'
            for item in reserves:
                print(item)
                print(item[1])
                namestr = datahandler.get_name_from_id(server_id, 'Users', item[1]) + '\r\n'
                print(namestr)
                message += namestr
        if len(declined) > 0:
            message += '\r\nDeclined:\r\n\r\n'
            for item in declined:
                print(item)
                print(item[1])
                namestr = datahandler.get_name_from_id(server_id, 'Users', item[1]) + '\r\n'
                print(namestr)
                message += namestr

    else:
        message = '```\r\n_________________________________\r\n'
        resultlist.sort(key=lambda x: x[5])
        for result in resultlist:
            timestr = datahandler.get_localtime(server_id, result[5])
            date = timestr.split(' ')[0]
            time = timestr.split(' ')[1]
            row = 'ID: {} | {} {} \r\n\r\n{} | {} \r\n_________________________________\r\n'.format(result[0], date, time, result[1], result[2])
            message += row

    message += '\r\n```'
    return message


async def event_reminder():
    await bot.wait_until_ready()
    while not bot.is_closed:
        for server in bot.servers:
            server_id = server.id
            events = datahandler.get_event(server_id)
            eventlist = list()

            for event in events:
                event_time = float(event[5])
                now = datahandler.get_now()
                if now > (event_time - 3600.0) and event_time > now:
                    eventlist.append(event)
            for event in eventlist:
                event_id = str(event[0])
                status = datahandler.get_status(server_id, event_id)
                for item in status:
                    if item[3] < 1:
                        user_id = item[1]
                        if item[2] == 0:
                            discord_id = str(datahandler.get_items_cond(server_id, 'Users', 'discord_id', id = 'id_' + str(item[1]))[0][0])
                            print(discord_id)
                            print(type(discord_id))
                            for member in server.members:
                                print(member.name)
                                print(type(member.id))
                                if member.id == discord_id:
                                    message = "You are attending {} at {}. It's time to get ready!".format(event[1], datahandler.get_localtime(server_id, event[5]))
                                    print(message)
                                    await bot.send_message(member, message)
                        if item[2] == 1:
                            discord_id = str(datahandler.get_items_cond(server_id, 'Users', 'discord_id', id = 'id_' + str(item[1]))[0][0])
                            for member in server.members:
                                if member.id == discord_id:
                                    message = "You are reserve on {} at {}. Please check if you are needed!".format(event[1], datahandler.get_localtime(server_id, event[5]))
                                    await bot.send_message(member, message)
                        datahandler.update_item(server_id, 'Attending', 'reminded', 1, event_id = 'AND_' + str(event_id), user_id = 'AND_' + str(user_id))

        await asyncio.sleep(10)


@bot.event
async def on_ready():
    '''Function that decides what happens on bot start.'''
    print('Logged in!')
    print('Bot: ' + bot.user.name)
    print('Bot ID: ' + bot.user.id)
    print('------')
    print('Connected to: ')
    for server in bot.servers:
        print('              ' + server.name + ':' + server.id)
        message = pyjokes.get_joke()
        await bot.send_message(server, message)
    print('------')
    print('Invite bot:')
    print('https://discordapp.com/oauth2/authorize?client_id={}&scope=bot&permissions=0'.format(bot.user.id))
    print('------')


@bot.event
async def on_server_join(server):
    '''Function that decides what happens when bot joins a server.'''
    server_id = server.id
    server_name = server.name
    print('Joined server: ' + server_name)
    print('Server ID: ' + server_id)
    print('-------')
    datahandler.create_db(server_id)
    datahandler.create_tables(server_id, database_tables)
    datahandler.create_start_values(server_id, database_start_values)
    for member in server.members:
        datahandler.add_user(server_id, name = member.name, discord_id = member.id)
    print('Bot successfully set up.')
    await bot.send_message(server, "I'm ready!")


@bot.event
async def on_member_join(member):
    '''Function that decides what happens when a new member joins the server.'''
    server = member.server
    server_id = server.id
    fmt = 'Welcome {0.mention} to {1.name}!'
    await bot.send_message(server, fmt.format(member, server))
    pm = 'Welcome to {0.name}!'
    await bot.send_message(member, pm.format(server))
    datahandler.add_user(server_id, name = member.name, discord_id = member.id)


@bot.command(pass_context=True)
async def reg(ctx, user = None):
    '''Function for manually adding users.'''
    server = ctx.message.server
    server_id = server.id
    if user is None:
        member = ctx.message.author
        name = member.name
        discord_id = member.id
        datahandler.add_user(server_id, name = name, discord_id = discord_id)
        fmt = 'Welcome {0.mention} to {1.name}!'
        await bot.send_message(server, fmt.format(member, server))
        pm = 'Welcome to {0.name}!'
        await bot.send_message(member, pm.format(server))
    else:
        for member in ctx.message.server.members:
            if user == member.name:
                datahandler.add_user(server_id, name = member.name, discord_id = member.id)
                fmt = 'Welcome {0.mention} to {1.name}!'
                await bot.send_message(server, fmt.format(member, server))
                pm = 'Welcome to {0.name}!'
                await bot.send_message(member, pm.format(server))



@bot.command(pass_context=True)
async def event(ctx, name, game, date, time = None, mode = None, league = None):
    '''Command for adding events'''
    server_id = ctx.message.server.id
    datahandler.add_event(server_id, name, game, date, time, mode, league)
    message = 'You have added the event {} in {}.'.format(name, game)
    await bot.send_message(ctx.message.channel, message)


@bot.command(pass_context=True)
async def events(ctx, name_or_id = None):
    '''Command for listing events.'''
    channel = ctx.message.channel
    if name_or_id is None:
        name_or_id = [None]
    else:
        name_or_id = [name_or_id]
    for name_or_id in name_or_id:
        message = show_event(ctx, name_or_id)
        await bot.send_message(channel, message)


@bot.command(pass_context=True)
async def show(ctx, *name_or_id):
    '''Command for showing one or more events.'''
    channel = ctx.message.channel
    for name_or_id in name_or_id:
        message = show_event(ctx, name_or_id)
        await bot.send_message(channel, message)


@bot.command(pass_context=True)
async def join(ctx, *event_id):
    '''Command for joining events.'''
    server_id = ctx.message.server.id
    discord_id = ctx.message.author.id
    user_id = str(datahandler.get_items_cond(server_id, 'Users', 'id', discord_id = 'id_' + str(discord_id))[0][0])
    message = ''

    for event_id in event_id:

        datahandler.update_status(server_id, 0, event_id, user_id)

        event_data = datahandler.get_event(server_id, event_id)[0]
        message += 'You are now attending {} in {}, at {}.\r\n\r\n'.format(event_data[1], event_data[2], datahandler.get_localtime(server_id, event_data[5]))

    await bot.send_message(ctx.message.author, message)


@bot.command(pass_context=True)
async def reserve(ctx, *event_id):
    '''Command for signing up as reserve in events'''
    server_id = ctx.message.server.id
    discord_id = ctx.message.author.id
    user_id = str(datahandler.get_items_cond(server_id, 'Users', 'id', discord_id = 'id_' + str(discord_id))[0][0])
    message = ''

    for event_id in event_id:

        datahandler.update_status(server_id, 1, event_id, user_id)

        event_data = datahandler.get_event(server_id, event_id)[0]
        message += 'You are now reserve on {} in {}, at {}.\r\n\r\n'.format(event_data[1], event_data[2], datahandler.get_localtime(server_id, event_data[5]))

    await bot.send_message(ctx.message.author, message)


@bot.command(pass_context=True)
async def decline(ctx, *event_id):
    '''Command for declining events.'''
    server_id = ctx.message.server.id
    discord_id = ctx.message.author.id
    user_id = str(datahandler.get_items_cond(server_id, 'Users', 'id', discord_id = 'id_' + str(discord_id))[0][0])
    message = ''

    for event_id in event_id:

        datahandler.update_status(server_id, 2, event_id, user_id)

        event_data = datahandler.get_event(server_id, event_id)[0]
        message += 'You have now declined {} in {}, at {}.\r\n\r\n'.format(event_data[1], event_data[2], datahandler.get_localtime(server_id, event_data[5]))

    await bot.send_message(ctx.message.author, message)

@bot.command(pass_context=True)
async def delete(ctx, event_id):
    '''Command for deleting events'''
    server_id = ctx.message.server.id
    datahandler.delete_event(server_id, event_id)
    message = 'You deleted event number {}'.format(event_id)


    await bot.send_message(ctx.message.author, message)
'''
@bot.command(pass_context=True)
async def update(ctx, event_id, date, time):

    server_id = ctx.message.server.id
    returnlist = datahandler.update_time(server_id, event_id, date, time)

    message = 'You changed the event time and date.'
    await bot.send_message(ctx.message.author, message)
'''
@bot.command(pass_context=True)
async def update(ctx, event_id, *new_value):
    '''Command for updating event name, date and time.'''
    server_id = ctx.message.server.id
    event = datahandler.get_event(server_id, event_id)[0] # id, name, game, mode, league, timestp
    name = event[1]
    game = event[2]
    mode = event[3]
    league = event[4]
    timestp = event[5]
    timestr = datahandler.get_localtime(server_id, timestp).split(' ')
    date = timestr[0]
    time = timestr[1]

    leagues = datahandler.get_gameshortleagues(server_id, game)
    modes = datahandler.get_gameshortmodes(server_id, game)


    for value in new_value:
        if ':' in value:
            if value[2] == ':' and len(value) == 5:
                time = value
            else:
                continue
        elif '-' in value:
            if (value[4] and value[7] == '-') and len(value) == 10:
                date = value
            else:
                continue
        elif value in leagues:
            league = value
            datahandler.update_league(server_id, event_id, league)
        else:
            name = value
            datahandler.update_name(server_id, event_id, name)

            '''
            elif value in all_games:
                game = value
                game_id = datahandler.get_id_from_name(server_id, 'Games', game)
                all_modes = datahandler.get_gamemodes(server_id, game)
                all_leagues = datahandler.get_gameleagues(server_id, game)
                if mode not in all_modes:
                    mode = datahandler.get_name_from_id(datahandler.get_default_mode(server_id, game_id))
                if league not in all_leagues:
                    mode = datahandler.get_default_league(server_id, game_id)
            elif value in all_modes:
                mode = value
            elif value in all_leagues:
                league = value
            '''
    returnlist = datahandler.update_time(server_id, event_id, date, time)

    message = 'You updated the event.'
    await bot.send_message(ctx.message.author, message)

@bot.command(pass_context=True)
async def nightynight(ctx):
    '''Command for shutting down the bot.'''
    channel = ctx.message.channel
    message = "I'm feeling a bit sleepy."
    await bot.send_message(channel, message)
    quit()

@bot.command(pass_context=True)
async def ins(ctx):
    '''Insert values in database from update-file. Requires server access.'''
    server_id = ctx.message.server.id
    datahandler.create_start_values(server_id, 'database_update.ini')

@bot.command(pass_context=True)
async def leagues(ctx, game):
    '''Command for listing leagues'''
    server_id = ctx.message.server.id
    channel = ctx.message.channel
    leagues = datahandler.get_gameshortleagues(server_id, game)
    message = '```'
    for league in leagues:
        message += league + '\r\n'
    message += '```'

    await bot.send_message(channel, message)

@bot.command(pass_context=True)
async def modes(ctx, game):
    '''Command for listing modes'''
    server_id = ctx.message.server.id
    channel = ctx.message.channel
    modes = datahandler.get_gameshortmodes(server_id, game)
    message = '```'
    for mode in modes:
        message += mode + '\r\n'
    message += '```'

    await bot.send_message(channel, message)


runbot()
