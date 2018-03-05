import sqlite3
from datetime import datetime
from pytz import timezone
import pytz
import configparser

class BotStorage:
    """Datahandler for discord.py and sqlite3."""
    def __init__(self):
        pass


    def connect(self, server_id):
        """Method for creating a connection to the database."""
        try:
            database = server_id + '.sqlitedb'
            conn = sqlite3.connect(database)
            return conn
        except Error as e:
            print(e)


    def create_db(self, server_id):
        '''Method for creating the database. Uses the self.connect method.'''
        conn = self.connect(server_id)
        conn.close()


    def create_table(self, server_id, table, *column):
        """Create table in the database."""
        conn = self.connect(server_id)
        cur = conn.cursor()
        columns = str()
        for col in column:
            if len(columns) < 1:
                columns = col
            else:
                columns += ', ' + col
        sqlstring = 'CREATE TABLE IF NOT EXISTS {}({})'.format(table, columns)

        cur.execute(sqlstring)
        conn.commit()
        conn.close()


    def create_tables(self, server_id, tables_config_file):
        '''Method for creating tables from file. Calls self.create_table method.'''
        with open(tables_config_file) as conf:
            for line in conf:
                line = line.strip()
                valuelist = line.split("'")
                self.create_table(server_id, *valuelist)


    def create_start_values(self, server_id, start_values_file):
        '''Method for creating start values in database.'''
        with open(start_values_file) as start:
            for line in start:
                line = line.strip()
                valuelist = line.split("'")
                if valuelist[0] == 'Settings':
                    self.add_item(server_id, valuelist[0], timezone = valuelist[1], timeformat = valuelist[2])
                elif valuelist[0] == 'Games':
                    self.add_game(server_id, valuelist[1], valuelist[2])
                elif valuelist[0] == 'Modes':
                    self.add_mode(server_id, valuelist[1], valuelist[2], valuelist[3])
                elif valuelist[0] == 'Leagues':
                    #game, name, short_name
                    self.add_league(server_id, valuelist[1], valuelist[2], valuelist[3])
                elif valuelist[0] == 'Default':
                    game_id = self.get_id_from_name(server_id, 'Games', valuelist[2])
                    if valuelist[1] == 'Mode':
                        # update_item(self, server_id, table, queryfield, queryvalue, **values):
                        # UPDATE Games SET mode_id = ? WHERE name = ?'
                        # Default'Mode'Battlefield 1'Domination
                        # 0       1    2             3
                        mode_id = self.get_mode_id(server_id, valuelist[3], game_id)
                        self.update_item(server_id, 'Games', 'default_mode', mode_id, name='OR_' + valuelist[2])
                    elif valuelist[1] == 'League':
                        league_id = self.get_league_id(server_id, valuelist[3], game_id)
                        self.update_item(server_id, 'Games', 'default_league', league_id, name='OR_' + valuelist[2])
                else:
                    print('Row not compatible.')


    def add_item(self, server_id, table, **values):
        '''Method for adding one or more items to table row.'''
        conn = self.connect(server_id)
        cur = conn.cursor()
        valueitems = list()
        valuekeys = str()
        placeholders = str()
        for key, item in values.items():
            if len(values) == 1:
                valueitems = (item, )
            else:
                valueitems.append(item)
            if len(valuekeys) < 1:
                valuekeys = str(key)
                placeholders = '?'
            else:
                valuekeys += ', ' + str(key)
                placeholders += ', ?'
        if type(valueitems) != tuple():
            valueitems = tuple(valueitems)
        sqlstring = 'INSERT OR IGNORE INTO {}({}) VALUES ({})'.format(table, valuekeys, placeholders)

        cur.execute(sqlstring, valueitems)
        conn.commit()
        conn.close()


    def update_item(self, server_id, table, queryfield, queryvalue, **values):
        '''Updating existing values'''
        conn = self.connect(server_id)
        cur = conn.cursor()
        updatestring = 'UPDATE {} '.format(table)
        setstring = 'SET {} = ? '.format(queryfield)
        wherestring = 'WHERE '
        tup = []

        for key, value in values.items():
            korg = value.split('_')


            #korg 0 = AND/OR


            if len(values) == 1:
                wherestring += key + ' = ?'
                tup = (queryvalue, korg[1])
            else:
                if len(tup) < 1:
                    wherestring += key + ' = ?'
                    tup = [queryvalue, korg[1]]

                else:
                    wherestring += ' ' + korg[0] + ' ' + key + ' = ?'

                    tup.append(korg[1])


        if type(tup) != tuple():
            tup = tuple(tup)

        sqlstring = updatestring + setstring + wherestring

        cur.execute(sqlstring, tup)
        conn.commit()
        conn.close()


    def get_items_from_col(self, server_id, table, query):
        '''Method for getting values from a specific column in a table.'''
        conn = self.connect(server_id)
        cur = conn.cursor()
        resultlist = list()
        sqlstring = 'SELECT {} FROM {}'.format(query, table)
        cur.execute(sqlstring)
        for item in cur.fetchall():
            resultlist.append(item)
        conn.close()
        return resultlist


    def get_items_cond(self, server_id, table, queryvalue, **values):
        '''Method for extracting information from the database with conditions. Conditions in values must be frased "rowname = and/or_rowvalue""'''
        conn = self.connect(server_id)
        cur = conn.cursor()
        selectstring = 'SELECT {} FROM {} '.format(queryvalue, table)
        wherestring = 'WHERE '
        condstring = str()
        condtup = list()
        resultlist = list()

        for key, value in values.items():
            korg = value.split('_')
            colname = key

            rowvalue = korg[1]

            if len(values) == 1:
                condstring += colname + ' = ?'
                condtup = (rowvalue, )
            else:
                if len(condstring) < 1:
                    condstring += colname + ' = ?'
                else:
                    condstring += ' ' + korg[0] + ' ' + colname + ' = ?'
                condtup.append(rowvalue)


        if type(condtup) != tuple():
            condtup = tuple(condtup)

        sqlstring = selectstring + wherestring + condstring

        cur.execute(sqlstring, condtup)
        for item in cur.fetchall():
            resultlist.append(item)
        conn.close()
        return resultlist


    def get_name_from_id(self, server_id, table, id):
        '''Method for getting the name of a database item using id.'''
        idstr = 'id_' + str(id)
        return self.get_items_cond(server_id, table, 'name', id=idstr)[0][0]


    def get_id_from_name(self, server_id, table, name):
        '''Method for getting the id of a database item using name or short_name.'''
        name = 'OR_' + str(name)
        return self.get_items_cond(server_id, table, 'id', name=name, short_name=name)[0][0]


    def get_default_mode(self, server_id, game_id):
        return self.get_items_cond(server_id, 'Games', 'default_mode', id = 'id_' + str(game_id))[0][0]


    def get_default_league(self, server_id, game_id):
        return self.get_items_cond(server_id, 'Games', 'default_league', id = 'id_' + str(game_id))[0][0]


    def add_user(self, server_id, name, discord_id):
        '''Method for adding a user. Method uses self.add_item.'''
        self.add_item(server_id, 'Users', name = name, discord_id = discord_id)


    def add_game(self, server_id, name, short_name):
        '''Method for adding a game. Method uses self.add_item.'''
        self.add_item(server_id, 'Games', name = name, short_name = short_name)


    def add_mode(self, server_id, game, name, short_name):
        '''Method for adding a mode. Method uses self.get_id_from_name to get game_id and self.add_item.'''
        game_id = self.get_id_from_name(server_id, 'Games', name = game)
        self.add_item(server_id, 'Modes', game_id = game_id, name = name, short_name = short_name)

    def get_mode_id(self, server_id, name, game_id):

        return self.get_items_cond(server_id, 'Modes', 'id', name = 'OR_' + name, short_name = 'OR_' + name, game_id = 'AND_' + str(game_id))[0][0]


    def add_league(self, server_id, game, name, short_name):
        '''Method for adding a league. Method uses self.get_id_from_name to get game_id and self.add_item.'''
        game_id = self.get_id_from_name(server_id, 'Games', name = game)
        self.add_item(server_id, 'Leagues', game_id = game_id, name = name, short_name = short_name)


    def get_gameshortleagues(self, server_id, game):
        game_id = str(self.get_id_from_name(server_id, 'Games', name = game))
        returnlist = self.get_items_cond(server_id, 'Leagues', 'short_name', game_id = 'OR_' + game_id)
        leagues = list()
        for item in returnlist:
            leagues.append(item[0])

        return leagues


    def get_gameleagues(self, server_id, game):
        game_id = str(self.get_id_from_name(server_id, 'Games', name = game))
        returnlist = self.get_items_cond(server_id, 'Leagues', 'name', game_id = 'OR_' + game_id)
        leagues = list()
        for item in returnlist:
            leagues.append(item[0])

        return leagues


    def get_gameshortmodes(self, server_id, game):
        game_id = str(self.get_id_from_name(server_id, 'Games', name = game))
        returnlist = self.get_items_cond(server_id, 'Modes', 'short_name', game_id = 'OR_' + game_id)
        modes = list()
        for item in returnlist:
            modes.append(item[0])

        return modes


    def get_gamemodes(self, server_id, game):
        game_id = str(self.get_id_from_name(server_id, 'Games', name = game))
        returnlist = self.get_items_cond(server_id, 'Modes', 'name', game_id = 'OR_' + game_id)
        modes = list()
        for item in returnlist:
            modes.append(item[0])

        return modes


    def get_league_id(self, server_id, name, game_id):

        return self.get_items_cond(server_id, 'Leagues', 'id', name = 'OR_' + name, short_name = 'OR_' + name, game_id = 'AND_' + str(game_id))[0][0]


    def add_event(self, server_id, name, game, date, time = None, mode = None, league = None):
        '''Method for adding a mode. Method uses self.get_id_from_name to get game_id, mode_id and league_id. Also uses self.add_item.'''
        game_id = self.get_id_from_name(server_id, table = 'Games', name = game)
        if mode is None:
            mode_id = self.get_default_mode(server_id, game_id)
        else:
            mode_id = self.get_mode_id(server_id, mode, game_id)
        if league is None:
            league_id = self.get_default_league(server_id, game_id)
        else:
            league_id = self.get_league_id(server_id, league, game_id)
        if time is None:
            time = '22:00'

        timestp = self.get_utctimestamp(server_id, date, time)
        self.add_item(server_id, 'Events', name = name, game_id = game_id, mode_id = mode_id, league_id = league_id, timestamp = timestp)


    def get_event(self, server_id, name_or_id = None):
        searchlist = list()
        resultlist = list()
        if name_or_id is None:
            searchlist = self.get_items_from_col(server_id, 'Events', '*')
            #if timestp is None:
            #    searchlist = self.get_items_from_col(server_id, 'Events', '*')
            #else:
            #    searchlist = self.get_items_cond(server_id, 'Events', '*', timestamp = '>_' + str(timestp))
        else:
            searchlist = self.get_items_cond(server_id, 'Events', '*', name = 'or_' + name_or_id, id = 'or_' + name_or_id)

        for item in searchlist:
            id = item[0]
            name = item[1]
            game = self.get_name_from_id(server_id, 'Games', item[2])
            mode = self.get_name_from_id(server_id, 'Modes', item[3])
            league = self.get_name_from_id(server_id, 'Leagues', item[4])
            timestp = item[5]
            resultlist.append([id, name, game, mode, league, timestp])

        return resultlist

    def delete_event(self, server_id, id):
        conn = self.connect(server_id)
        cur = conn.cursor()
        cur.execute('DELETE FROM Attending WHERE event_id = ?', (id, ))
        cur.execute('DELETE FROM Events WHERE id = ?', (id, ))
        conn.commit()
        conn.close()

    def update_time(self, server_id, id, date, time):
        timestp = self.get_utctimestamp(server_id, date, time)
        self.update_item(server_id, 'Events', 'timestamp', timestp, id='OR_' + id)

    def update_name(self, server_id, id, name):
        self.update_item(server_id, 'Events', 'name', name, id='OR_' + id)

    def update_league(self, server_id, id, league):
        league_id = self.get_id_from_name(server_id, 'Leagues', league)
        print(league_id)
        self.update_item(server_id, 'Events', 'league_id', league_id, id='OR_' + id)


    def get_status(self, server_id, event_id = None, user_id = None):
        searchlist = list()
        resultlist = list()
        if event_id and user_id is not None:
            searchlist = self.get_items_cond(server_id, 'Attending', '*', event_id = 'AND_' + event_id, user_id = 'AND_' + user_id)
        elif event_id is None:
            searchlist = self.get_items_cond(server_id, 'Attending', '*', user_id = 'AND_' + user_id)
        elif user_id is None:
            searchlist = self.get_items_cond(server_id, 'Attending', '*', event_id = 'AND_' + event_id)
        for item in searchlist:
            event_id = item[0]
            user_id = item[1]
            status = item[2]
            reminded = item[3]
            resultlist.append([event_id, user_id, status, reminded])
        return resultlist


    def update_status(self, server_id, status, event_id, user_id):
        if len(self.get_status(server_id, event_id, user_id)) == 0:
            self.add_item(server_id, 'Attending', status = status, event_id = event_id, user_id = user_id, reminded = 0)
            print('ping!')
        else:
            self.update_item(server_id, 'Attending', 'status', status, event_id = 'AND_' + event_id, user_id = 'AND_' + user_id)
            print('pong!')
        return self.get_status(server_id, event_id, user_id)


    def get_timezone(self, server_id):
        zone = timezone(self.get_items_from_col(server_id, 'Settings', 'timezone')[0][0])
        return zone


    def get_timeformat(self, server_id):
        fmt = self.get_items_from_col(server_id, 'Settings', 'timeformat')[0][0]
        return fmt


    def get_utctimestamp(self, server_id, date, time):
        ltz = self.get_timezone(server_id)
        fmt = self.get_timeformat(server_id)
        timestring = date + ' ' + time
        timestp = datetime.strptime(timestring, '%Y-%m-%d %H:%M')
        timestp = ltz.localize(timestp)
        utctimestp = datetime.fromtimestamp(timestp.timestamp(), pytz.utc)
        return utctimestp.timestamp()


    def get_localtime(self, server_id, timestp):
        ltz = self.get_timezone(server_id)
        fmt = self.get_timeformat(server_id)
        local_timstr = datetime.fromtimestamp(float(timestp), ltz)
        return local_timstr.strftime(fmt)


    def get_utctime(self, server_id, timestp):
        fmt = self.get_timeformat(server_id)
        utctime = datetime.utcfromtimestamp(float(timestp))
        return utctime.strftime(fmt)


    def get_now(self):
        return datetime.utcnow().timestamp()
